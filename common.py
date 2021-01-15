import bpy
from mathutils import Vector
from collections import defaultdict
import math
import json
from typing import List, Tuple, Dict

# def createMaterial(uvmap):
#     mat = bpy.data.materials.new(name='WAD material')
#     mat.use_nodes = True
#     bsdf = mat.node_tree.nodes["Principled BSDF"]
#     texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
#     texImage.image = bpy.data.images.load(uvmap)
#     mat.node_tree.links.new(
#         bsdf.inputs['Base Color'], texImage.outputs['Color'])
#     mat.node_tree.nodes["Image Texture"].interpolation = 'Closest'
#     bpy.ops.image.open(filepath=uvmap, files=[{"name":"textures.png"}])

#     mat.node_tree.nodes["Image Texture"].image = bpy.data.images["textures.png"]
#     return mat


def createMaterials(name, uvmap):
    materials = []
    ids = []
    for i in range(32):
        mat = bpy.data.materials.new(name=name + '_' + str(i))
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
        texImage.image = bpy.data.images.load(uvmap)
        mat.node_tree.links.new(
            bsdf.inputs['Base Color'], texImage.outputs['Color'])
        mat.node_tree.nodes["Image Texture"].interpolation = 'Closest'
        bpy.ops.image.open(filepath=uvmap, files=[{"name":"textures.png"}])
        bsdf.inputs[7].default_value = 1.0 - i / 31

        mat.node_tree.nodes["Image Texture"].image = bpy.data.images["{}.png".format(name)]
        materials.append(mat)
        ids.append(bpy.data.materials.find(mat.name))

    for i in range(32, 64):
        mat = bpy.data.materials.new(name=name + '_' + str(i))
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
        texImage.image = bpy.data.images.load(uvmap)
        mat.node_tree.links.new(
            bsdf.inputs['Base Color'], texImage.outputs['Color'])
        mat.node_tree.nodes["Image Texture"].interpolation = 'Closest'
        bpy.ops.image.open(filepath=uvmap, files=[{"name":"textures.png"}])
        bsdf.inputs[7].default_value = 1.0 - (i-32) / 31
        bsdf.inputs[18].default_value = 0.

        mat.node_tree.nodes["Image Texture"].image = bpy.data.images["{}.png".format(name)]
        mat.blend_method = 'BLEND'
        materials.append(mat)
        ids.append(bpy.data.materials.find(mat.name))

    return materials


def apply_textures(mesh, obj, materials):

    for i in range(64):
        obj.data.materials.append(materials[i])

    bpy.ops.mesh.uv_texture_add()
    for polygon, blender_polygon in zip(mesh.polygons, obj.data.polygons):
        a, b, c, d = map(Vector, polygon.tbox)
        data = obj.data.uv_layers.active.data
        if len(polygon.face) == 4:
            i, j, k, l = blender_polygon.loop_indices
            data[i].uv, data[j].uv, data[k].uv, data[l].uv = a, b, c, d
        else:
            i, j, k = blender_polygon.loop_indices
            if polygon.order == 0:
                data[i].uv, data[j].uv, data[k].uv = a, b, d
            elif polygon.order == 2:
                data[i].uv, data[j].uv, data[k].uv = b, c, a
            elif polygon.order == 4:
                data[i].uv, data[j].uv, data[k].uv = c, d, b
            else:
                data[i].uv, data[j].uv, data[k].uv = d, a, c

        if hasattr(polygon, 'intensity') and polygon.shine == 1:
            if polygon.opacity == 1:
                blender_polygon.material_index = polygon.intensity - 1
            else:
                blender_polygon.material_index = polygon.intensity - 1 + 32
            if polygon.intensity > 0:
                print(mesh)
        else:
            blender_polygon.material_index = 0


def create_lara_skeleton(rig, pivot_points, lara_skin_meshes, lara_skin_joints_meshes, bonesfile, vertexfile, scale):
    # create bones
    bpy.ops.object.mode_set(mode='EDIT')
    amt = rig.data

    def create_bone(node, parent=None, child=None):
        bonename = next(mesh.name + '_BONE' for mesh in lara_skin_meshes if node in mesh.name)
        bone = amt.edit_bones.new(bonename)
        bone.head = pivot_points[node]
        if child:
            bone.tail = pivot_points[child]
        else:
            x, y, z = pivot_points[node]
            if 'FOOT' in node:
                bone.tail = (x, y + 10/scale, z + 25/scale)
            else:
                bone.tail = (x, y + 50 / scale, z)

        if parent is not None:
            parent = next(mesh.name + '_BONE' for mesh in lara_skin_meshes if parent in mesh.name)
            bone.parent = amt.edit_bones[parent]

    with open(bonesfile, 'r') as f:
        for line in f:
            create_bone(*line.split())

    # weight paint
    for mesh in lara_skin_meshes:
        bonename = mesh.name + '_BONE'
        mesh.vertex_groups.new(name=bonename)
        mesh.vertex_groups[bonename].add([vert.index for vert in mesh.data.vertices], 1.0, "ADD")
        mesh.parent = rig
        modifier = mesh.modifiers.new(type='ARMATURE', name=rig.name)
        modifier.object = rig

    with open(vertexfile, 'r') as f:
        lines = f.readlines()

    for i in range(0, len(lines), 2):
        mesh_a, mesh_b = lines[i].split()
        mesh_a = next(mesh for mesh in lara_skin_joints_meshes if mesh_a in mesh.name)
        mesh_b = next(mesh for mesh in lara_skin_meshes if mesh_b in mesh.name)
        vertices = [int(c) for c in lines[i + 1].split()]
        mesh_a.vertex_groups.new(name=mesh_b.name + '_BONE')
        mesh_a.vertex_groups[mesh_b.name + '_BONE'].add(vertices, 1.0, "ADD")

    for mesh in lara_skin_joints_meshes:
        mesh.parent = rig
        modifier = mesh.modifiers.new(type='ARMATURE', name=rig.name)
        modifier.object = rig


def create_animations(rig, bonenames, ppoints, animations, options): #, scale, path, export_fbx, export_json, create_nla):
    bpy.ops.object.mode_set(mode="OBJECT")

    if rig.animation_data is None:
        rig.animation_data_create()

    for bonename in bonenames:
        # this first rotates y, then x and z
        if bonename in rig.pose.bones:
            rig.pose.bones[bonename].rotation_mode = 'ZXY'


    bpy.context.view_layer.objects.active = rig
    
    # if options.rotate:
    #     bpy.context.object.rotation_euler[0] = -math.pi/2
    #     bpy.context.object.rotation_euler[2] = -math.pi
    #     bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


    for idx, animation in enumerate(animations):
        action = bpy.data.actions.new(str(idx).zfill(3))
        action.name = rig.name + str(idx).zfill(3)

        offsets = [keyframe.offset for keyframe in animation.keyFrames]
        rotations = defaultdict(list)
        for keyframe in animation.keyFrames:
            for bonename, rot in zip(bonenames, keyframe.rotations):
                rotations[bonename].append(rot)

        for axis in [0, 1, 2]:
            fc = action.fcurves.new(data_path='pose.bones["{}"].location'.format(bonenames[0]), index=axis)
            keyframe_points = fc.keyframe_points
            keyframe_points.add(len(offsets))
            for j, val in enumerate(offsets):
                keyframe_points[j].co = (j, val[axis] / options.scale)

        for bonename in bonenames:
            for axis in [0, 1, 2]:
                data_path = 'pose.bones["{}"].rotation_euler'.format(
                    bonename)
                fc = action.fcurves.new(data_path=data_path, index=axis)
                keyframe_points = fc.keyframe_points
                keyframe_points.add(len(rotations[bonename]))
                for j, rot in enumerate(rotations[bonename]):
                    keyframe_points[j].co = (j, rot[axis])

        action.use_fake_user = True

        if options.create_nla:
            track = rig.animation_data.nla_tracks.new()
            track.name = str(idx)
            track.strips.new(action.name, start=0, action=action)

    if options.export_fbx:
        bpy.ops.object.select_all(action='DESELECT')
        rig.select_set(True)
        bpy.context.view_layer.objects.active = rig
        filepath = options.path + '\\{}.fbx'.format(rig.name)
        bpy.ops.export_scene.fbx(filepath=filepath, axis_forward='Z', use_selection=True, add_leaf_bones=False, bake_anim_use_all_actions =True, bake_anim_use_nla_strips=False)


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
            pivot_points[cur] = (px + dx / scale, py +
                                 dy / scale, pz + dz / scale)
            prev = cur

    return pivot_points



def save_animations_data(animations, path, filename, animationsfile='', statesfile=''):
    states = set()
    for idx, a in enumerate(animations):
        states.add(a.stateID)

    class AnimationData:
        idx: str
        name: str
        bboxes: List[Tuple]
        stateChanges: Dict[str, List[Tuple]]
        commands: List[Tuple[int]]
        frameDuration: int
        speed: int
        acceleration: int
        frameStart: int
        frameEnd: int
        frameIn: int
        nextAnimation: str

    saves = {}

    if animationsfile:
        animations_names = []
        with open(animationsfile, 'r') as f:
            for line in f:
                animations_names.append(line.strip())

    if statesfile:
        states_names = {}
        with open(statesfile, 'r') as f:
            for line in f:
                idx, name = line.split()
                idx = idx.zfill(3)
                states_names[idx] = name

    for state in states:
        animations_state = []
        for idx, a in enumerate(animations):
            if a.stateID != state:
                continue

            data = AnimationData()
            data.idx = str(idx).zfill(3)
            if animationsfile:
                data.name = animations_names[idx]
            data.frameDuration = a.frameDuration
            data.speed = a.speed
            data.acceleration = a.acceleration
            data.frameStart = a.frameStart
            data.frameEnd = a.frameEnd
            data.frameIN = a.frameIn
            data.nextAnimation = str(a.nextAnimation).zfill(3)

            bboxes = []
            for keyframe in a.keyFrames:
                x0, y0, z0 = keyframe.bb1
                x1, y1, z1 = keyframe.bb2
                bboxes.append((x0, y0, z0, x1, y1, z1))

            data.bboxes = bboxes
            data.commands = a.commands

            data.stateChanges = {}
            for sc, dispatches in a.stateChanges.items():
                d = []
                for dispatch in dispatches:
                    nextAnim = str(dispatch[2]).zfill(3)
                    d.append([dispatch[0], dispatch[1], nextAnim, dispatch[3]])

                data.stateChanges[str(sc).zfill(3)] = d

            animations_state.append(data.__dict__)

        s = str(state).zfill(3)
        if statesfile:
            saves[s] = states_names[s], animations_state
        else:
            saves[s] = animations_state

    with open(path + '\\' + filename + '.json', 'w') as f:
        json.dump(saves, f)
