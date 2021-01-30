'''
Copyright (C) 2021 Bergus
YOUR@MAIL.com

Created by Bergus

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
from . import movables
from . import statics
from . import developer_utils
from . import shinepanel
from . import export_anim
from . import import_mixamo
from .common import createMaterials
from .preview import preview
import importlib
import os
import bpy
from bpy.types import PropertyGroup
from . import objects as object_names

bl_info = {
    "name": "WAD Blender",
    "description": "Import Tomb Raider 4 Objects and animations into Blender",
    "author": "Bergus",
    "version": (0, 0, 3),
    "blender": (2, 90, 1),
    "location": "import.wad",
    "warning": "This addon is still in development.",
    "wiki_url": "",
    "category": "Import-Export"}



# class MyToolPropertyGroup(PropertyGroup):
#     testint: bpy.props.EnumProperty(
#         name="objects",
#         description=""
#         )

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
importlib.reload(import_mixamo)
modules = developer_utils.setup_addon_modules(__path__, __name__, "bpy" in locals())

objects = []
obj_sel = ["None"]
update = [False]
files = {}

class Options:
    filepath: str
    wadname: str
    path: str
    scale: int
    import_anims: bool
    discard_junk: bool
    export_fbx: bool
    export_json: bool
    create_nla: bool
    export_obj: bool
    rotate: bool
    single_object: bool
    object: str



def import_wad(context, type, options):
    with open(options.filepath, "rb") as f:
        wad = read.readWAD(f)
    uvmap = bpy.data.images.new('textures', wad.mapwidth, wad.mapheight, alpha=True)
    uvmap.pixels = wad.textureMap
    texture_path = options.path + options.wadname + ".png"
    bpy.data.images["textures"].save_render(texture_path)
    materials = createMaterials(options.wadname, texture_path)

    if not options.single_object:
        if type == 'OPT_A' or type == 'OPT_D':
            lara.main(materials, wad, options)

        if type == 'OPT_B' or type == 'OPT_D':
            movables.main(materials, wad, options)

        if type == 'OPT_C' or type == 'OPT_D':
            statics.main(materials, wad, options)

        return set()

    else:
        if options.object in object_names.movable_names:
            movables.main(materials, wad, options)
        else:
            statics.main(materials, wad, options)

        return set()
        


class ImportWAD(Operator, ImportHelper):
    """Load a Tomb Raider 4 WAD file"""
    bl_idname = "import_test.some_data"
    bl_label = "Import WAD"

    filename_ext = ".wad"

    filter_glob: StringProperty(
        default="*.wad;*.WAD",
        options={'HIDDEN'},
        maxlen=255,
    )

    object: StringProperty(
        default="",
        options={'HIDDEN'},
        maxlen=255,
    )

    single_object: BoolProperty(
        name="",
        description="",
        default=False,
    )

    type: EnumProperty(
        name="Import",
        description="",
        items=(
            ('OPT_A', "Lara Full Model", "Import all Lara objects"),
            ('OPT_B', "All Movables", "Import all Movable objects"),
            ('OPT_C', "All Statics", "Import all Static objects"),
            ('OPT_D', "Everything", "Import everything"),
        ),
        default='OPT_D',
    )

    onames: EnumProperty(
        name="Game slot names",
        description="",
        items=(
            ('OPT_1', "TR1", ""),
            ('OPT_2', "TR2", ""),
            ('OPT_3', "TR3", ""),
            ('OPT_4', "TR4", ""),
            ('OPT_5', "TR5", ""),
            ('OPT_6', "TR5Main", ""),
        ),
        default='OPT_4',
    )

    scale_setting: IntProperty(
        name="Scale",
        description="Dividing by 512, one TRLE click becomes 0.5 meters",
        default=512,
        min=1,
        max=100000
    )

    import_anims: BoolProperty(
        name="Import Animations",
        description="Import Lara and Movables Animations",
        default=True,
    )

    create_nla: BoolProperty(
        name="Generate NLA tracks",
        description="Generate NLA tracks to manipulate actions",
        default=True,
    )

    discard_junk: BoolProperty(
        name="Discard Placeholders",
        description="Do not load triggers, particle emitters, AI, etc",
        default=True,
    )

    rotate: BoolProperty(
        name="Rotate objects upright",
        description="Swap y/z axis",
        default=True,
    )

    export_fbx: BoolProperty(
        name="Objects and Animations (FBX)",
        description="Export objects and animations in FBX format",
        default=False,
    )

    export_obj: BoolProperty(
        name="Objects (OBJ)",
        description="Export objects and animations in OBJ format",
        default=False,
    )

    export_json: BoolProperty(
        name="Additional Data (JSON)",
        description="Export additional wad data in json format",
        default=False,
    )

    processing: BoolProperty(
        name="",
        description="",
        default=False,
    )
    

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text='WAD Blender', icon="BLENDER")

        self.object = obj_sel[0]


        if update[0]:
            self.single_object = True
            update[0] = False

        if not self.processing: 
            if self.properties.filepath not in files and os.path.exists(self.properties.filepath):
                self.processing = True
                is_wad = self.properties.filepath[-4:] in {'.wad', '.WAD'}
                if is_wad:
                    with open(self.properties.filepath, "rb") as f:
                        movables, statics = preview(f)
                        files[self.properties.filepath] = movables + statics
                        #print(files)
                        objects.clear()
                        objects.extend(files[self.properties.filepath])
                        #print(objects)
                else:
                    objects.clear()
                    obj_sel[0] = 'None'
            elif self.properties.filepath in files:
                objects.clear()
                objects.extend(files[self.properties.filepath])
                #obj_sel[0] = 'None'

            else:
                objects.clear()
                obj_sel[0] = 'None'

            self.processing = False



        box = layout.box()
        box.label(text="Settings", icon="SETTINGS")
        box.prop(self, "type")
        
        row = box.row(align=True)
        row.prop(self, "discard_junk")


        if obj_sel[0] == 'None':
            self.single_object = False

        row = box.label(text="or select file and")
        row = box.row()
        row.operator("object.simple_operator")
        row.prop(self, "single_object", text=self.object)


        #box = layout.box()
        #box.label(text="Settings", icon="SETTINGS")
        #row = box.split(factor=0.5, align=True)
        # row.label(text="Game slot names: ")
        # row.prop(self, "onames", text="")
        #row = layout.row(align=True)
        #row.prop(self, "rotate")


        row = box.row(align=True)
        row.prop(self, "import_anims")

        # row = box.row(align=True)
        # if not self.import_anims:
        #     self.create_nla = False
        #     row.enabled = False
        # row.prop(self, "create_nla")

        row = box.row()
        row.prop(self, "scale_setting")

        row = layout.box()
        row.label(text="Batch Export:", icon="EXPORT")

        # row = layout.row(align=True)
        row.prop(self, "export_fbx")

        #row = layout.row(align=True)
        row.prop(self, "export_obj")

        #row = layout.row(align=True)
        row.prop(self, "export_json")

    def execute(self, context):
        options = Options()
        options.filepath = self.filepath
        options.wadname = os.path.basename(self.filepath)[:-4]
        options.scale = int(self.scale_setting)
        options.import_anims = self.import_anims
        options.discard_junk = self.discard_junk
        options.export_json = self.export_json
        options.export_fbx = self.export_fbx
        options.export_obj = self.export_obj
        options.create_nla = self.create_nla
        options.rotate = self.rotate
        options.single_object = self.single_object
        options.object = obj_sel[0]

        options.path, _ = os.path.split(options.filepath)
        options.path += '\\'

        return import_wad(context, self.type, options)


def menu_func_import(self, context):
    self.layout.operator(ImportWAD.bl_idname, text="TRLE WAD file (.wad)")



def item_cb(self, context):
    #return [e.customString for e in bpy.context.scene.objectsList]
    # props = context.scene.MyPropertyGroup
    # return props.objects
    #return objects
    return [(o, o, "") for o in objects]


class SimpleOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.simple_operator"
    bl_label = "Choose Object"
    bl_property = "my_enum"

    my_enum: bpy.props.EnumProperty(items=item_cb)

    def execute(self, context):
        obj_sel[0] = self.my_enum
        update[0] = True
        context.area.tag_redraw()
        #self.report({'INFO'}, "Selected: %s" % self.my_enum)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.invoke_search_popup(self)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(SimpleOperator)
    bpy.utils.register_class(ImportWAD)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    export_anim.register()
    shinepanel.register()
    import_mixamo.register()


def unregister():
    bpy.utils.unregister_class(SimpleOperator)
    bpy.utils.unregister_class(ImportWAD)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    export_anim.unregister()
    shinepanel.unregister()
    import_mixamo.unregister()






if __name__ == "__main__":
    register()

    # test call
    bpy.ops.import_wad.objects('INVOKE_DEFAULT')