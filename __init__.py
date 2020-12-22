'''
Copyright (C) CURRENT_YEAR YOUR NAME
YOUR@MAIL.com

Created by YOUR NAME

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty
from bpy_extras.io_utils import ImportHelper
from . import model
from . import data
from . import read
from . import lara
from . import common
from . import objects
from . import movables
from . import statics
from . import developer_utils
import importlib
import os
import bpy
bl_info = {
    "name": "WAD Blender",
    "description": "Import Tomb Raider 4 Objects and animations into Blender",
    "author": "veeti512",
    "version": (0, 0, 1),
    "blender": (2, 90, 1),
    "location": "import.wad",
    "warning": "This addon is still in development.",
    "wiki_url": "",
    "category": "Import-Export"}


# load and reload submodules
##################################


importlib.reload(developer_utils)
importlib.reload(movables)
importlib.reload(statics)
importlib.reload(common)
importlib.reload(lara)
importlib.reload(read)
importlib.reload(data)
importlib.reload(model)
modules = developer_utils.setup_addon_modules(__path__, __name__, "bpy" in locals())


def import_wad(context, filepath, type, scale_setting, import_anims, discard_junk, export_fbx, export_json, create_nla):
    from importlib import reload

    with open(filepath, "rb") as f:
        wad = read.readWAD(f)

    path, wadfile = os.path.split(filepath)
    path += '\\'

    scale = int(scale_setting)

    if type == 'OPT_A' or type == 'OPT_D':
        lara.main(path, wadfile[:-4], wad, scale, import_anims, create_nla, export_fbx, export_json)

    if type == 'OPT_B' or type == 'OPT_D':
        movables.main(path, wadfile[:-4], wad, scale, import_anims,
                      export_fbx, export_json, discard_junk, create_nla)

    if type == 'OPT_C' or type == 'OPT_D':
        statics.main(path, wadfile[:-4], wad, scale, export_fbx)

    return set()


# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.


class ImportWAD(Operator, ImportHelper):
    """Load a Tomb Raider 4 WAD file"""
    bl_idname = "import_test.some_data"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import WAD"

    # ImportHelper mixin class uses this
    filename_ext = ".wad"

    filter_glob: StringProperty(
        default="*.wad;*.WAD",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.

    type: EnumProperty(
        name="Import",
        description="Choose between two items",
        items=(
            ('OPT_A', "Lara", "Import all Lara objects"),
            ('OPT_B', "Movables", "Import all Movable objects"),
            ('OPT_C', "Statics", "Import all Static objects"),
            ('OPT_D', "Everything", "Import everything"),
        ),
        default='OPT_A',
    )

    scale_setting: IntProperty(
        name="Scale",
        description="Dividing by 512, one TRLE click becomes 0.5 meters",
        default=512,
        min=1,
        max=2048
    )

    import_anims: BoolProperty(
        name="Import Animations",
        description="Import Lara and Movables Animations",
        default=True,
    )

    create_nla: BoolProperty(
        name="Generate NLA tracks",
        description="Generate NLA tracks to manipulate actions",
        default=False,
    )

    discard_junk: BoolProperty(
        name="Discard Placeholders",
        description="Do not load triggers, particle emitters, AI, etc",
        default=True,
    )

    export_fbx: BoolProperty(
        name="Export Objects and Animations (FBX)",
        description="Export objects and animations in FBX format",
        default=False,
    )

    export_json: BoolProperty(
        name="Export Additional Data (JSON)",
        description="Export additional wad data in json format",
        default=False,
    )

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text='WAD Blender')

        row = layout.row()
        row.prop(self, "type")

        row = layout.row()
        row.prop(self, "scale_setting")

        row = layout.row(align=True)
        row.prop(self, "import_anims")

        row = layout.row(align=True)
        row.prop(self, "create_nla")

        row = layout.row(align=True)
        row.prop(self, "discard_junk")

        row = layout.row(align=True)
        row.prop(self, "export_fbx")

        row = layout.row(align=True)
        row.prop(self, "export_json")

    def execute(self, context):
        return import_wad(context, self.filepath, self.type, self.scale_setting, self.import_anims, self.discard_junk, self.export_fbx, self.export_json, self.create_nla)


# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(ImportWAD.bl_idname,
                         text="Tomb Raider 4 WAD file (.wad)")


def register():
    bpy.utils.register_class(ImportWAD)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportWAD)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.import_wad.objects('INVOKE_DEFAULT')
