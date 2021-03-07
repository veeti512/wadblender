# this is mostly from sprytile source code.
# used to write metadata into bmeshes
import bpy


def check_install():
    try:
        _ = bpy.context.scene.sprytile_data
        return True
    except:
        return False

class UvDataLayers:
    GRID_INDEX = "grid_index"
    GRID_TILE_ID = "grid_tile_id"
    GRID_SEL_WIDTH = "grid_sel_width"
    GRID_SEL_HEIGHT = "grid_sel_height"
    GRID_SEL_ORIGIN = "grid_sel_origin"
    PAINT_SETTINGS = "paint_settings"
    WORK_LAYER = "work_layer"

    LAYER_NAMES = [GRID_INDEX, GRID_TILE_ID,
                   GRID_SEL_WIDTH, GRID_SEL_HEIGHT,
                   GRID_SEL_ORIGIN, PAINT_SETTINGS,
                   WORK_LAYER]


def get_work_layer_data(sprytile_data):
    """
    Returns the work layer bitmask from the given sprytile data
    """
    # Bits 0-4 are reserved for storing layer numbers
    # Bit 5 = Face is using decal mode
    # Bit 6 = Face is using UV mode

    # When face is using UV mode, there may be multiple
    # UV layers, to find which layers it is using,
    # Mask against bits 0-4

    # This is only for 1 layer decals, figure out multi layer later
    out_data = 0
    if sprytile_data.work_layer != 'BASE':
        out_data += (1 << 0)
        if sprytile_data.work_layer_mode == 'MESH_DECAL':
            out_data += (1 << 5)
        else:
            out_data += (1 << 6)
    return out_data


def get_paint_settings(sprytile_data, flipx, flipy, degree_rotation=0):
    '''
    Returns the paint settings bitmask from a sprytile_data instance
    :param sprytile_data: sprytile_data instance
    :return: A bitmask representing the paint settings in the sprytile_data
    '''
    # Rotation and UV flip are always included
    paint_settings = 0

    # Flip x/y are toggles
    paint_settings += (1 if flipx else 0) << 9
    paint_settings += (1 if flipy else 0) << 8

    # Rotation is encoded as 0-3 clockwise, bit shifted by 10
    #degree_rotation = round(math.degrees(sprytile_data.mesh_rotate), 0)
    if degree_rotation < 0:
        degree_rotation += 360
    rot_val = 0
    if degree_rotation <= 1:
        rot_val = 0
    elif degree_rotation <= 90:
        rot_val = 3
    elif degree_rotation <= 180:
        rot_val = 2
    elif degree_rotation <= 270:
        rot_val = 1
    paint_settings += rot_val << 10

    if not "paint_align" in sprytile_data.keys():
        sprytile_data["paint_align"] = 5

    paint_settings += sprytile_data["paint_align"]
    paint_settings += 1 << 7
    paint_settings += 1 << 6
    paint_settings += 1 << 5
    paint_settings += 1 << 4
    return paint_settings


def get_grid(context, grid_id):
    """
    Returns the sprytile_grid with the given id
    :param context: Blender tool context
    :param grid_id: grid id
    :return: sprytile_grid or None
    """
    mat_list = context.scene.sprytile_mats
    for mat_data in mat_list:
        for grid in mat_data.grids:
            if grid.id == grid_id:
                return grid
    return None


def write_metadata(context, obj, face_index, mesh, width, height, tile_x, tile_y, flipx, flipy, map_width=256):
    grid_layer_id = mesh.faces.layers.int.get(UvDataLayers.GRID_INDEX)
    grid_layer_tileid = mesh.faces.layers.int.get(UvDataLayers.GRID_TILE_ID)
    grid_sel_width = mesh.faces.layers.int.get(UvDataLayers.GRID_SEL_WIDTH)
    grid_sel_height = mesh.faces.layers.int.get(UvDataLayers.GRID_SEL_HEIGHT)
    grid_sel_origin = mesh.faces.layers.int.get(UvDataLayers.GRID_SEL_ORIGIN)
    paint_settings_id = mesh.faces.layers.int.get(UvDataLayers.PAINT_SETTINGS)
    work_layer_id = mesh.faces.layers.int.get(UvDataLayers.WORK_LAYER)

    face = mesh.faces[face_index]
    tile_id = (tile_y * map_width) + tile_x

    data = context.scene.sprytile_data
    paint_settings = get_paint_settings(data, flipx, flipy, 0)
    work_layer_data = get_work_layer_data(data)

    mat = obj.material_slots[face.material_index].material

    mat_list = context.scene.sprytile_mats
    for mat_data in mat_list:
        if mat_data.mat_id == mat.name:
            for grid in mat_data.grids:
                face[grid_layer_id] = grid.id
                face[grid_layer_tileid] = tile_id
                face[grid_sel_width] = width
                face[grid_sel_height] = height
                face[grid_sel_origin] = tile_id
                face[paint_settings_id] = paint_settings
                face[work_layer_id] = work_layer_data
                break

    mesh.to_mesh(obj.data)
    mesh.faces.index_update()



def get_material_texture_node(mat):
    """
    Returns the first image texture node applied to a material
    :param mat: Material
    :return: ShaderNodeImageTexImage or None
    """
    if mat.node_tree is None:
        return None

    for node in mat.node_tree.nodes:
        if node.bl_static_type == 'TEX_IMAGE':
            return node

    return None


def set_material_texture(mat, texture):
    """
    Apply texture (if possible) to a material
    :param mat: Material
    :param mat: Texture image to apply
    :return: True if successful
    """
    texture_img = get_material_texture_node(mat)

    if texture_img:
        texture_img.image = texture
        return True
    else:
        return False


def get_highest_grid_id(context):
    highest_id = -1
    mat_list = context.scene.sprytile_mats
    for mat_data in mat_list:
        for grid in mat_data.grids:
            highest_id = max(grid.id, highest_id)
    return highest_id


def validate_grids(context):
    """this is almost the same as in sprytile code, just set the grid to 1 px"""
    mat_list = bpy.data.materials
    mat_data_list = context.scene.sprytile_mats

    # Validate the material IDs in scene.sprytile_mats
    for check_mat_data in mat_data_list:
        mat_idx = mat_list.find(check_mat_data.mat_id)
        if mat_idx > -1:
            continue

        # This mat data id not found in materials
        # Loop through materials looking for one
        # that doesn't appear in sprytile_mats list
        for check_mat in mat_list:
            mat_unused = True
            for mat_data in mat_data_list:
                if mat_data.mat_id == check_mat.name:
                    mat_unused = False
                    break

            if mat_unused:
                target_mat_id = check_mat_data.mat_id
                check_mat_data.mat_id = check_mat.name
                for grid in check_mat_data.grids:
                    grid.mat_id = check_mat.name
                for list_display in context.scene.sprytile_list.display:
                    if list_display.mat_id == target_mat_id:
                        list_display.mat_id = check_mat.name
                break

    remove_idx = []

    # Filter out mat data with invalid IDs or users
    for idx, mat in enumerate(mat_data_list.values()):
        mat_idx = mat_list.find(mat.mat_id)
        if mat_idx < 0:
            remove_idx.append(idx)
            continue
        if (mat.mat_id == "Dots Stroke"):
            remove_idx.append(idx)
            continue
        if mat_list[mat_idx].users == 0:
            remove_idx.append(idx)
        for grid in mat.grids:
            grid.mat_id = mat.mat_id
    remove_idx.reverse()
    for idx in remove_idx:
        mat_data_list.remove(idx)

    # Loop through available materials, checking if mat_data_list has
    # at least one entry for each material
    for mat in mat_list:
        if mat.users == 0:
            continue
        is_mat_valid = False
        for mat_data in mat_data_list:
            if mat_data.mat_id == mat.name:
                is_mat_valid = True
                break
        if is_mat_valid is False and mat.name != "Dots Stroke":
            mat_data_entry = mat_data_list.add()
            mat_data_entry.mat_id = mat.name
            mat_grid = mat_data_entry.grids.add()
            mat_grid.mat_id = mat.name
            mat_grid.id = get_highest_grid_id(context) + 1

            mat_grid.grid = (1, 1)
            addon_prefs = bpy.context.preferences.addons['SpryTile'].preferences
            if addon_prefs:
                mat_grid.auto_pad_offset = addon_prefs.default_pad_offset

    context.object.sprytile_gridid = get_highest_grid_id(context)
    bpy.ops.sprytile.build_grid_list()


def assign_material(context, obj, material, sprytile_installed):
    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj

    if sprytile_installed:
        validate_grids(context)
        bpy.data.materials.update()

        bpy.ops.sprytile.texture_setup('INVOKE_DEFAULT')
        validate_grids(context)
        bpy.data.textures.update()

        addon_prefs = context.preferences.addons['SpryTile'].preferences
        if addon_prefs:
            if addon_prefs.auto_pixel_viewport:
                bpy.ops.sprytile.viewport_setup('INVOKE_DEFAULT')
            if addon_prefs.auto_grid_setup:
                bpy.ops.sprytile.setup_grid('INVOKE_DEFAULT')


def verify_bmesh_layers(bm):
    # Verify layers are created
    for layer_name in UvDataLayers.LAYER_NAMES:
        layer_data = bm.faces.layers.int.get(layer_name)
        if layer_data is None:
            bm.faces.layers.int.new(layer_name)

        for el in [bm.faces, bm.verts, bm.edges]:
            el.index_update()
            el.ensure_lookup_table()

        bm.loops.layers.uv.verify()


def update(context):
    bpy.ops.sprytile.texture_setup('INVOKE_DEFAULT')
    validate_grids(context)
    bpy.data.textures.update()

    addon_prefs = context.preferences.addons['SpryTile'].preferences
    if addon_prefs:
        if addon_prefs.auto_pixel_viewport:
            bpy.ops.sprytile.viewport_setup('INVOKE_DEFAULT')
        if addon_prefs.auto_grid_setup:
            bpy.ops.sprytile.setup_grid('INVOKE_DEFAULT')