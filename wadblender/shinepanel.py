import bpy
import bmesh


class ShinePanel(bpy.types.Panel):
    bl_label = "Wad Blender"
    bl_idname = "OBJECT_PT_hello"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Wad Blender'
    ebm = dict()

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_MESH':
            me = context.edit_object.data
            cls.ebm.setdefault(me.name, bmesh.from_edit_mesh(me))
            return True

        cls.ebm.clear()
        return False


    def draw(self, context):
        layout = self.layout
        obj = context.object
        me = context.edit_object.data

        bm = bmesh.from_edit_mesh(obj.data)
        selected = []
        for face in bm.faces:
            if face.select:
                selected.append(face)
        
        row = layout.row(align=True)
        row = row.split(factor=0.8, align=True)
        row.prop(me, "Shine")
        row.prop(me, "Opacity", text='T', text_ctxt='Translucent')

def set_shine(self, value):

    bm = ShinePanel.ebm.setdefault(self.name, bmesh.from_edit_mesh(self))

    selected = []
    for face in bm.faces:
        if face.select:
            selected.append(face)

    for af in selected:
        if value > 31:
            break
        if af and 0 <= af.material_index <= 31:
            af.material_index = value
        elif af and af.material_index >= 32:
            af.material_index = value + 32
        
    bmesh.update_edit_mesh(self)
            


def get_shine(self):        
    bm = ShinePanel.ebm.setdefault(self.name, bmesh.from_edit_mesh(self))

    af = bm.faces.active
    if af:
        return(af.material_index if af.material_index < 32 else af.material_index - 32)



def set_opacity(self, value):
    value = not value

    bm = ShinePanel.ebm.setdefault(self.name, bmesh.from_edit_mesh(self))

    selected = []
    for face in bm.faces:
        if face.select:
            selected.append(face)

    for af in selected:
        if af and af.material_index <= 31 and not value:
            af.material_index += 32
        elif af and af.material_index > 31 and value:
            af.material_index -= 32
        
        bmesh.update_edit_mesh(self)


def get_opacity(self):        
    bm = ShinePanel.ebm.setdefault(self.name, bmesh.from_edit_mesh(self))

    af = bm.faces.active
    if af:
        return not af.material_index < 32

def register():

    bpy.types.Mesh.Shine = bpy.props.IntProperty(get=get_shine, set=set_shine, min=0, max=31)
    bpy.types.Mesh.Opacity = bpy.props.BoolProperty(get=get_opacity, set=set_opacity, description='Translucent')
    bpy.utils.register_class(ShinePanel)


def unregister():
    bpy.utils.unregister_class(ShinePanel)


if __name__ == "__main__":
    register()
