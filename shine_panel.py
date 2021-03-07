import bpy
import bmesh

class ShinePanel(bpy.types.Panel):
    bl_label = "Shine Panel"
    bl_idname = "WADBLENDER_PT_ShinePanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'Wad Blender'

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        try:
            me = context.edit_object.data
            return ob and ob.type == 'MESH' and ob.mode == 'EDIT'
        except (AttributeError, KeyError, TypeError):
            return False

    def draw(self, context):
        layout = self.layout
        bm = bmesh.from_edit_mesh(context.active_object.data)
        if bm.select_mode != {'FACE'}:
            layout.label(text="Face select only", icon = 'INFO')
            return
        
        af = bm.faces.active
        if not af:
            layout.label(text="Nothing selected", icon = 'INFO')
        else:
            row = layout.row(align=True)
            row = row.split(factor=0.5, align=True)
            row.prop(context.scene, 'Shine', text="Shine")
            row.prop(context.scene, 'Opacity', text="Translucent")
            row = layout.row(align=True)
            row.operator("wadblender.apply_shine")


class ApplyVertCol(bpy.types.Operator):
    bl_idname = "wadblender.apply_shine"
    bl_label = "Assign"
    bl_description = "Assign shine and opacity to selected vertices for selected vertex color layer"

    def execute(self, context):
        me = context.active_object.data
        bm = bmesh.from_edit_mesh(me)
        face_selection = [face.index for face in bm.faces if face.select]

        bpy.ops.object.mode_set(mode='EDIT', toggle=True)
        if 'shine' not in me.vertex_colors:
            vcolor_layer = me.vertex_colors.new(name='shine')
            v = 0
            for poly in me.polygons:
                for idx in poly.loop_indices:
                    vcolor_layer.data[v].color = (0, 0, 0, 1)
                    v += 1

        if 'opacity' not in me.vertex_colors:
            vcolor_layer = me.vertex_colors.new(name='opacity')
            v = 0
            for poly in me.polygons:
                for idx in poly.loop_indices:
                    vcolor_layer.data[v].color = (0, 0, 0, 1)
                    v += 1

        for face in me.polygons:
            if face.index in face_selection:
                for loop_idx in face.loop_indices:
                        shine = context.scene.Shine
                        transl = 1 if context.scene.Opacity == 1 else 0
                        me.vertex_colors['shine'].data[loop_idx].color = (shine/31,) * 3 + (1,)
                        me.vertex_colors['opacity'].data[loop_idx].color = (transl,) * 3 + (1,)

        bpy.ops.object.mode_set(mode='EDIT', toggle=True)
        return{'FINISHED'}


def register():
    bpy.types.Scene.Shine = bpy.props.IntProperty(min=0, max=31)
    bpy.types.Scene.Opacity = bpy.props.BoolProperty(description='Translucent')
    bpy.utils.register_class(ShinePanel)
    bpy.utils.register_class(ApplyVertCol)


def unregister():
    bpy.utils.unregister_class(ShinePanel)
    bpy.utils.unregister_class(ApplyVertCol)
    