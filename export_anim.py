import bpy
from . import anim_mixamo
from .anim_mixamo import export_anim_mixamo
import importlib


def export(context, filepath, offset, action):
    importlib.reload(anim_mixamo)

    export_anim_mixamo(filepath, offset, action)
    return {'FINISHED'}


# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty
from bpy.types import Operator


class ExportSomeData(Operator, ExportHelper):
    bl_idname = "export_anim.data"
    bl_label = "Export Wad Tool Animation"

    # ExportHelper mixin class uses this
    filename_ext = ".anim"

    filter_glob: StringProperty(
        default="*.anim",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )


    offset: IntProperty(
        name="Rise Lara by",
        description="Rise Lara by amount in TRLE units (1m = 512)",
        default=0
    )


    def get_enum_items(self, context):

        actions = []
        for obj in bpy.data.objects:
            action_name = (obj.animation_data.action.name 
                           if obj.animation_data is not None and obj.animation_data.action is not None 
                           else "")
            if action_name and obj.type == "ARMATURE":
                actions.append((obj.name,action_name))

        return [(a[0], a[1], 'Instance group "%s"'%a[0]) for a in actions]

    group: EnumProperty(
    name = "Action", items = get_enum_items,
    description = "Animation to export.")


    def draw(self, context):
        obj = context.object
        layout = self.layout
        row = layout.row()
        row.label(text='WAD Blender', icon="BLENDER")

        box = layout.box()
        #row = box.row(align=True)
        box.prop(self, "group")
        
        #row = box.row()
        box.prop(self, "offset")




    def execute(self, context):
        return export(context, self.filepath, self.offset, self.group)


# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(ExportSomeData.bl_idname, text="TRLE Animation (.anim)")


def register():
    bpy.utils.register_class(ExportSomeData)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ExportSomeData)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.export_anim.data('INVOKE_DEFAULT')



