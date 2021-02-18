import os
import math
import bpy
import xml.etree.ElementTree as ET
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, EnumProperty
from bpy.types import Operator
from mathutils import Quaternion
from .objects import lara_skin_names


template = """<?xml version="1.0" encoding="utf-8"?>
<WadAnimation xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <FrameRate>1</FrameRate>
    <StateId>2</StateId>
    <EndFrame>43</EndFrame>
    <NextAnimation>103</NextAnimation>
    <NextFrame>0</NextFrame>
    <Name>STAND_IDLE</Name>
    <StartVelocity>0</StartVelocity>
    <EndVelocity>0</EndVelocity>
    <StartLateralVelocity>0</StartLateralVelocity>
    <EndLateralVelocity>0</EndLateralVelocity>
    <KeyFrames />
    <StateChanges />
    <AnimCommands />
</WadAnimation>
"""


def export_anim(template_anim, rig_name):
    if os.path.exists(template_anim):
        with open(template_anim) as f:
            xml_string = '\n'.join(f.readlines())
    else:
        xml_string = template

    obj = bpy.data.objects[rig_name]

    bonenames = [e.name for e in obj.pose.bones]

    xml_string = xml_string.replace('utf-16', 'utf8')
    tree = ET.ElementTree(ET.fromstring(xml_string))

    # remove template anim keyframes
    keyframes_node = tree.find("KeyFrames")
    for keyframe in keyframes_node.findall("WadKeyFrame"):
        keyframes_node.remove(keyframe)

    fcurves = obj.animation_data.action.fcurves
    keyframes_count = len(fcurves[0].keyframe_points)

    keyframes_cnt_node = tree.find("EndFrame")
    keyframes_cnt_node.text = str(keyframes_count)

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
                locations[i][datapath[1]] = kf_points[i] * 512  # 512 is 1m
            continue
        else:
            # location keyframes are discarded except for the hips
            bonename = datapath[0].split('"')[1]

        # save bodyparts rotations
        axis = datapath[1]
        for i, bone in enumerate(lara_skin_names):
            if bone in datapath[0]:
                idx = i
                print(idx, bone, bonename)
                break
        else:
            assert False

        for i in range(keyframes_count):
            rotations[idx][i][axis] = kf_points[i]

    # # angles conversion
    for j, e in enumerate(rotations):
        for i in range(keyframes_count):
            euler = Quaternion(e[i]).to_euler("ZXY")
            angles = [math.degrees(e) for e in euler]
            rotations[j][i][0] = -angles[0]
            rotations[j][i][1] = angles[1]
            rotations[j][i][2] = -angles[2]

    # Write xml
    for datapath in range(keyframes_count):
        wadkf = ET.SubElement(keyframes_node, 'WadKeyFrame')

        bbox = ET.SubElement(wadkf, 'BoundingBox')

        minimum = ET.SubElement(bbox, 'Minimum')
        ET.SubElement(minimum, 'X').text = "0"
        ET.SubElement(minimum, 'Y').text = "0"
        ET.SubElement(minimum, 'Z').text = "0"

        maximum = ET.SubElement(bbox, 'Maximum')
        ET.SubElement(maximum, 'X').text = "0"
        ET.SubElement(maximum, 'Y').text = "0"
        ET.SubElement(maximum, 'Z').text = "0"

        offset = ET.SubElement(wadkf, 'Offset')
        x = ET.SubElement(offset, 'X')
        x.text = '%f' % locations[datapath][0]
        y = ET.SubElement(offset, 'Y')
        y.text = '%f' % -locations[datapath][1]
        z = ET.SubElement(offset, 'Z')
        z.text = '%f' % locations[datapath][2]

        angles = ET.SubElement(wadkf, 'Angles')

        for i in range(n):
            rot = ET.SubElement(angles, 'WadKeyFrameRotation')
            rot = ET.SubElement(rot, 'Rotations')
            x = ET.SubElement(rot, 'X')
            x.text = '%.6f' % rotations[i][datapath][0]
            y = ET.SubElement(rot, 'Y')
            y.text = '%.6f' % rotations[i][datapath][1]
            z = ET.SubElement(rot, 'Z')
            z.text = '%.6f' % rotations[i][datapath][2]

    tree.write(template_anim)


def export(context, filepath, action):
    export_anim(filepath, action)
    return {'FINISHED'}


class ExportAnim(Operator, ExportHelper):
    bl_idname = "wadblender.export_anim"
    bl_label = "Export Wad Tool Animation"

    filename_ext = ".anim"

    filter_glob: StringProperty(
        default="*.anim",
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
    self.layout.operator("wadblender.export_anim", text="TRLE Animation (.anim)")


def register():
    bpy.utils.register_class(ExportAnim)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ExportAnim)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.export_anim.data('INVOKE_DEFAULT')
