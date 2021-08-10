import os
import bpy
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import BoolProperty, IntProperty, StringProperty, EnumProperty, FloatVectorProperty
from mathutils import Vector
from bpy_extras.io_utils import ExportHelper
from .wad import write
from .import_wad import ImportWAD, ImportWADContext
from .wad import write_obj
from .bake import bake

from .create_materials import generateNodesSetup


def item_cb(self, context):
    """Populates popup search box"""
    movable_names, static_names = ImportWADContext.mov_names['TR4'], ImportWADContext.static_names['TR4']

    if ImportWAD.SlotType == 'movable':
        return [(o, '{} - {}'.format(o, v), "") for o,v in movable_names.items()]
    else:
        return [(o, '{} - {}'.format(o, v), "") for o,v in static_names.items()]


class PopUpSearch2(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "wadblender.popup_search2"
    bl_label = "Select Slot"
    bl_property = "objs_enum"

    objs_enum: bpy.props.EnumProperty(items=item_cb)

    def execute(self, context):
        context.scene.SelectedObject = self.objs_enum
        context.area.tag_redraw()
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.invoke_search_popup(self)
        return {'FINISHED'}



class WadBlenderAddShineVertexLayer(bpy.types.Operator):
    bl_idname = "wadblender.shine_load"
    bl_label = "Add Shine Layer"
    bl_description = "Add Shine Layer to current object. It is used to make movable objects textures glossy"

    def execute(self, context):
        if context.active_object.type != 'MESH':
            return {'FINISHED'}

        vcolor_layer = context.active_object.data.vertex_colors.new(name='shine')
        v = 0
        for poly in context.active_object.data.polygons:
            for idx in poly.loop_indices:
                vcolor_layer.data[v].color = (0, 0, 0, 1)
                v += 1

        return {'FINISHED'}

class WadBlenderAddOpacityVertexLayer(bpy.types.Operator):
    bl_idname = "wadblender.opacity_load"
    bl_label = "Add Opacity Layer"
    bl_description = "Add Opacity Layer to current object. It is used to make movable objects textures translucent"

    def execute(self, context):
        if context.active_object.type != 'MESH':
            return {'FINISHED'}

        vcolor_layer = context.active_object.data.vertex_colors.new(name='opacity')
        v = 0
        for poly in context.active_object.data.polygons:
            for idx in poly.loop_indices:
                vcolor_layer.data[v].color = (0, 0, 0, 1)
                v += 1

        return {'FINISHED'}


class WadBlenderAddShadeVertexLayer(bpy.types.Operator):
    bl_idname = "wadblender.shade_load"
    bl_label = "Add Shade Layer"
    bl_description = "Add Shade Layer to current object. It is used to apply lighting to static objects"

    def execute(self, context):
        if context.active_object.type != 'MESH':
            return {'FINISHED'}

        v = 0
        vcolor_layer = context.active_object.data.vertex_colors.new(name='shade')
        for poly in context.active_object.data.polygons:
            for idx in poly.loop_indices:
                vcolor_layer.data[v].color = (0.5, 0.5, 0.5, 1)
                v += 1
        return {'FINISHED'}


class WadBlenderAddMaterial(bpy.types.Operator, ExportHelper):
    bl_idname = "wadblender.add_material"
    bl_label = "Create Blank Texture Page"
    bl_description = "Create blank texture and assign it the current object"

    filename_ext = ".png"

    filter_glob: StringProperty(
        default="*.png",
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self, context):
        pixels = []
        for _y in range(256):
            row = []
            for _x in range(256):
                red = green = blue = 0.
                alpha = 1.0
                row += [red, green, blue, alpha]

            pixels.append(row)

        img_pixels = []
        for row in pixels:
            for val in row:
                img_pixels.append(val)

        name = bpy.path.basename(self.filepath)[:-4]
        image = bpy.data.images.new(name, width=256, height=256)
        image.pixels = img_pixels
        image.filepath_raw = self.filepath
        image.file_format = 'PNG'
        image.save()
        
        set_idx = len(context.object.material_slots)
        mat = generateNodesSetup(name + 'Material', self.filepath)
        context.active_object.data.materials.append(mat)
        context.active_object.active_material_index = set_idx
        return {'FINISHED'}


class WadBlenderAddExistingMaterial(bpy.types.Operator, ImportHelper):
    bl_idname = "wadblender.add_existing_material"
    bl_label = "Add Texture Image"
    bl_description = "Add texture image to current object"

    filename_ext = ".png;.bmp;jpg"

    filter_glob: StringProperty(
        default="*.png;*.bmp;*.jpg",
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self, context):
        name = bpy.path.basename(self.filepath)[:-4]
        set_idx = len(context.active_object.material_slots)
        mat = generateNodesSetup(name + 'Material', self.filepath)
        context.active_object.data.materials.append(mat)
        context.active_object.active_material_index = set_idx
        return {'FINISHED'}


class WadBlenderSaveAsStatic(bpy.types.Operator, ExportHelper):
    bl_idname = "wadblender.save_static"
    bl_label = "Save as Static"
    bl_description = "Save the selected object in a static slot"

    filename_ext = ".wad"

    filter_glob: StringProperty(
        default="*.wad",
        options={'HIDDEN'},
        maxlen=255,
    )

    scale_setting: IntProperty(
        name="Scale",
        description="Dividing by 512, one TRLE click becomes 0.5 meters",
        default=512,
        min=1,
        max=100000
    )

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text='WAD Blender', icon="BLENDER")
        obj = context.active_object

        ImportWAD.SlotType = 'static'
        box = layout.box()
        row = box.row()
        row.operator("wadblender.popup_search2")
        row.label(text=ImportWADContext.static_names['TR4'][str(context.scene.SelectedObject)])
        row = box.row()
        row.prop(self, "scale_setting")

    def execute(self, context):
        name = ImportWADContext.static_names['TR4'][context.scene.SelectedObject]
        exit_code, log = write.writeWAD(context.object, int(context.scene.SelectedObject), self.filepath, name, True, self.scale_setting)
        ImportWADContext.log = log
        return exit_code


class WadBlenderSaveAsMovable(bpy.types.Operator, ExportHelper):
    bl_idname = "wadblender.save_movable"
    bl_label = "Save as Movable"
    bl_description = "Save the selected object in a movable slot"

    filename_ext = ".wad"

    filter_glob: StringProperty(
        default="*.wad",
        options={'HIDDEN'},
        maxlen=255,
    )


    scale_setting: IntProperty(
        name="Scale",
        description="Dividing by 512, one TRLE click becomes 0.5 meters",
        default=512,
        min=1,
        max=100000
    )

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text='WAD Blender', icon="BLENDER")
        obj = context.active_object
        ImportWAD.SlotType = 'movable'
        box = layout.box()
        row = box.row()
        row.operator("wadblender.popup_search2")
        row.label(text=ImportWADContext.mov_names['TR4'][str(context.scene.SelectedObject)])
        row = box.row()
        row.prop(self, "scale_setting")


    def execute(self, context):
        ImportWADContext.log.clear()
        name = ImportWADContext.mov_names['TR4'][context.scene.SelectedObject]
        exit_code, log = write.writeWAD(context.object, int(context.scene.SelectedObject), self.filepath, name, False, self.scale_setting)
        ImportWADContext.log = log
        return exit_code


class WadBlenderSaveAsObj(bpy.types.Operator, ExportHelper):
    bl_idname = "wadblender.save_obj"
    bl_label = "Save as Obj"
    bl_description = "Export option for making Shine and Opacity attributes compatible with Tomb Editor"

    filename_ext = ".obj"

    filter_glob: StringProperty(
        default="*.obj",
        options={'HIDDEN'},
        maxlen=255,
    )

    scale_setting: IntProperty(
        name="Scale",
        description="Dividing by 512, one TRLE click becomes 0.5 meters",
        default=512,
        min=1,
        max=100000
    )

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text='WAD Blender', icon="BLENDER")
        obj = context.active_object
        row = layout.row()
        row.prop(self, "scale_setting")

    def execute(self, context):
        exit_code, log = write_obj.write_obj(context.object, self.filepath, context, self.scale_setting)
        ImportWADContext.log = log
        return exit_code



class WadBlenderBake(bpy.types.Operator):
    bl_idname = "wadblender.bake"
    bl_label = "Bake into lightmap"
    bl_description = "lightmap packing of object textures"


    def execute(self, context):
        bake(context.object)
        return {'FINISHED'}




class WadBlenderClearLog(bpy.types.Operator):
    bl_idname = "wadblender.clear_log"
    bl_label = "Clear log"
    bl_description = ""

    def execute(self, context):
        ImportWADContext.log.clear()
        return {'FINISHED'}


class ObjectPanel(bpy.types.Panel):
    bl_label = "Wad Blender"
    bl_idname = "WADBLENDER_PT_ObjectPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Wad Blender'
    

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        try:
            me = context.active_object.data
            return ob and ob.type == 'MESH' and ob.mode == 'OBJECT'
        except (AttributeError, KeyError, TypeError):
            return False

    def draw(self, context):
        layout = self.layout
        selection = bpy.context.selected_objects



        if len(selection) < 1:
            layout.label(text="Select an object", icon = 'INFO')
            return
        elif len(selection) > 1:
            layout.label(text="Select a single mesh", icon = 'INFO')
            return

        obj = selection[0]

        row = layout.row(align=True)
        row.operator('wadblender.add_material', icon='FILE_NEW')

        row = layout.row(align=True)
        row.operator('wadblender.add_existing_material', icon='FILE_IMAGE')

        shade_missing = 'shade' not in context.active_object.data.vertex_colors
        shine_missing = 'shine' not in context.active_object.data.vertex_colors
        opacity_missing = 'opacity' not in context.active_object.data.vertex_colors


        if shade_missing or shine_missing or opacity_missing:
            box = layout.box()
            box.label(text='Create layer:')
            col = box.column(align=True)
            if shade_missing:
                col.operator('wadblender.shade_load', text='Shade', icon='LIGHT')

            if shine_missing:
                col.operator('wadblender.shine_load', text='Shine', icon='MOD_SMOOTH')

            if opacity_missing:
                col.operator('wadblender.opacity_load', text='Opacity', icon='MOD_OPACITY')


        box = layout.box()
        row = box.row(align=True)
        row.label(text='Save as:')
        row = box.row(align=True)
        row.operator('wadblender.save_static', text='Static')
        row.operator('wadblender.save_movable', text='Movable')
        row.operator('wadblender.save_obj', text='Obj')
        row = box.row(align=True)
        row.operator('wadblender.bake', text='Bake Lightmap')


class LogPanel(bpy.types.Panel):
    bl_label = "Log"
    bl_idname = "WADBLENDER_PT_LogPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Wad Blender'
    

    @classmethod
    def poll(cls, context):
        return len(ImportWADContext.log) > 0

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        for line in ImportWADContext.log:
            if line.startswith('W'):
                col = layout.column()
                col.alert = True
                col.label(text=line[1:])
                col.alert = False
            else:
                col.label(text=line)

        col.operator('wadblender.clear_log')



def returnCubeMesh(passed_name, vertices):
    v = []
    e = []

    for vertex in vertices:
        v.append(Vector(vertex))     
                  
    # Default cube face order.
    faces = [[4,5,1,0],
             [5,6,2,1],
             [6,7,3,2],
             [7,4,0,3],
             [0,1,2,3],
             [7,6,5,4],
            ]
            
    me = bpy.data.meshes.new(passed_name)
    me.from_pydata(v, e, faces)
    me.validate(verbose = True)  # useful for development when the mesh may be invalid.
    return me

def register():
    bpy.utils.register_class(ObjectPanel)
    bpy.utils.register_class(WadBlenderAddShineVertexLayer)
    bpy.utils.register_class(WadBlenderAddOpacityVertexLayer)
    bpy.utils.register_class(WadBlenderAddShadeVertexLayer)
    bpy.utils.register_class(WadBlenderAddMaterial)
    bpy.utils.register_class(WadBlenderAddExistingMaterial)
    bpy.utils.register_class(WadBlenderSaveAsStatic)
    bpy.utils.register_class(WadBlenderSaveAsMovable)
    bpy.utils.register_class(WadBlenderSaveAsObj)
    bpy.utils.register_class(PopUpSearch2)
    bpy.utils.register_class(WadBlenderClearLog)
    bpy.utils.register_class(LogPanel)
    bpy.utils.register_class(WadBlenderBake)

    bpy.types.Scene.SelectedObject = StringProperty(default='0')

    bpy.types.Scene.SlotType = StringProperty()


def unregister():
    bpy.utils.unregister_class(ObjectPanel)
    bpy.utils.unregister_class(WadBlenderAddShineVertexLayer)
    bpy.utils.unregister_class(WadBlenderAddOpacityVertexLayer)
    bpy.utils.unregister_class(WadBlenderAddShadeVertexLayer)
    bpy.utils.unregister_class(WadBlenderAddMaterial)
    bpy.utils.unregister_class(WadBlenderAddExistingMaterial)
    bpy.utils.unregister_class(WadBlenderSaveAsStatic)
    bpy.utils.unregister_class(WadBlenderSaveAsMovable)
    bpy.utils.unregister_class(WadBlenderSaveAsObj)
    bpy.utils.unregister_class(PopUpSearch2)
    bpy.utils.unregister_class(WadBlenderClearLog)
    bpy.utils.unregister_class(LogPanel)
    bpy.utils.unregister_class(WadBlenderBake)


if __name__ == "__main__":
    register()
