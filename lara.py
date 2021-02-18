import bpy
import os
import math

from .common import apply_textures, extract_pivot_points, create_lara_skeleton, create_animations, save_animations_data
from .objects import lara_skin_names, lara_skin_joints_names


def main(materials, wad, options): 

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
        for movable in wad.movables:
            item_idx = str(movable.idx)
            if item_idx in options.mov_names:
                movable_name = options.mov_names[item_idx]
            else:
                movable_name = 'MOVABLE' + item_idx

            if movable_name == anim:
                found = True
                break

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
        for i, movable in enumerate(wad.movables):
            idx = str(movable.idx)
            if idx in options.mov_names:
                movable_name = options.mov_names[idx]
            else:
                movable_name = 'MOVABLE' + idx
            if movable_name not in {anim, 'LARA_SKIN', 'LARA_SKIN_JOINTS'}:
                continue


            animations[movable_name] = movable.animations

            mesh_objects = []
            bodyparts_names = []
            for j, m in enumerate(movable.meshes):
                verts = [[v/options.scale for v in e] for e in m.vertices]
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

                apply_textures(m, mesh_obj, materials)

                mesh_objects.append(mesh_obj)

                if options.flip_normals:
                    mesh_data.flip_normals()

            movables[movable_name] = mesh_objects
            ppoints = extract_pivot_points(bodyparts_names, movable.joints, options.scale)
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
        bonesfile = cur_script_path + '\\resources\\bones.txt'
        vertexfile = cur_script_path + '\\resources\\vertex_mapping.txt'
        create_lara_skeleton(rig, pivot_points['LARA_SKIN'], movables['LARA_SKIN'],
                            movables['LARA_SKIN_JOINTS'], bonesfile, vertexfile, options.scale)

        bonenames = [mesh_data.name + '_BONE' for mesh_data in movables['LARA_SKIN']]

        rig.rotation_mode = 'ZXY'
        bpy.ops.object.mode_set(mode="OBJECT")
        rig.rotation_euler[1] = math.pi
        rig.rotation_euler[0] = math.pi/2
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        if options.export_fbx:
            filepath = options.path + '\\{}.fbx'.format(anim)
            bpy.ops.object.select_all(action='DESELECT')

            bpy.context.view_layer.objects.active = rig
            for obj in col.objects:
                obj.select_set(True)
            bpy.ops.export_scene.fbx(filepath=filepath, axis_forward='Z', use_selection=True, add_leaf_bones=False, bake_anim_use_all_actions =False)

        if options.export_obj:
            filepath = options.path + '\\{}.obj'.format(anim)

            bpy.ops.object.select_all(action='DESELECT')
            for obj in col.objects:
                obj.select_set(True)
            bpy.ops.export_scene.obj(filepath=filepath, axis_forward='Z', use_selection=True)

        if options.import_anims:
            create_animations(item_idx, rig, bonenames, animations[anim], options)

        if options.export_json:
            save_animations_data(animations[anim], anim, options)
            
        bpy.context.view_layer.layer_collection.children['Collection'].children['Lara'].children[anim].hide_viewport = True

