import bpy
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import StringProperty

from .create_materials import generateNodesSetup

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
        obj = context.active_object

        if obj is None:
            layout.label(text="Nothing selected", icon = 'INFO')
            return

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


def register():
    bpy.utils.register_class(ObjectPanel)
    bpy.utils.register_class(WadBlenderAddShineVertexLayer)
    bpy.utils.register_class(WadBlenderAddOpacityVertexLayer)
    bpy.utils.register_class(WadBlenderAddShadeVertexLayer)
    bpy.utils.register_class(WadBlenderAddMaterial)
    bpy.utils.register_class(WadBlenderAddExistingMaterial)


def unregister():
    bpy.utils.unregister_class(ObjectPanel)
    bpy.utils.unregister_class(WadBlenderAddShineVertexLayer)
    bpy.utils.unregister_class(WadBlenderAddOpacityVertexLayer)
    bpy.utils.unregister_class(WadBlenderAddShadeVertexLayer)
    bpy.utils.unregister_class(WadBlenderAddMaterial)
    bpy.utils.unregister_class(WadBlenderAddExistingMaterial)


if __name__ == "__main__":
    register()
