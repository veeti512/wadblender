import os
import math
from collections import defaultdict

import bpy

from .create_materials import apply_textures, pack_textures
from .objects import lara_skin_names, lara_skin_joints_names


def extract_pivot_points(meshnames, joints, scale):
    root_name = meshnames[0]
    parent = root_name
    prev = parent
    stack = [root_name] * 1000
    pivot_points = {}
    pivot_points[root_name] = (0., 0., 0.)
    parents = {}
    if len(joints) > 0:
        for j in range(1, len(meshnames)):
            op, dx, dy, dz = joints[j-1]
            cur = meshnames[j]
            if op == 0:
                parent = prev
            elif op == 1:
                parent = stack.pop()
            elif op == 2:
                parent = prev
                stack.append(parent)
            else:
                parent = stack[-1]

            parents[cur] = parent
            px, py, pz = pivot_points[parent]
            pivot_points[cur] = (px + dx / scale, py + dy / scale, pz + dz / scale)
            prev = cur

    return pivot_points


def join_skin(lara_skin_meshes, lara_skin_joints_meshes, vertexfile, d=0.005):
    def find_overlapping_vertices(bone, joint):
        bone = next(mesh for mesh in lara_skin_meshes if bone in mesh.name)
        joint = next(mesh for mesh in lara_skin_joints_meshes if joint in mesh.name)

        vertices = []
        for vert in bone.data.vertices:
            # find closest skin joint vertex
            dist = float('inf')
            idx = -1
            for v in joint.data.vertices:
                cur_dist = (joint.matrix_world @ v.co - bone.matrix_world @ vert.co).length
                if cur_dist < dist:
                    dist = cur_dist
                    idx = v.index
            
            # if vertex is close enough, add it to vertex group
            if dist < d :
                vertices.append(idx)

        joint.vertex_groups.new(name=bone.name + '_BONE')
        joint.vertex_groups[bone.name + '_BONE'].add(vertices, 1.0, "ADD")
        return vertices


    vx = defaultdict(set)
    for i, sjm in enumerate(lara_skin_joints_meshes):
        for v in sjm.data.vertices:
            vx[i].add(v.index)

    with open(vertexfile, 'r') as f:
        lines = f.readlines()

    for line in lines:
        # find non overlapping skin joint vertices (the ones that do not connect directly to adjacent meshes)
        joint, bone = line.split()
        idx = next(k for k, e in enumerate(lara_skin_joints_meshes) if joint in e.name)
        vertices = find_overlapping_vertices(bone, joint)
        for e in vertices:
            vx[idx].discard(e)

    # add them to all vertex groups (e.g. the vertices in the middle of the knee 
    # are added to the vertex groups of both thigh and leg)
    for k, v in vx.items():
        joint = lara_skin_joints_meshes[k]
        for vg in joint.vertex_groups:
            vg.add(list(vx[k]), 1.0, "ADD")


def create_lara_skeleton(rig, pivot_points, lara_skin_meshes, lara_skin_joints_meshes, bonesfile, vertexfile, scale):
    # create bones
    bpy.ops.object.mode_set(mode='EDIT')
    amt = rig.data

    def create_bone(node, parent=None, child=None):
        bonename = next(
            mesh.name + '_BONE' for mesh in lara_skin_meshes if node in mesh.name)
        bone = amt.edit_bones.new(bonename)
        bone.head = pivot_points[node]
        x, y, z = pivot_points[node]

        if 'foot' in bonename:
            bone.tail = (x, y + 100 / scale, z)
        else:
            bone.tail = (x, y + 45 / scale, z)

        if parent is not None:
            parent = next(
                mesh.name + '_BONE' for mesh in lara_skin_meshes if parent in mesh.name)
            bone.parent = amt.edit_bones[parent]

    with open(bonesfile, 'r') as f:
        for line in f:
            create_bone(*line.split())

    # weight paint
    for mesh in lara_skin_meshes:
        bonename = mesh.name + '_BONE'
        mesh.vertex_groups.new(name=bonename)
        mesh.vertex_groups[bonename].add(
            [vert.index for vert in mesh.data.vertices], 1.0, "ADD")
        mesh.parent = rig
        modifier = mesh.modifiers.new(type='ARMATURE', name=rig.name)
        modifier.object = rig

    join_skin(lara_skin_meshes, lara_skin_joints_meshes, vertexfile)

    for mesh in lara_skin_joints_meshes:
        mesh.parent = rig
        modifier = mesh.modifiers.new(type='ARMATURE', name=rig.name)
        modifier.object = rig


def paint_vertex(mesh):
    vcol_layer = mesh.vertex_colors.new(name='shade')

    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            vcol_layer.data[loop_index].color = (0.5, 0.5, 0.5, 1.0)


def main(context, materials, wad, options): 
    main_collection = bpy.data.collections.get('Collection')
    col_lara = bpy.data.collections.new('Outfit')
    main_collection.children.link(col_lara)

    anim = 'LARA'

    col = col_lara

    movables = {}
    pivot_points = {}
    animations = {}
    meshes2 = []  
    lara_objs = [] 
    for i, movable in enumerate(wad.movables):
        idx = str(movable.idx)
        if idx in options.mov_names:
            movable_name = options.mov_names[idx]
        else:
            movable_name = 'MOVABLE' + idx

        if movable_name not in {'LARA_SKIN', 'LARA_SKIN_JOINTS'}:
            continue

        mesh_objects = []
        bodyparts_names = []
        for j, m in enumerate(movable.meshes):

            if movable_name == 'LARA_SKIN':
                bodypart_name = lara_skin_names[j] 
            elif movable_name == 'LARA_SKIN_JOINTS':
                bodypart_name = lara_skin_joints_names[j]
            else:
                continue

            verts = [[v/options.scale for v in e] for e in m.vertices]
            faces = [e.face for e in m.polygons]
            normals = m.normals

            bodyparts_names.append(bodypart_name)

            mesh_name = bodypart_name
            mesh_data = bpy.data.meshes.new(mesh_name)
            mesh_data.from_pydata(verts, [], faces)
            if normals:
                for v, n in zip(mesh_data.vertices, normals):
                    v.normal = n

            mesh_obj = bpy.data.objects.new(mesh_name, mesh_data)
            col.objects.link(mesh_obj)

                
            if not options.one_material_per_object:
                apply_textures(context, m, mesh_obj, materials, options)
                if options.flip_normals:
                    mesh_obj.data.flip_normals()
            else:
                meshes2.append(m)
                lara_objs.append(mesh_obj)

            mesh_objects.append(mesh_obj)


            paint_vertex(mesh_data)


        movables[movable_name] = mesh_objects
        ppoints = extract_pivot_points(bodyparts_names, movable.joints, options.scale)
        pivot_points[movable_name] = ppoints
        for bodypart, obj in zip(bodyparts_names, mesh_objects):
            obj.location = ppoints[bodypart]

    if options.one_material_per_object:
        pack_textures(context, meshes2, lara_objs, options, anim)

        for obj in lara_objs:
            if options.flip_normals:
                obj.data.flip_normals()

    amt = bpy.data.armatures.new(anim + '_BONES')
    rig = bpy.data.objects.new(anim + "_RIG", amt)
    col.objects.link(rig)
    bpy.context.view_layer.objects.active = rig

    cur_script_path = os.path.dirname(os.path.realpath(__file__))
    bonesfile = cur_script_path + '\\resources\\bones.txt'
    vertexfile = cur_script_path + '\\resources\\skin_links.txt'
    create_lara_skeleton(rig, pivot_points['LARA_SKIN'], movables['LARA_SKIN'],
                        movables['LARA_SKIN_JOINTS'], bonesfile, vertexfile, options.scale)

    rig.rotation_mode = 'ZXY'
    bpy.ops.object.mode_set(mode="OBJECT")
    rig.rotation_euler[1] = math.pi
    rig.rotation_euler[0] = math.pi/2
    
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.data.objects.remove(rig, do_unlink=True)

    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    if options.export_obj:
        filepath = options.path + '\\{}.obj'.format(anim)

        bpy.ops.object.select_all(action='DESELECT')
        for obj in col.objects:
            obj.select_set(True)
        bpy.ops.export_scene.obj(filepath=filepath, axis_forward='Z', use_selection=True)
        mtl_path = filepath[:-3] + 'mtl'
        line1 = 'map_Ka {}.png\n'.format(anim)
        line2 = 'map_Kd {}.png'.format(anim)
        with open(mtl_path, 'a') as f:
            f.write(line1)
            f.write(line2)
