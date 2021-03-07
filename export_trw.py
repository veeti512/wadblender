import math
import struct

import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, EnumProperty
from bpy.types import Operator
from mathutils import Quaternion


class TRWKeyframe:
    def __init__(self, frame_idx, offsets, rotations):
        self.root_offset = offsets[frame_idx]
        self.rotations = []
        self.bytes_size = 18

        for rot in rotations:
            rotx, roty, rotz, _ = rot[frame_idx]
            self.append_rotation(rotx, roty, rotz)

    def append_rotation(self, x, y, z):
        self.rotations.append((x, y, z))
        self.bytes_size += 4 if sum(e == 0 for e in [x, y, z]) < 2 else 2


class TRW:
    def __init__(self, meshes_cnt, keyframes_cnt, offsets, rotations):
        self.meshes_cnt = meshes_cnt
        self.keyframes_cnt = keyframes_cnt
        self.keyframes = [TRWKeyframe(i, offsets, rotations) for i in range(keyframes_cnt)]
        self.keyframes_words_size = max(k.bytes_size for k in self.keyframes) // 2
        self.keyframes_package_words_size = self.keyframes_cnt * self.keyframes_words_size

    def save(self, filename):
        with open(filename, 'wb') as f:
            f.write(struct.pack('HHHH', 190, 0, 5, 0))  # wadmerger version
            f.write(struct.pack('I', 0))  # keyframe offset
            f.write(struct.pack('B', 1))  # frame duration
            f.write(struct.pack('B', self.keyframes_words_size))
            f.write(struct.pack('H', 0))  # state id
            f.write(struct.pack('H', 0))  # unknown
            f.write(struct.pack('h', 0))  # speed
            f.write(struct.pack('i', 0))  # acceleration
            f.write(struct.pack('II', 0, 0))  # unknown
            f.write(struct.pack('H', 0))  # frame start
            f.write(struct.pack('H', self.keyframes_cnt - 1)) # end keyframe
            f.write(struct.pack('h', 0))  # next anim
            f.write(struct.pack('H', 0))  # frame in
            f.write(struct.pack('H', 0))  # num state changes
            f.write(struct.pack('H', 0))  # changes index
            f.write(struct.pack('H', 0))  # num anim commands
            f.write(struct.pack('H', 0))  # anim commands offset
            f.write(struct.pack('i', -1))  # file marker?
            f.write(struct.pack('H', 0))  # num anim commands
            f.write(struct.pack('I', self.keyframes_package_words_size))
            f.write(struct.pack('I', self.keyframes_cnt))  # num frames
            f.write(struct.pack('I', self.keyframes_cnt))  # num keyframes

            for kf in self.keyframes:
                # use wadmerger for bbox
                f.write(struct.pack('6h', *((0,) * 6))) # null bbox
                f.write(struct.pack('3h', *kf.root_offset))
                f.write(struct.pack('H', self.meshes_cnt))
                for ang in kf.rotations:
                    f.write(struct.pack('3H', *ang))



def export_anim(filepath, rig_name):

    obj = bpy.data.objects[rig_name]

    bonenames = [e.name for e in obj.pose.bones]

    fcurves = obj.animation_data.action.fcurves
    keyframes_count = len(fcurves[0].keyframe_points)

    # read keyframes from anim file
    data = {}
    for fcurve in fcurves:
        axis = fcurve.array_index

        data[(fcurve.data_path, axis)] = []
        for i in range(keyframes_count):
            data[(fcurve.data_path, axis)].append(fcurve.evaluate(i))

    # initialize rotations and locations lists for each body part and keyframe
    n = len(bonenames)
    rotations = [[] for _ in range(n)]
    for i in range(n):
        for j in range(keyframes_count):
            rotations[i].append([0, 0, 0, 0])

    locations = [[0, 0, 0] for _ in range(keyframes_count)]

    # For each fcurve
    for datapath, kf_points in data.items():
        if "location" in datapath[0]:  # this is the hips location
            for i in range(keyframes_count):
                locations[i][datapath[1]] = int(
                    kf_points[i]*512)  # 512 is 1m
            continue
        else:
            # location keyframes are discarded except for the hips
            bonename = datapath[0].split('"')[1]

        # save bodyparts rotations
        axis = datapath[1]
        for i, bone in enumerate(bonenames):
            if bone in datapath[0]:
                idx = i
                break
        else:
            assert False

        idx = bonenames.index(bone)

        for i in range(keyframes_count):
            rotations[idx][i][axis] = kf_points[i]

    # # angles conversion
    for j, e in enumerate(rotations):
        for i in range(keyframes_count):
            angles = Quaternion(e[i]).to_euler("ZXY")
            rotx = round(angles.x*512/math.pi)
            roty = round(angles.y*512/math.pi)
            rotz = round(angles.z*512/math.pi)

            while rotx < 0:
                rotx += 1024

            while roty < 0:
                roty += 1024

            while rotz < 0:
                rotz += 1024

            while rotx >= 1024:
                rotx -= 1024

            while roty >= 1024:
                roty -= 1024

            while rotz >= 1024:
                rotz -= 1024

            rotations[j][i][0] = rotx
            rotations[j][i][1] = roty
            rotations[j][i][2] = rotz

    anim = TRW(n, keyframes_count, locations, rotations)
    anim.save(filepath)


def export(context, filepath, action):
    export_anim(filepath, action)
    return {'FINISHED'}


class ExportAnimTRW(Operator, ExportHelper):
    bl_idname = "wadblender.export_anim_trw"
    bl_label = "Export WADMerger Animation"

    filename_ext = ".trw"

    filter_glob: StringProperty(
        default="*.trw",
        options={'HIDDEN'},
        maxlen=255,
    )

    def get_actions(self, context):
        actions = []
        for obj in bpy.data.objects:
            action_name = (obj.animation_data.action.name
                           if obj.animation_data and obj.animation_data.action
                           else "")
            if action_name and obj.type == "ARMATURE":
                actions.append((obj.name, action_name, action_name))

        return actions

    actions: EnumProperty(
        name="Action", items=get_actions,
        description="Animation to export.")

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text='WAD Blender', icon="BLENDER")

        box = layout.box()
        box.prop(self, "actions")

    def execute(self, context):
        return export(context, self.filepath, self.actions)


def menu_func_export(self, context):
    self.layout.operator("wadblender.export_anim_trw",
                         text="TRLE Animation (.trw)")


def register():
    bpy.utils.register_class(ExportAnimTRW)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ExportAnimTRW)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.export_anim.data('INVOKE_DEFAULT')
