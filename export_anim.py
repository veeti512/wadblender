import bpy
from .anim import export_anim


def export(context, filepath, offset, rig_name):
    export_anim(filepath, offset, rig_name)
    return {'FINISHED'}


# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty
from bpy.types import Operator


class ExportSomeData(Operator, ExportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "export_anim.data"
    bl_label = "Export Wad Tool Animation"

    # ExportHelper mixin class uses this
    filename_ext = ".anim"

    filter_glob: StringProperty(
        default="*.anim",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    rig_name: StringProperty(
        default="LARA_RIG",
        description="RIG name of the active action to export",
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )


    offset: IntProperty(
        name="Offset",
        description="Rise Lara by amount",
        default=0
    )

    def execute(self, context):
        return export(context, self.filepath, self.offset, self.rig_name)


# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(ExportSomeData.bl_idname, text="Export Wad Tool Animation")


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
