import math

import bpy
from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty
from bpy_extras.io_utils import ImportHelper
from mathutils import Quaternion, Euler


def import_mixamo(context, filepath, target_rig_name, new_action_name):
    context = bpy.context

    # Import mixamo FBX
    old_objs = set(context.scene.objects)
    bpy.ops.import_scene.fbx(filepath=filepath, ignore_leaf_bones=True)
    imported_objs = set(context.scene.objects) - old_objs
    mixamo_rig = next(e for e in imported_objs if e.type == 'ARMATURE')
    mixamo_bonenames = [e.name for e in mixamo_rig.pose.bones]

    fcurves = mixamo_rig.animation_data.action.fcurves
    keyframes_count = len(fcurves[0].keyframe_points)

    # read mixamo keyframes
    data = {}
    for fcurve in fcurves:
        if "scale" in fcurve.data_path or "HIPS" in fcurve.data_path or \
           ('location' in fcurve.data_path and fcurve.data_path != 'location'):
            # trle does not support scale animation.
            # root motion/rotation is applied to the entire rig,
            # so discard the hips bone datapath
            continue
        else:
            axis = fcurve.array_index
            data[(fcurve.data_path, axis)] = []
            for i in range(keyframes_count):
                data[(fcurve.data_path, axis)].append(fcurve.evaluate(i))

    # initialize rotations and locations for each body part and keyframe
    n = len(mixamo_bonenames)
    rotations = [[] for _ in range(n)]
    for i in range(n):
        for j in range(keyframes_count):
            rotations[i].append([0, 0, 0, 0])

    locations = [[0, 0, 0] for _ in range(keyframes_count)]

    # For each fcurve set angles and locations
    bones = set()
    for datapath, kf_points in data.items():
        if "location" == datapath[0]:  # this is the root location
            for i in range(keyframes_count):
                locations[i][datapath[1]] = kf_points[i]
            continue

        # location fcurves are discarded except for root motion
        if datapath[0] != 'location' and datapath[0] != 'rotation_euler':
            bonename = datapath[0].split('"')[1]
        else:
            # the fcurve for the hips rotations (root motion) is rotation_euler
            # (first bone is always the root)
            bonename = mixamo_bonenames[0]
        bones.add(bonename)

        # save bodypart rotations
        axis = datapath[1]
        idx = mixamo_bonenames.index(bonename)
        for i in range(keyframes_count):
            rotations[idx][i][axis] = kf_points[i]

    # angles conversion
    for j, e in enumerate(rotations):
        if mixamo_bonenames[j] not in bones:
            continue

        if j == 0:
            # mixamo root motion rotation mode is Euler XYZ
            for i in range(keyframes_count):
                angle = e[i][:3]
                angle = Euler(angle, 'XYZ').to_quaternion()
                rot = Euler((math.pi/2, math.pi, 0), 'ZXY')
                angle.rotate(rot)
                rotations[j][i] = angle
        else:
            # other bones are in quaternions
            for i in range(keyframes_count):
                rotations[j][i] = Quaternion(e[i])

    for l in locations:
        l[0], l[1], l[2] = -l[0], -l[2], -l[1]

    target_rig = bpy.data.objects[target_rig_name]
    target_bonenames = [e.name for e in target_rig.pose.bones]

    old_action_name = mixamo_rig.animation_data.action.name
    bpy.data.actions.remove(bpy.data.actions[old_action_name])

    # create new animation
    bpy.ops.object.mode_set(mode="OBJECT")
    if target_rig.animation_data is None:
        target_rig.animation_data_create()

    bpy.context.view_layer.objects.active = target_rig

    if new_action_name == "":
        new_action_name = old_action_name
    action = bpy.data.actions.new(target_rig.name + '_' + new_action_name)

    for axis in [0, 1, 2]:
        dp = 'pose.bones["{}"].location'.format(target_bonenames[0])
        fc = action.fcurves.new(data_path=dp, index=axis)
        keyframe_points = fc.keyframe_points
        keyframe_points.add(len(locations))
        for j, val in enumerate(locations):
            keyframe_points[j].co = (j, val[axis])

    for bonename in target_bonenames:
        for axis in [0, 1, 2, 3]:
            dp = 'pose.bones["{}"].rotation_quaternion'.format(bonename)
            fc = action.fcurves.new(data_path=dp, index=axis)
            keyframe_points = fc.keyframe_points
            part_idx = target_bonenames.index(bonename)
            keyframe_points.add(len(rotations[part_idx]))
            for j, rot in enumerate(rotations[part_idx]):
                keyframe_points[j].co = (j, rot[axis])

    action.use_fake_user = True

    track = target_rig.animation_data.nla_tracks.new()
    track.name = action.name
    track.strips.new(action.name, start=0, action=action)

    # remove imported FBX objects
    for o in imported_objs:
        bpy.data.objects.remove(o, do_unlink=True)

    return {'FINISHED'}


class ImportMixamo(Operator, ImportHelper):
    bl_idname = "wadblender.import_mixamo"
    bl_label = "Import Mixamo Animation"

    filename_ext = ".fbx"

    filter_glob: StringProperty(
        default="*.fbx",
        options={'HIDDEN'},
        maxlen=255,
    )

    def get_enum_items(self, context):
        rigs = []
        for obj in bpy.data.objects:
            if obj.type == "ARMATURE":
                rigs.append((obj.name, obj.name, obj.name))

        # put LARA_RIG first if available
        rigs.sort(key=lambda x: x[0] != 'LARA_RIG')

        return rigs

    target_rig: EnumProperty(
        name="Target Rig",
        items=get_enum_items,
        description="")

    new_action_name: StringProperty(
        name="Rename action",
        description="Insert name for target action",
        default=""
    )

    def draw(self, context):
        obj = context.object
        layout = self.layout
        row = layout.row()
        row.label(text='WAD Blender', icon="BLENDER")

        box = layout.box()
        row = box.row(align=True)
        row = row.split(factor=0.35, align=True)
        row.label(text="Target Rig:")
        row.prop(self, "target_rig", text="")

        row = box.row(align=True)
        row = row.split(factor=0.35, align=True)
        row.label(text="Rename:")
        row.prop(self, "new_action_name", text="")

    def execute(self, context):
        return import_mixamo(context, self.filepath, self.target_rig,
                             self.new_action_name)


def menu_func_import(self, context):
    self.layout.operator(ImportMixamo.bl_idname, text="Mixamo to TRLE (.fbx)")


def register():
    bpy.utils.register_class(ImportMixamo)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportMixamo)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.import_wad.mixamo('INVOKE_DEFAULT')
