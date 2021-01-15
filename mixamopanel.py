import bpy


class ACTION_UL_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        ob = data
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon_value=icon)
        elif self.layout_type in {'GRID'}:
            pass


class UIListPanelExample(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "UIList Panel"
    bl_idname = "OBJECT_PT_ui_list_example"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        ob = context.object
        layout.template_list("ACTION_UL_list", "", bpy.data, "actions", ob, "action_list_index")


def register():
    bpy.types.Object.action_list_index = bpy.props.IntProperty()
    bpy.utils.register_class(__name__)


def unregister():
    bpy.utils.unregister_class(__name__)
    del bpy.types.Object.action_list_index

if __name__ == "__main__":
    register()