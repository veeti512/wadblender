import bpy
from mathutils import Quaternion, Euler
import math
import os
from collections import defaultdict



def create_animation(rig, bonenames, offsets, rots, name):
    bpy.ops.object.mode_set(mode="OBJECT")

    if rig.animation_data is None:
        rig.animation_data_create()

    bpy.context.view_layer.objects.active = rig

    action = bpy.data.actions.new(rig.name + '_' + name)
    action.name = rig.name + '_' + name

    rotations = defaultdict(list)
    for keyframe in rots:
        for bonename, rotation in zip(bonenames, keyframe):
            angle = [math.radians(e) for e in rotation[:3]]
            angle = Euler(angle, 'ZXY')
            angle = angle.to_quaternion()
            rotations[bonename].append(angle)

    for axis in [0, 1, 2]:
        fc = action.fcurves.new(
            data_path='pose.bones["{}"].location'.format(bonenames[0]), index=axis)
        keyframe_points = fc.keyframe_points
        keyframe_points.add(len(offsets))
        for j, val in enumerate(offsets):
            v = val[axis]
                
            keyframe_points[j].co = (j, v)

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
    track.name = rig.name + '_' + name
    track.strips.new(action.name, start=0, action=action)


def read_some_data(context, filepath, group, name):
    context = bpy.context
    old_objs = set(context.scene.objects)
    bpy.ops.import_scene.fbx(filepath=filepath)
    imported_objs = set(context.scene.objects) - old_objs
    obj = [e for e in imported_objs if e.type == 'ARMATURE'][0]
    bonenames = [e.name for e in obj.pose.bones]
    print(bonenames)

    fcurves = obj.animation_data.action.fcurves
    oldname = obj.animation_data.action.name
    if name == "":
        name = oldname

    keyframes_count = len(fcurves[0].keyframe_points)

    # read keyframes from anim file
    data = {}
    for fcurve in fcurves:

        if "scale" in fcurve.data_path or "HIPS" in fcurve.data_path or ('location' in fcurve.data_path and fcurve.data_path != 'location'):
            # trle does not support scale animation
            # root motion/rotation is applied to the entire rig,
            # so discard the hips bone datapath
            continue
        else:
            axis = fcurve.array_index
            data[(fcurve.data_path, axis)] = []
            for i in range(keyframes_count):
                data[(fcurve.data_path, axis)].append(fcurve.evaluate(i))


    # initialize rotations and locations lists for each of the body parts
    # and keyframes_count keyframes
    n = len(bonenames)
    rotations = [[] for _ in range(n)]
    for i in range(n):
        for j in range(keyframes_count):
            rotations[i].append([0, 0, 0, 0])

    locations = [[0, 0, 0] for _ in range(keyframes_count)]

    # For each fcurve
    bones = set()
    for datapath, kf_points in data.items():
        if "location" == datapath[0]:  # this is the root location
            for i in range(keyframes_count):
                locations[i][datapath[1]] = kf_points[i]  # 512 is 1m in trle
                # mixamo animations ground is at the height of the foot pivot point
                # so optionally rise the z offset by the height of the foot mesh
                # if datapath[1] == 2:
                #     locations[i][2] += zoffset
            continue

        if datapath[0] != 'location' and datapath[0] != 'rotation_euler':
            # location keyframes are discarded except for the hips
            bonename = datapath[0].split('"')[1]
        else:
            # the datapath for the hips rotations is rotation_euler
            bonename = bonenames[0]
        bones.add(bonename)

        # save bodyparts rotations in the same order as wad tool
        axis = datapath[1]
        idx = bonenames.index(bonename)
        for i in range(keyframes_count):
            rotations[idx][i][axis] = kf_points[i]

    # angles conversion
    for j, e in enumerate(rotations):
        if bonenames[j] not in bones:
            continue


        if j == 0:
            for i in range(keyframes_count):
                angle = e[i][:3]
                angle = Euler(angle, 'XYZ')
                angle = angle.to_quaternion()
                angle = angle.to_euler('ZXY')
                rot = Euler((math.pi/2, math.pi, 0), 'ZXY')
                angle.rotate(rot)
                
                angles = [math.degrees(p) for p in angle]
                rotations[j][i][0] = angles[0]
                rotations[j][i][1] = angles[1]
                rotations[j][i][2] = angles[2]

        else:
            for i in range(keyframes_count):
                q = Quaternion(e[i])
                euler = q.to_euler("ZXY")
                angles = [math.degrees(e) for e in euler]
                rotations[j][i][0] = angles[0]
                rotations[j][i][1] = angles[1]
                rotations[j][i][2] = angles[2]
                if j == 14 or j == 3 or j == 6:
                    rotations[j][i][0] -= 180



    rots = [[] for _ in range(keyframes_count)]
    for kf in range(keyframes_count):
        for part in range(n):
            rots[kf].append(rotations[part][kf])


    for l in locations:
        l[0], l[1], l[2] = -l[0], -l[2], -l[1]

    rig = bpy.data.objects[group]
    target_bonenames = [e.name for e in rig.pose.bones]
    bpy.data.actions.remove(bpy.data.actions[oldname])
    create_animation(rig, target_bonenames, locations, rots, name)

    for o in imported_objs:
        bpy.data.objects.remove(o, do_unlink=True)

    return {'FINISHED'}


# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


class ImportSomeData(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "import_wad.mixamo"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import Mixamo Animation"

    # ImportHelper mixin class uses this
    filename_ext = ".fbx"

    filter_glob: StringProperty(
        default="*.fbx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def get_enum_items(self, context):

        res = []
        for obj in bpy.data.objects:
            if obj.type == "ARMATURE":
                res.append((obj.name,obj.name))

        res.sort(key=lambda x: x[0]!='LARA_RIG')

        return [(a[0], a[1], 'Instance group "%s"'%a[0]) for a in res]

    group: EnumProperty(
    name = "Target Rig", items = get_enum_items,
    description = "Rig where to copy keyframes")

    name: StringProperty(
        name = "Rename action",
        description = "Insert new name of action",
        default = ""
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
        row.prop(self, "group", text="")

        row = box.row(align=True)
        row = row.split(factor=0.35, align=True)
        row.label(text="Rename:")
        row.prop(self, "name", text="")
        
        

    def execute(self, context):
        return read_some_data(context, self.filepath, self.group, self.name)


# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(ImportSomeData.bl_idname, text="Mixamo to TRLE (.fbx)")


def register():
    bpy.utils.register_class(ImportSomeData)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportSomeData)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.import_wad.mixamo('INVOKE_DEFAULT')
