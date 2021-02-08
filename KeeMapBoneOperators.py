import bpy
import math
import json
from os import path
import mathutils


def Update():
    #bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
     
    #bpy.context.view_layer.update()
    #bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
    
def SetBonePosition(SourceArmature, SourceBoneName, DestinationArmature, DestinationBoneName, DestinationTwistBoneName, WeShouldKeyframe, CorrectionX, CorrectionY, CorrectionZ, Gain, swapxy, swapxz, swapyz, gx, gy, gz):
    destination_bone =  DestinationArmature.pose.bones[DestinationBoneName]
    sourceBone = SourceArmature.pose.bones[SourceBoneName]
    
    WsPosition = sourceBone.matrix.translation
    matrix_final = SourceArmature.matrix_world @ sourceBone.matrix
    destination_bone.matrix.translation = matrix_final.translation
    destination_bone.location.x = (destination_bone.location.x + CorrectionX)*gx
    destination_bone.location.y = (destination_bone.location.y + CorrectionY)*gy
    destination_bone.location.z = (destination_bone.location.z + CorrectionZ)*gz

    if swapxy:
        destination_bone.location.x, destination_bone.location.y = destination_bone.location.y, destination_bone.location.x
    
    if swapxz:
        destination_bone.location.x, destination_bone.location.z = destination_bone.location.z, destination_bone.location.x
    
    if swapyz:
        destination_bone.location.y, destination_bone.location.z = destination_bone.location.z, destination_bone.location.y
    
    #destination_bone.location = sourceBone.location
    Update()
    if (WeShouldKeyframe):
        currentFrame = bpy.context.scene.frame_current
        destination_bone.keyframe_insert(data_path='location',frame=currentFrame)

def GetBoneWSQuat(Bone, Arm):
    source_arm_matrix = Arm.matrix_world
    source_bone_matrix = Bone.matrix
    
    #get the source bones rotation in world space.
    source_bone_world_matrix = source_arm_matrix @ source_bone_matrix
    
    return source_bone_world_matrix.to_quaternion()
        
def SetBoneRotation(SourceArmature, SourceBoneName, DestinationArmature, DestinationBoneName, DestinationTwistBoneName, CorrectionQuat, WeShouldKeyframe, hastwistbone, xferAxis, Transpose, invert_x_rot,invert_y_rot,invert_z_rot):

    #Get the rotation of the bone in edit mode
#    SourceBoneEdit = SourceArmature.data.bones[SourceBoneName]
#    SourceBoneEditRotation = SourceBoneEdit.matrix_local.to_quaternion()
    
    #Get the rotation of the bone in edit mode
#    DestinationBoneEdit = DestinationArmature.data.bones[DestinationBoneName]
#    DestinationBoneEditRotation = DestinationBoneEdit.matrix_local.to_quaternion()
#    
#    DeltaSourceEditBoneandDestEditBone = DestinationBoneEditRotation.rotation_difference(SourceBoneEditRotation)
#    DeltaDestinationEditBoneandSourceEdit = SourceBoneEditRotation.rotation_difference(DestinationBoneEditRotation)
    
    #rotate the edit rotation quat first to armature rotation
    #ArmatureSpaceBoneEditPosition = RigArmature.rotation_quaternion * BoneEditRotation
    if(DestinationTwistBoneName == "" and hastwistbone):
        self.report({'ERROR'}, "You checked Twist Bone, but no name of bone entered!")
        hastwistbone = False
    elif hastwistbone:  
        TwistBone = DestinationArmature.pose.bones[DestinationTwistBoneName]
    destination_bone =  DestinationArmature.pose.bones[DestinationBoneName]
    sourceBone = SourceArmature.pose.bones[SourceBoneName]
    
    #Set Bone Position now that we've calculated it.
    destination_bone.rotation_mode = 'QUATERNION'
     
     #################################################
     ################## Get Source WS Quat ###########
     #################################################
    source_arm_matrix = SourceArmature.matrix_world
    source_bone_matrix = sourceBone.matrix
    
    #get the source bones rotation in world space.
    source_bone_world_matrix = source_arm_matrix @ source_bone_matrix
    
    SourceBoneRotWS = source_bone_world_matrix.to_quaternion()
    #print('Source Rotation WS Before:')
    #print(SourceBoneRotWS.to_euler())
     
     #################################################
     ################## Get Dest edit WS Quat ###########
     #################################################
    dest_arm_matrix = DestinationArmature.matrix_world
    dest_bone_matrix = destination_bone.matrix
    
    #get the DESTINATION bones rotation in world space.
    dest_bone_world_matrix = dest_arm_matrix @ dest_bone_matrix
    
    DestBoneRotWS = dest_bone_world_matrix.to_quaternion()
    #print('Destination Rotation WS Before:')
    #print(DestBoneRotWS.to_euler())
    
    DifferenceBetweenSourceWSandDestWS = DestBoneRotWS.rotation_difference(SourceBoneRotWS)
    #print('Difference Rotation')
    FinalQuat = destination_bone.rotation_quaternion.copy() @ DifferenceBetweenSourceWSandDestWS @ CorrectionQuat

    # destination_bone.rotation_mode = 'XYZ'
    FinalEul = FinalQuat.to_euler(Transpose) if Transpose != 'NONE' else FinalQuat.to_euler()
    # if Transpose == 'ZYX':
    #     destination_bone.rotation_euler.x = FinalEul.z
    #     destination_bone.rotation_euler.y = FinalEul.y
    #     destination_bone.rotation_euler.z = FinalEul.x
    # elif Transpose == 'ZXY':
    #     destination_bone.rotation_euler.x = FinalEul.z
    #     destination_bone.rotation_euler.y = FinalEul.x
    #     destination_bone.rotation_euler.z = FinalEul.y
    # elif Transpose == 'XZY':
    #     destination_bone.rotation_euler.x = FinalEul.x
    #     destination_bone.rotation_euler.y = FinalEul.z
    #     destination_bone.rotation_euler.z = FinalEul.y
    # elif Transpose == 'YZX':
    #     destination_bone.rotation_euler.x = FinalEul.y
    #     destination_bone.rotation_euler.y = FinalEul.z
    #     destination_bone.rotation_euler.z = FinalEul.x
    # elif Transpose == 'YXZ':
    #     destination_bone.rotation_euler.x = FinalEul.y
    #     destination_bone.rotation_euler.y = FinalEul.x
    #     destination_bone.rotation_euler.z = FinalEul.z
    # else:
    #     destination_bone.rotation_euler = FinalEul


    if xferAxis == 'X':
        FinalEul.y = 0
        FinalEul.z = 0
    elif xferAxis == 'Y':
        FinalEul.x = 0
        FinalEul.z = 0
    elif xferAxis == 'Z':
        FinalEul.x = 0
        FinalEul.y = 0
    elif xferAxis == 'XY':
        FinalEul.z = 0
    elif xferAxis == 'XZ':
        FinalEul.y = 0
    elif xferAxis == 'YZ':
        FinalEul.x = 0

    if invert_x_rot:
        FinalEul.x *= -1
    
    if invert_y_rot:
        FinalEul.y *= -1

    if invert_z_rot:
        FinalEul.z *= -1

    FinalQuat = FinalEul.to_quaternion()
    destination_bone.rotation_quaternion = FinalQuat
        
    Update()
    
    if (hastwistbone):
        #TwistBone.rotation_mode = 'XYZ'
        yrotation = FinalEul.y
        FinalEul.y = 0
        FinalQuat = FinalEul.to_quaternion()
        destination_bone.rotation_quaternion = FinalQuat
        #destination_bone.rotation_euler.y = 0
        angle = TwistBone.rotation_quaternion
        angle = angle.to_euler('XYZ')
        angle.y = yrotation
        TwistBone.rotation_quaternion = angle.to_quaternion()
        #print('Setting Twist Bone: ' + yrotation)
        #TwistBone.rotation_mode = 'QUATERNION'
        #destination_bone.rotation_mode = 'QUATERNION'
        
    Update()
    
    if (WeShouldKeyframe):
        currentFrame = bpy.context.scene.frame_current
        #destination_bone.rotation_mode = 'XYZ'
        destination_bone.keyframe_insert(data_path='rotation_quaternion',frame=currentFrame)
        #print('keyframed' + str(currentFrame))
        if (hastwistbone):
            #TwistBone.rotation_mode = 'XYZ'
            TwistBone.keyframe_insert(data_path='rotation_quaternion',frame=currentFrame)

def GetBoneEditRotationWorldSpace(arm, bonename):
    BoneEdit = arm.data.bones[bonename]
    BoneEditRotation = BoneEdit.matrix_local.to_quaternion()
    BoneEditWS = arm.rotation_quaternion*BoneEditRotation
    return BoneEditWS
	
####################################################################################
####################################################################################
####################################################################################
# Code for iteration through frames and applying positions and angles to rig
####################################################################################
####################################################################################
####################################################################################

class PerformAnimationTransfer(bpy.types.Operator):
    bl_idname = "wm.perform_animation_transfer"
    bl_label = "Transfer Animation from Source to Destination"

    def execute(self, context):
        scene = bpy.context.scene
        KeeMap = bpy.context.scene.keemap_settings 
        bone_mapping_list = context.scene.keemap_bone_mapping_list
        
        SourceArmName = KeeMap.source_rig_name
        DestArmName = KeeMap.destination_rig_name
        KeyFrame_Every_Nth_Frame = KeeMap.keyframe_every_n_frames
        NumberOfFramesToTransfer = KeeMap.number_of_frames_to_apply
        #StartFrame = scene.frame_current
        StartFrame = KeeMap.start_frame_to_apply


        print('')
        print('Start of Everything')
        print('')
        #SourcArm = bpy.context.selected_objects[SourcArmName]
        #DestArm  = bpy.context.selected_objects[DestArmName]
                    
        if SourceArmName == "":
            self.report({'ERROR'}, "Must Have a Source Armature Name Entered")
        elif DestArmName == "":
            self.report({'ERROR'}, "Must Have a Destination Armature Name Entered")
        else:
            SourceArm = bpy.data.objects[SourceArmName]
            DestArm  = bpy.data.objects[DestArmName]
            
            i=0
            while (i < NumberOfFramesToTransfer):
                #scene.frame_current = StartFrame + i
                bpy.context.scene.frame_set(StartFrame + i)
                Update()
                
                print('')
                CurrentFrame = scene.frame_current
                EndFrame =  StartFrame + NumberOfFramesToTransfer
                PercentComplete = ((CurrentFrame - StartFrame)/(EndFrame - StartFrame))*100
                print('Working On Frame: ' + str(scene.frame_current) + ' of ' + str(EndFrame) + ' ' + "{:.1f}".format(PercentComplete) + '%')
                print('')

                bpy.ops.wm.test_all_bones(keyframe = True)
                i = i + KeyFrame_Every_Nth_Frame

        return{'FINISHED'}
    
class KEEMAP_TestSetRotationOfBone(bpy.types.Operator): 
    """Maps a Single Bone on the Current Frame to Test Mapping""" 
    bl_idname = "wm.test_set_rotation_of_bone" 
    bl_label = "Test Bone Re-Targetting" 
    index2pose: bpy.props.IntProperty() 
    keyframe: bpy.props.BoolProperty(default = False) 
    
    def execute(self, context): 
        scene = bpy.context.scene
        if(self.index2pose == -1):
            index = scene.keemap_bone_mapping_list_index 
        else:
            index = self.index2pose
        KeeMap = bpy.context.scene.keemap_settings 
        bone_mapping_list = context.scene.keemap_bone_mapping_list
        
        #if the box is checked we're going to keyframe no matter what:
        if KeeMap.keyframe_test:
            self.keyframe = True
            
        #print('')
        #print('Test Pressed:')
        SourceArmName = KeeMap.source_rig_name
        DestArmName = KeeMap.destination_rig_name
                    
        if SourceArmName == "":
            self.report({'ERROR'}, "Must Have a Source Armature Name Entered")
        elif DestArmName == "":
            self.report({'ERROR'}, "Must Have a Destination Armature Name Entered")
        else:
            SourceArm = bpy.data.objects[SourceArmName]
            DestArm  = bpy.data.objects[DestArmName]
            
            SourceBoneName = bone_mapping_list[index].SourceBoneName
            DestBoneName = bone_mapping_list[index].DestinationBoneName
            
            xferAxis = bone_mapping_list[index].bone_rotation_application_axis
            xPose = bone_mapping_list[index].bone_transpose_axis
            
            if SourceBoneName == "":
                self.report({'ERROR'}, "Must Have a Source Bone Name Entered")
            elif DestBoneName == "":
                self.report({'ERROR'}, "Must Have a Destination Bone Name Entered")
            else:
                HasTwist = bone_mapping_list[index].has_twist_bone
                TwistBoneName = bone_mapping_list[index].TwistBoneName
                CorrectionVectorX = bone_mapping_list[index].CorrectionFactor.x
                #print(math.degrees(CorrectionVectorX))
                CorrectionVectorY = bone_mapping_list[index].CorrectionFactor.y
                #print(math.degrees(CorrectionVectorY))
                CorrectionVectorZ = bone_mapping_list[index].CorrectionFactor.z
                #print(math.degrees(CorrectionVectorZ))
                corrEul = mathutils.Euler((CorrectionVectorX, CorrectionVectorY, CorrectionVectorZ), 'XYZ')
                #print('correction Eul in:')
                #print(corrEul)
                CorrQuat = corrEul.to_quaternion()
                #print('correction in:')
                #print(CorrQuat.to_euler())
                invert_x_rot = bone_mapping_list[index].invert_x_rot
                invert_y_rot = bone_mapping_list[index].invert_y_rot
                invert_z_rot = bone_mapping_list[index].invert_z_rot
                if bone_mapping_list[index].set_bone_rotation:
                    SetBoneRotation(SourceArm, SourceBoneName, DestArm, DestBoneName, TwistBoneName, CorrQuat, self.keyframe, HasTwist, xferAxis,xPose,invert_x_rot,invert_y_rot,invert_z_rot)
                if bone_mapping_list[index].set_bone_position:
                    corr = bone_mapping_list[index].position_correction_factor
                    gain = bone_mapping_list[index].position_gain
                    swapxy = bone_mapping_list[index].swap_xy
                    swapxz = bone_mapping_list[index].swap_xz
                    swapyz = bone_mapping_list[index].swap_yz
                    gx = bone_mapping_list[index].position_gain_vec.x
                    gy = bone_mapping_list[index].position_gain_vec.y
                    gz = bone_mapping_list[index].position_gain_vec.z
                    
                    SetBonePosition(SourceArm, SourceBoneName, DestArm, DestBoneName, TwistBoneName, self.keyframe,corr.x,corr.y,corr.z,gain,swapxy, swapxz, swapyz, gx, gy, gz)
        return{'FINISHED'}
    
class KEEMAP_BoneSelectedOperator(bpy.types.Operator):
    bl_idname = "wm.bone_selected"
    bl_label = "Operator to Change Selection based on selected bone"

    @classmethod
    def poll(cls, context):
        return len(context.selected_pose_bones) > 0
    
    def execute(self, context):
        print('Checking')

        bone_mapping_list = context.scene.keemap_bone_mapping_list
        index = context.scene.keemap_bone_mapping_list_index 
        KeeMap = bpy.context.scene.keemap_settings 
        
        DestArmName = KeeMap.destination_rig_name
        if DestArmName != '':
            DestArm  = bpy.data.objects[DestArmName]
            if len(context.selected_pose_bones) > 0:
                bonename = context.selected_pose_bones[0].name
                i = 0
                for bone_settings in bone_mapping_list:
                    if bone_settings.DestinationBoneName == bonename:
                        context.scene.keemap_bone_mapping_list_index = i
                    i = i+1
        return {'FINISHED'}    
    
class KEEMAP_TestAllBones(bpy.types.Operator): 
    """Test All Bones to set there position""" 
    bl_idname = "wm.test_all_bones" 
    bl_label = "Test Set All Bone's Position"
    keyframe: bpy.props.BoolProperty(default = False) 

    def execute(self, context): 

        bone_mapping_list = context.scene.keemap_bone_mapping_list
        index = context.scene.keemap_bone_mapping_list_index 
        # CODE FOR SETTING BONE POSITIONS:
        i = 0
        for bone_settings in bone_mapping_list:
            index = i
            print(bone_settings.name)
            bpy.ops.wm.test_set_rotation_of_bone(index2pose = index,keyframe = self.keyframe)
            i = i+1
        return{'FINISHED'}

class KEEMAP_GetArmatureName(bpy.types.Operator):
    """If an armature is selected, get the name and populate"""
    bl_idname = "wm.get_arm_name"
    bl_label = "Get Armature Name"
    bl_options = {"REGISTER", "INTERNAL"}

    source : bpy.props.BoolProperty()

    @classmethod
    def poll(self, context):
        return context.object is not None and context.object.type == 'ARMATURE'

    def execute(self, context):
        KeeMap = bpy.context.scene.keemap_settings
        if self.source:
            KeeMap.source_rig_name = context.object.name
        else:
            KeeMap.destination_rig_name = context.object.name
        return{'FINISHED'}

class KEEMAP_GetSourceBoneName(bpy.types.Operator): 
    """If a bone is selected, get the name and popultate""" 
    bl_idname = "wm.get_source_bone_name" 
    bl_label = "Get Source Bone Name" 

    def execute(self, context): 
        scene = bpy.context.scene
        index = scene.keemap_bone_mapping_list_index 
        KeeMap = bpy.context.scene.keemap_settings 
        bone_mapping_list = context.scene.keemap_bone_mapping_list
        if len(context.selected_objects) == 1:
            rigname = context.selected_objects[0].name
            bonename = context.selected_pose_bones[0].name
        elif len(context.selected_objects) == 2:
            bonename = context.selected_pose_bones[0].name
            rig1 = context.selected_objects[0]
            if rig1.pose.bones.find(bonename) == -1:
                rigname = context.selected_objects[1].name
            else:
                rigname = context.selected_objects[0].name
        if len(context.selected_pose_bones) == 1:
            if rigname == KeeMap.source_rig_name:
                bone_mapping_list[index].SourceBoneName = bonename
            if rigname == KeeMap.destination_rig_name:
                bone_mapping_list[index].DestinationBoneName = bonename
            if bone_mapping_list[index].name == '' and rigname == KeeMap.source_rig_name:
                bone_mapping_list[index].name = bonename
        return{'FINISHED'}

class KEEMAP_AutoGetBoneCorrection(bpy.types.Operator): 
    """Auto Calculate the Bones Correction Number from calculated to current position.""" 
    bl_idname = "wm.get_bone_rotation_correction" 
    bl_label = "Auto Calc Correction" 

    def execute(self, context): 
        scene = bpy.context.scene
        index = scene.keemap_bone_mapping_list_index 
        KeeMap = bpy.context.scene.keemap_settings 
        bone_mapping_list = context.scene.keemap_bone_mapping_list
        
        print('')
        print('Calc Pressed:')
        SourceArmName = KeeMap.source_rig_name
        DestArmName = KeeMap.destination_rig_name
        
        if SourceArmName == "":
            self.report({'ERROR'}, "Must Have a Source Armature Name Entered")
        elif DestArmName == "":
            self.report({'ERROR'}, "Must Have a Destination Armature Name Entered")
        else:
            SourceArm = bpy.data.objects[SourceArmName]
            DestArm  = bpy.data.objects[DestArmName]
            
            SourceBoneName = bone_mapping_list[index].SourceBoneName
            DestBoneName = bone_mapping_list[index].DestinationBoneName
            
            xferAxis = bone_mapping_list[index].bone_rotation_application_axis
            xPose = bone_mapping_list[index].bone_transpose_axis
            
            if SourceBoneName == "":
                self.report({'ERROR'}, "Must Have a Source Bone Name Entered")
            elif DestBoneName == "":
                self.report({'ERROR'}, "Must Have a Destination Bone Name Entered")
            else:
                destBone = DestArm.pose.bones[DestBoneName]
                sourceBone = SourceArm.pose.bones[SourceBoneName]
                # destBoneMode = 'XYZ'
                # destBone.rotation_mode = destBoneMode
                
                StartingDestBoneWSQuat = GetBoneWSQuat(destBone, DestArm)
                print("Destination Bone Starting WS")
                print(StartingDestBoneWSQuat.to_euler())
                destBoneStartPosition = destBone.rotation_quaternion.copy()
                #print(destBoneStartPosition)
                
                HasTwist = bone_mapping_list[index].has_twist_bone
                if HasTwist:
                    TwistBoneName = bone_mapping_list[index].TwistBoneName
                    TwistBone = DestArm.pose.bones[TwistBoneName]
                    y = TwistBone.rotation_quaternion.to_euler('XYZ').y
                    #y =  TwistBone.rotation_euler.y
                else:
                    TwistBoneName = ''
                    
                CorrQuat =  mathutils.Quaternion((1,0,0,0))
                invert_x_rot = bone_mapping_list[index].invert_x_rot
                invert_y_rot = bone_mapping_list[index].invert_y_rot
                invert_z_rot = bone_mapping_list[index].invert_z_rot
                SetBoneRotation(SourceArm, SourceBoneName, DestArm, DestBoneName, TwistBoneName, CorrQuat, False, HasTwist, xferAxis,xPose,invert_x_rot,invert_y_rot,invert_z_rot)
                Update()
                
                ModifiedDestBoneWSQuat = GetBoneWSQuat(destBone, DestArm)
                print("Destination Bone After Modifying WS")
                print(ModifiedDestBoneWSQuat.to_euler())
                
                q = ModifiedDestBoneWSQuat.rotation_difference(StartingDestBoneWSQuat)
                print('Difference between before and After modification')
                print(q.to_euler())
                corrEuler = q.to_euler()
                print(math.degrees(corrEuler.x))
                print(math.degrees(corrEuler.y))
                print(math.degrees(corrEuler.z))
                print(corrEuler.to_quaternion())
                bone_mapping_list[index].CorrectionFactor.x = corrEuler.x
                bone_mapping_list[index].CorrectionFactor.y = corrEuler.y
                bone_mapping_list[index].CorrectionFactor.z = corrEuler.z
                
                destBone.rotation_quaternion = destBoneStartPosition
                if HasTwist:
                    angle = TwistBone.rotation_quaternion.to_euler('XYZ')
                    angle.y = y
                    angle = angle.to_quaternion()
                    TwistBone.rotation_quaternion = angle

                    angle = destBone.rotation_quaternion.to_euler('XYZ')
                    angle.y = 0
                    angle = angle.to_quaternion()
                    destBone.rotation_quaternion = angle
                print(destBoneStartPosition)
                
        return{'FINISHED'}


def register():
    bpy.utils.register_class(PerformAnimationTransfer)
    bpy.utils.register_class(KEEMAP_GetArmatureName)
    bpy.utils.register_class(KEEMAP_GetSourceBoneName)
    bpy.utils.register_class(KEEMAP_TestSetRotationOfBone)
    bpy.utils.register_class(KEEMAP_AutoGetBoneCorrection)
    bpy.utils.register_class(KEEMAP_TestAllBones)
    bpy.utils.register_class(KEEMAP_BoneSelectedOperator)


def unregister():
    bpy.utils.unregister_class(PerformAnimationTransfer)
    bpy.utils.unregister_class(KEEMAP_GetArmatureName)
    bpy.utils.unregister_class(KEEMAP_GetSourceBoneName)
    bpy.utils.unregister_class(KEEMAP_TestSetRotationOfBone)
    bpy.utils.unregister_class(KEEMAP_AutoGetBoneCorrection)
    bpy.utils.unregister_class(KEEMAP_TestAllBones)
    bpy.utils.unregister_class(KEEMAP_BoneSelectedOperator)
