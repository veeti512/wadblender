import json
from typing import List, Tuple, Dict
from collections import defaultdict

import bpy
from mathutils import Euler


def create_animations(item_idx, rig, bonenames, animations, options):
    if rig.animation_data is None:
        rig.animation_data_create()

    for idx, animation in enumerate(animations):
        if item_idx in options.anim_names and str(idx) in options.anim_names[item_idx]:
            name = ' - '.join((rig.name, str(idx).zfill(3), options.anim_names[item_idx][str(idx)])) 
        else:
            name = ' - '.join((rig.name, str(idx).zfill(3))) 
        action = bpy.data.actions.new(name)

        offsets = [keyframe.offset for keyframe in animation.keyFrames]
        rotations = defaultdict(list)
        for keyframe in animation.keyFrames:
            for bonename, rot in zip(bonenames, keyframe.rotations):
                angle = Euler(rot, 'ZXY')

                angle = angle.to_quaternion()
                rotations[bonename].append(angle)

        for axis in [0, 1, 2]:
            fc = action.fcurves.new(
                data_path='pose.bones["{}"].location'.format(bonenames[0]), index=axis)
            keyframe_points = fc.keyframe_points
            keyframe_points.add(len(offsets))
            for j, val in enumerate(offsets):
                k = 0
                v = val[axis]
                    
                keyframe_points[j].co = (j, v / options.scale)

        for bonename in bonenames:
            for axis in [0, 1, 2, 3]:
                data_path = 'pose.bones["{}"].rotation_quaternion'.format(
                    bonename)
                fc = action.fcurves.new(data_path=data_path, index=axis)
                keyframe_points = fc.keyframe_points
                keyframe_points.add(len(rotations[bonename]))
                for j, rot in enumerate(rotations[bonename]):
                    keyframe_points[j].co = (j, rot[axis])

        action.use_fake_user = True


        track = rig.animation_data.nla_tracks.new()
        name = action.name
        action = bpy.data.actions[name]
        track.name = name
        track.strips.new(action.name, start=0, action=action)

    if options.export_fbx:
        bpy.ops.object.select_all(action='DESELECT')
        rig.select_set(True)
        bpy.context.view_layer.objects.active = rig
        filepath = options.path + '\\{}.fbx'.format(rig.name)
        bpy.ops.export_scene.fbx(
            filepath=filepath, axis_forward='Z', use_selection=True,
            add_leaf_bones=False, bake_anim_use_all_actions=False, 
            bake_anim_use_nla_strips=True
            )


def save_animations_data(item_idx, animations, filename, options):
    path = options.path

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

    animations_names = options.anim_names
    states_names = options.state_names

    for state in states:
        animations_state = []
        for idx, a in enumerate(animations):
            if a.stateID != state:
                continue

            data = AnimationData()
            data.idx = str(idx).zfill(3)
            str_idx = str(idx)
            if item_idx in animations_names and str_idx in animations_names[item_idx]:
                data.name = animations_names[item_idx][str_idx]
            else:
                data.name = data.idx

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
        if item_idx in states_names and str(state) in states_names[item_idx]:
            saves[s] = states_names[item_idx][str(state)], animations_state
        else:
            saves[s] = 'UNKNOWN_STATE', animations_state

    with open(path + '\\' + filename + '.json', 'w') as f:
        json.dump(saves, f, indent=4)
