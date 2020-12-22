import bpy
from importlib import reload
import os

from .objects import movable_names
from .common import createMaterial, apply_textures, extract_pivot_points, create_lara_skeleton, create_animations, save_animations_data
from .objects import lara_skin_names, lara_skin_joints_names


def main(path, wadname, w, scale, import_anims, create_nla, export_fbx, export_json):
    uvmap = bpy.data.images.new('textures', w.mapwidth, w.mapheight, alpha=True)
    uvmap.pixels = w.textureMap
    mat = createMaterial(uvmap)
    bpy.data.images["textures"].save_render(path + "textures.png")

    meshes2replace = {}
    meshes2replace['LARA'] = []
    meshes2replace['PISTOLS_ANIM'] = ['LEFT_THIGH', 'RIGHT_THIGH', 'RIGHT_HAND', 'LEFT_HAND']
    meshes2replace['UZI_ANIM'] = ['LEFT_THIGH', 'RIGHT_THIGH', 'RIGHT_HAND', 'LEFT_HAND', 'HEAD']
    meshes2replace['SHOTGUN_ANIM'] = ['RIGHT_HAND', 'HEAD']
    meshes2replace['CROSSBOW_ANIM'] = ['RIGHT_HAND', 'HEAD']
    meshes2replace['GRENADE_GUN_ANIM'] = ['RIGHT_HAND', 'HEAD']
    meshes2replace['SIXSHOOTER_ANIM'] = ['LEFT_THIGH', 'RIGHT_HAND']
    meshes2replace['FLARE_ANIM'] = ['LEFT_HAND']
    meshes2replace['CROWBAR_ANIM'] = ['RIGHT_HAND']
    meshes2replace['TORCH_ANIM'] = ['LEFT_HAND']
    meshes2replace['VEHICLE_EXTRA'] = []
    meshes2replace['LARA_SCREAM'] = ['HEAD']

    main_collection = bpy.data.collections.get('Collection')
    col_lara = bpy.data.collections.new('Lara')
    main_collection.children.link(col_lara)

    for anim, replacements in meshes2replace.items():
        found = False
        for movable in w.movables:
            movable_name = movable_names[movable.idx]
            if movable_name == anim:
                found = True

        if not found:
            continue

        indices = [lara_skin_names.index(name) for name in replacements]

        if anim not in meshes2replace:
            continue

        col = bpy.data.collections.new(anim)
        col_lara.children.link(col)

        movables = {}
        pivot_points = {}
        animations = {}
        for i, movable in enumerate(w.movables):
            movable_name = movable_names[movable.idx]
            if movable_name not in {anim, 'LARA_SKIN', 'LARA_SKIN_JOINTS'}:
                continue


            animations[movable_name] = movable.animations

            mesh_objects = []
            bodyparts_names = []
            for j, m in enumerate(movable.meshes):
                verts = [[v/scale for v in e] for e in m.vertices]
                faces = [e.face for e in m.polygons]
                normals = m.normals

                if movable_name == 'LARA_SKIN':
                    bodypart_name = lara_skin_names[j] 
                elif movable_name == 'LARA_SKIN_JOINTS':
                    bodypart_name = lara_skin_joints_names[j]
                else:
                    bodypart_name = lara_skin_names[j] + '.gun'

                bodyparts_names.append(bodypart_name)

                mesh_name = anim + '_' + bodypart_name
                mesh_data = bpy.data.meshes.new(mesh_name)
                mesh_data.from_pydata(verts, [], faces)
                if normals:
                    for v, n in zip(mesh_data.vertices, normals):
                        v.normal = n

                mesh_obj = bpy.data.objects.new(mesh_name, mesh_data)
                col.objects.link(mesh_obj)
                bpy.context.view_layer.objects.active = mesh_obj

                apply_textures(m, mesh_obj, mat)
                mesh_objects.append(mesh_obj)
                mesh_data.flip_normals()

            movables[movable_name] = mesh_objects
            ppoints = extract_pivot_points(bodyparts_names, movable.joints, scale)
            pivot_points[movable_name] = ppoints
            for bodypart, obj in zip(bodyparts_names, mesh_objects):
                obj.location = ppoints[bodypart]

        for i in range(len(movables['LARA_SKIN'])):
            if i in indices:
                bpy.data.objects.remove(movables['LARA_SKIN'][i], do_unlink=True)
                movables['LARA_SKIN'][i] = movables[anim][i]
            else:
                bpy.data.objects.remove(movables[anim][i], do_unlink=True)

        for obj in movables['LARA_SKIN']:
            if obj.name.endswith('.gun'):
                obj.name = obj.name[:-4]

        amt = bpy.data.armatures.new(anim + '_BONES')
        rig = bpy.data.objects.new(anim + "_RIG", amt)
        col.objects.link(rig)
        bpy.context.view_layer.objects.active = rig

        cur_script_path = os.path.dirname(os.path.realpath(__file__))
        bonesfile = cur_script_path + '\\bones.txt'
        vertexfile = cur_script_path + '\\vertex_mapping.txt'
        animationsfile = cur_script_path + '\\animations_names.txt'
        statesfile = cur_script_path + '\\states.txt'
        create_lara_skeleton(rig, pivot_points['LARA_SKIN'], movables['LARA_SKIN'],
                            movables['LARA_SKIN_JOINTS'], bonesfile, vertexfile, scale)

        bonenames = [mesh_data.name + '_BONE' for mesh_data in movables['LARA_SKIN']]

        if export_fbx:
            filepath = path + '\\{}.fbx'.format(anim)
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action='DESELECT')

            bpy.context.view_layer.objects.active = rig
            for obj in col.objects:
                obj.select_set(True)
            bpy.ops.export_scene.fbx(filepath=filepath, axis_forward='Z', use_selection=True, add_leaf_bones=False, bake_anim_use_all_actions =False)

        if import_anims:
            create_animations(rig, bonenames, pivot_points['LARA_SKIN'], animations[anim], scale, path, export_fbx, export_json, create_nla)

        if export_json:
            if anim == 'LARA':
                save_animations_data(animations[anim], path, anim, animationsfile, statesfile)
            else:
                save_animations_data(animations[anim], path, anim)
            
        bpy.context.view_layer.layer_collection.children['Collection'].children['Lara'].children[anim].hide_viewport = True
