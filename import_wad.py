import os

import bpy
from collections import Counter
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty

from . import lara, movables, statics, objects, lara_rigless
from .wad import read, preview
from .create_materials import generateNodesSetup, createPageMaterial


def check_requirements():
    try:
        import numpy
        import PIL
        return True
    except ImportError as e:
        return False


def rename_dups(obj_names):
    """Add obj numeric idx to name when it appears multiple times in catalog"""
    names = Counter(obj_names.values())
    for name, cnt in names.items():
        if cnt > 1:
            for idx in obj_names:
                if obj_names[idx] == name:
                    obj_names[idx] += idx


class ImportWADContext:
    update_single_obj_chkbox = False
    selected_obj = 'None'

    last_selected_file = ''
    last_objects_list = []
    cur_selected_file = ''
    has_numpy = check_requirements()
    mov_names = {}
    static_names = {}
    anim_names = {}
    state_names = {}
    for game in ['TR1', 'TR2', 'TR3', 'TR4', 'TR5', 'TR5Main']:
        mov_names[game], static_names[game], \
        anim_names[game], state_names[game] = objects.get_names(game)
        rename_dups(mov_names[game])
        rename_dups(static_names[game])

    game = 'TR4'

    @classmethod
    def set_game(cls, game):
        if cls.game != game:
            cls.game = game
            cls.last_selected_file = ''
            cls.last_objects_list.clear()


class ImportWAD(Operator, ImportHelper):
    """Load a TRLE WAD file"""
    bl_idname = "wadblender.import_wad"
    bl_label = "Import WAD"

    filename_ext = ".wad"

    filter_glob: StringProperty(
        default="*.wad;*.WAD",
        options={'HIDDEN'},
        maxlen=255,
    )

    # if user has choosen a single object instad of batch import
    single_object: BoolProperty(default=False)

    batch_import: EnumProperty(
        name="Import",
        description="",
        items=(
            ('OPT_LARA', "Lara Full Model", "Import all Lara objects"),
            ('OPT_OUTFIT', "Lara's Outfit", "Import only LARA_SKIN and LARA_SKIN_JOINTS meshes"),
            ('OPT_MOVABLES', "All Movables", "Import all Movable objects"),
            ('OPT_STATICS', "All Statics", "Import all Static objects"),
            ('OPT_EVERYTHING', "Everything", "Import Everything"),
        ),
        default='OPT_EVERYTHING',
    )

    batch_import_nolara: EnumProperty(
        name="Import",
        description="",
        items=(
            ('OPT_MOVABLES', "All Movables", "Import all Movable objects"),
            ('OPT_STATICS', "All Statics", "Import all Static objects"),
            ('OPT_EVERYTHING', "Everything", "Import Everything"),
        ),
        default='OPT_EVERYTHING',
    )

    texture_type: EnumProperty(
        name="Import mode",
        description="",
        items=(
            ('OPT_OBJECT', "One texture per object",
             "Each object has its own material with its own textures only."),
            ('OPT_PAGES', "Texture Pages",
             "256x256 texture pages are shared across all objects"),
            ('OPT_FULL', "Full Texture Map",
             "The entire wad texture map is shared across all objects"),
        ),
        default='OPT_OBJECT',
    )

    texture_type_nolib: EnumProperty(
        name="Import mode",
        description="",
        items=(
            ('OPT_FULL', "Full Texture Map",
             "The entire wad texture map is shared across all objects"),
        ),
        default='OPT_FULL',
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

    discard_junk: BoolProperty(
        name="Discard Placeholders",
        description="Do not load triggers, particle emitters, AI, etc",
        default=True,
    )

    texture_pages: BoolProperty(
        name="Texture pages",
        description="Split texture map in 256x256 pages",
        default=False,
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

    flip_normals: BoolProperty(
        name="Flip Normals",
        description="TRLE and Blender normals point to opposite directions",
        default=True,
    )

    one_material_per_object: BoolProperty(
        name="One material per object",
        description="If checked, each object has its own texture map and other textures are discarded",
        default=False,
    )

    game: EnumProperty(
        name="Game slot names",
        description="",
        items=(
            ('TR1', "TR1", ""),
            ('TR2', "TR2", ""),
            ('TR3', "TR3", ""),
            ('TR4', "TR4", ""),
            ('TR5', "TR5", ""),
            ('TR5Main', "TR5Main", ""),
        ),
        default='TR4',
    )

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text='WAD Blender', icon="BLENDER")
        box = layout.box()
        box.label(text="Settings", icon="SETTINGS")

        row = box.row(align=True)
        if self.game in {'TR1', 'TR2', 'TR3'}:
            row.prop(self, "batch_import_nolara")
        else:
            row.prop(self, "batch_import")

        row = box.row(align=True)
        row.prop(self, "discard_junk")

        row = box.label(text="or select file and")
        row = box.row()
        ImportWADContext.cur_selected_file = self.filepath
        row.operator("wadblender.popup_search")
        if ImportWADContext.selected_obj == 'None':
            self.single_object = False
        elif ImportWADContext.update_single_obj_chkbox:
            self.single_object = True
            ImportWADContext.update_single_obj_chkbox = False

        row.prop(self, "single_object", text=ImportWADContext.selected_obj)

        row = box.label(text='Materials:')

        col = box.column()
        if ImportWADContext.has_numpy:
            col.prop(self, "texture_type", expand=True)
        else:
            col.prop(self, "texture_type_nolib", expand=True)

        if not ImportWADContext.has_numpy:
            row = layout.row()
            row.operator("wadblender.install_requirements", icon='COLORSET_05_VEC')

        row = box.row(align=True)
        row.prop(self, "import_anims")

        row = box.split(factor=0.5, align=True)
        row.label(text="Game Slot Names")
        row.prop(self, "game", text="")
        ImportWADContext.set_game(self.game)

        row = box.row()
        row.prop(self, "scale_setting")

        row = layout.box()
        row.label(text="Batch Export:", icon="EXPORT")
        row.prop(self, "export_fbx")
        row.prop(self, "export_obj")
        row.prop(self, "export_json")

        box = layout.box()
        box.label(text="Advanced", icon="SETTINGS")
        box.prop(self, "flip_normals")

    def execute(self, context):

        class ImportOptions:
            pass

        options = ImportOptions()
        options.filepath = self.filepath
        options.wadname = os.path.basename(self.filepath)[:-4]
        options.scale = int(self.scale_setting)
        options.import_anims = self.import_anims
        options.discard_junk = self.discard_junk
        options.export_json = self.export_json
        options.export_fbx = self.export_fbx
        options.export_obj = self.export_obj
        options.single_object = self.single_object
        options.object = ImportWADContext.selected_obj
        options.flip_normals = self.flip_normals
        options.path, _ = os.path.split(options.filepath)
        options.path += '\\'

        options.mov_names = ImportWADContext.mov_names[ImportWADContext.game]
        options.static_names = ImportWADContext.static_names[ImportWADContext.game]
        options.anim_names = ImportWADContext.anim_names[ImportWADContext.game]
        options.state_names = ImportWADContext.state_names[ImportWADContext.game]

        if ImportWADContext.has_numpy:
            options.one_material_per_object = self.texture_type == 'OPT_OBJECT'
            options.texture_pages = self.texture_type == 'OPT_PAGES'
        else:
            options.one_material_per_object = False
            options.texture_pages = False


        with open(options.filepath, "rb") as f:
            wad = read.readWAD(f, options)

        materials = []
        if options.texture_pages:
            w = h = 256
            if options.wadname + '_PAGE0' not in bpy.data.materials:
                # create materials
                for i, page in enumerate(wad.textureMaps):
                    name = options.wadname + '_PAGE{}'.format(i)
                    uvmap = bpy.data.images.new(name, w, h, alpha=True)
                    uvmap.pixels = page
                    texture_path = options.path + name + ".png"
                    bpy.data.images[name].save_render(texture_path)
                    material = createPageMaterial(texture_path, context)
                    materials.append(material)
            else:
                # load existing materials
                for i, page in enumerate(wad.textureMaps):
                    name = options.wadname + '_PAGE{}'.format(i)
                    material = bpy.data.materials[name]
                    materials.append(material)
        else:
            # generate full texture map image
            w, h = wad.mapwidth, wad.mapheight
            uvmap = bpy.data.images.new(options.wadname, w, h, alpha=True)
            uvmap.pixels = wad.textureMap
            texture_path = options.path + options.wadname + ".png"
            bpy.data.images[options.wadname].save_render(texture_path)
            # create one material only if full texture option is checked
            # otherwise materials are generated at the time of object creation
            if not options.one_material_per_object:
                materials = [generateNodesSetup(options.wadname, texture_path)]

        if options.single_object:
            # find selected object in movable or static list
            found = False
            for idx, name in options.mov_names.items():
                if options.object == name:
                    movables.main(context, materials, wad, options)
                    found = True
                    break
            else:
                if options.object.startswith('movable'):
                    movables.main(context, materials, wad, options)
                    found = True

            if not found:
                statics.main(context, materials, wad, options)
        else:
            # Batch import objects
            # Lara option is only available for games >= TR4
            t = self.batch_import_nolara if self.game in {
                'TR1', 'TR2', 'TR3'} else self.batch_import
            if t == 'OPT_LARA':
                lara.main(context, materials, wad, options)
            elif t == 'OPT_OUTFIT':
                lara_rigless.main(context, materials, wad, options)
            elif t == 'OPT_MOVABLES':
                movables.main(context, materials, wad, options)
            elif t == 'OPT_STATICS':
                statics.main(context, materials, wad, options)
            else:
                # Import everything
                if self.game not in {'TR1', 'TR2', 'TR3'}:
                    lara.main(context, materials, wad, options)
                    bpy.ops.object.select_all(action='DESELECT')

                movables.main(context, materials, wad, options)
                bpy.ops.object.select_all(action='DESELECT')
                statics.main(context, materials, wad, options)

            bpy.ops.object.select_all(action='DESELECT')

        ImportWADContext.last_selected_file = 'None'
        ImportWADContext.last_objects_list.clear()
        return {"FINISHED"}


# menu entry
def menu_func_import(self, context):
    self.layout.operator(ImportWAD.bl_idname, text="TRLE WAD file (.wad)")


def item_cb(self, context):
    """Populates popup search box"""
    filepath = ImportWADContext.cur_selected_file

    if filepath != ImportWADContext.last_selected_file:
        if os.path.exists(filepath):
            is_wad = filepath[-4:] in {'.wad', '.WAD'}
            if is_wad:
                with open(filepath, "rb") as f:
                    game = ImportWADContext.game
                    movables, statics = preview.preview(
                        f, ImportWADContext.mov_names[game],
                        ImportWADContext.static_names[game])

                    ImportWADContext.last_selected_file = filepath
                    ImportWADContext.last_objects_list.clear()
                    ImportWADContext.last_objects_list += movables + statics
            else:
                ImportWADContext.last_selected_file = filepath
                ImportWADContext.last_objects_list.clear()
                ImportWADContext.selected_obj = 'None'
        else:
            ImportWADContext.last_selected_file = filepath
            ImportWADContext.last_objects_list.clear()
            ImportWADContext.selected_obj = 'None'

    return [(o, o, "") for o in ImportWADContext.last_objects_list]


class PopUpSearch(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "wadblender.popup_search"
    bl_label = "Choose Object"
    bl_property = "objs_enum"

    objs_enum: bpy.props.EnumProperty(items=item_cb)

    def execute(self, context):
        ImportWADContext.update_single_obj_chkbox = True
        ImportWADContext.selected_obj = self.objs_enum
        context.area.tag_redraw()
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.invoke_search_popup(self)
        return {'FINISHED'}


class InstallRequirements(bpy.types.Operator):
    bl_idname = "wadblender.install_requirements"
    bl_label = "Install libraries"
    bl_description = "Install Numpy and PIL python libraries to enable additional texture mappings and Sprytile compatibility"

    def execute(self, context):
        import subprocess
        import sys

        # path to python.exe
        python_exe = os.path.join(sys.prefix, 'bin', 'python.exe')

        # upgrade pip
        subprocess.call([python_exe, "-m", "ensurepip"])
        subprocess.call(
            [python_exe, "-m", "pip", "install", "--upgrade", "pip"]
        )

        # install required packages
        subprocess.call([python_exe, "-m", "pip", "install", "numpy"])
        subprocess.call([python_exe, "-m", "pip", "install", "pillow"])
        ImportWADContext.has_numpy = check_requirements()

        return{'FINISHED'}


def register():
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.utils.register_class(ImportWAD)
    bpy.utils.register_class(PopUpSearch)
    bpy.utils.register_class(InstallRequirements)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.utils.unregister_class(ImportWAD)
    bpy.utils.unregister_class(PopUpSearch)
    bpy.utils.unregister_class(InstallRequirements)
