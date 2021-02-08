import bpy
import json   

class KEEMAP_BONE_UL_List(bpy.types.UIList): 
    """Demo UIList.""" 
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        # We could write some code to decide which icon to use here... 
        custom_icon = 'BONE_DATA' 
        
        # Make sure your code supports all 3 layout types if 
        if self.layout_type in {'DEFAULT', 'COMPACT'}: 
            layout.label(text=item.name, icon = custom_icon) 
        elif self.layout_type in {'GRID'}: 
            layout.alignment = 'CENTER' 
            layout.label(text="", icon = custom_icon) 
            
       
class KEEMAP_LIST_OT_NewItem(bpy.types.Operator): 
    """Add a new item to the list.""" 
    bl_idname = "keemap_bone_mapping_list.new_item" 
    bl_label = "Add a new item" 

    def execute(self, context): 
        index = context.scene.keemap_bone_mapping_list_index 
        context.scene.keemap_bone_mapping_list.add() 
        index = len(context.scene.keemap_bone_mapping_list)
        return{'FINISHED'}       
    
class KEEMAP_LIST_OT_DeleteItem(bpy.types.Operator): 
    """Delete the selected item from the list.""" 
    bl_idname = "keemap_bone_mapping_list.delete_item" 
    bl_label = "Deletes an item" 
    
    @classmethod 
    def poll(cls, context): 
        return context.scene.keemap_bone_mapping_list 
    
    def execute(self, context): 
        bone_mapping_list = context.scene.keemap_bone_mapping_list
        index = context.scene.keemap_bone_mapping_list_index 
        bone_mapping_list.remove(index) 
        index = min(max(0, index - 1), len(bone_mapping_list) - 1) 
        return{'FINISHED'}

class KEEMAP_LIST_OT_MoveItem(bpy.types.Operator): 
    """Move an item in the list.""" 
    bl_idname = "keemap_bone_mapping_list.move_item" 
    bl_label = "Move an item in the list" 
    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""), ('DOWN', 'Down', ""),)) 

    @classmethod 
    def poll(cls, context): 
        return context.scene.keemap_bone_mapping_list 
    
    def move_index(self): 
        """ Move index of an item render queue while clamping it. """ 
        scene = bpy.context.scene	
        index = scene.keemap_bone_mapping_list_index 
        list_length = len(bpy.context.scene.keemap_bone_mapping_list) - 1 # (index starts at 0) 
        new_index = index + (-1 if self.direction == 'UP' else 1) 
        index = max(0, min(new_index, list_length)) 
    
    def execute(self, context): 
        bone_mapping_list = context.scene.keemap_bone_mapping_list 
        scene = context.scene	
        index = scene.keemap_bone_mapping_list_index 
        neighbor = index + (-1 if self.direction == 'UP' else 1) 
        bone_mapping_list.move(neighbor, index) 
        self.move_index() 
        return{'FINISHED'}
    
class KEEMAP_LIST_OT_ReadInFile(bpy.types.Operator): 
    """Read in Bone Mapping File""" 
    bl_idname = "wm.keemap_read_file" 
    bl_label = "Read In Bone Mapping File" 

    def execute(self, context): 
        
        context.scene.keemap_bone_mapping_list_index = 0    
        bone_list = context.scene.keemap_bone_mapping_list
        bone_list.clear()
        
        KeeMap = bpy.context.scene.keemap_settings 
        filepath = bpy.path.abspath(KeeMap.bone_mapping_file)
        file = open(filepath, 'r')

        data = json.load(file)
        
        if "start_frame_to_apply" in data:
            KeeMap.start_frame_to_apply = data['start_frame_to_apply']
        if "number_of_frames_to_apply" in data:
            KeeMap.number_of_frames_to_apply = data['number_of_frames_to_apply']
        if "keyframe_every_n_frames" in data:
            KeeMap.keyframe_every_n_frames = data['keyframe_every_n_frames']
        if "source_rig_name" in data:
            KeeMap.source_rig_name = data['source_rig_name']
        if "destination_rig_name" in data:
            KeeMap.destination_rig_name = data['destination_rig_name']
        if "bone_mapping_file" in data:
            KeeMap.bone_mapping_file = data['bone_mapping_file']
        i = 0
        for p in data['bones']:
            bone_list.add()
            bone = bone_list[i]
            
            if "name" in p:
                bone.name = p['name']
            if "label" in p:
                bone.label = p['label']
            if "description" in p:
                bone.description = p['description']
            if "SourceBoneName" in p:
                bone.SourceBoneName = p['SourceBoneName']
            if "DestinationBoneName" in p:
                bone.DestinationBoneName = p['DestinationBoneName']
            if "keyframe_this_bone" in p:
                bone.keyframe_this_bone = p['keyframe_this_bone']
            if "CorrectionFactorX" in p:
                bone.CorrectionFactor.x = p['CorrectionFactorX']
            if "CorrectionFactorY" in p:
                bone.CorrectionFactor.y = p['CorrectionFactorY']
            if "CorrectionFactorZ" in p:
                bone.CorrectionFactor.z = p['CorrectionFactorZ']
            if "has_twist_bone" in p:
                bone.has_twist_bone = p['has_twist_bone']
            if "TwistBoneName" in p:
                bone.TwistBoneName = p['TwistBoneName']
            if "set_bone_position" in p:
                bone.set_bone_position = p['set_bone_position']
            if "set_bone_rotation" in p:
                bone.set_bone_rotation = p['set_bone_rotation']
            if "bone_rotation_application_axis" in p:
                bone.bone_rotation_application_axis = p['bone_rotation_application_axis']
            if "position_correction_factorX" in p:
                bone.position_correction_factor.x = p['position_correction_factorX']
            if "position_correction_factorY" in p:
                bone.position_correction_factor.y = p['position_correction_factorY']
            if "position_correction_factorZ" in p:
                bone.position_correction_factor.z = p['position_correction_factorZ']
            if "position_gain" in p:
                bone.position_gain = p['position_gain']

            if "swap_yz" in p:
                bone.swap_yz = p['swap_yz']
            if "swap_xy" in p:
                bone.swap_xy = p['swap_xy']
            if "swap_xz" in p:
                bone.swap_xz = p['swap_xz']

            if "invert_x_rot" in p:
                bone.invert_x_rot = p['invert_x_rot']
            if "invert_y_rot" in p:
                bone.invert_y_rot = p['invert_y_rot']
            if "invert_z_rot" in p:
                bone.invert_z_rot = p['invert_z_rot']

            if "position_gain_vec_x" in p:
                bone.position_gain_vec.x = p['position_gain_vec_x']
            if "position_gain_vec_y" in p:
                bone.position_gain_vec.y = p['position_gain_vec_y']
            if "position_gain_vec_z" in p:
                bone.position_gain_vec.z = p['position_gain_vec_z']

            i = i + 1
        file.close()
        
        return{'FINISHED'}
     
class KEEMAP_LIST_OT_SaveToFile(bpy.types.Operator): 
    """Save Out Bone Mapping File""" 
    bl_idname = "wm.keemap_save_file" 
    bl_label = "Save Bone Mapping File" 

    def execute(self, context): 
        #context.scene.bone_mapping_list.clear() 
        KeeMap = bpy.context.scene.keemap_settings 
        filepath = bpy.path.abspath(KeeMap.bone_mapping_file)
        file = open(filepath, 'w+')
        
        rootParams = {
        "start_frame_to_apply":KeeMap.start_frame_to_apply,
        "number_of_frames_to_apply":KeeMap.number_of_frames_to_apply,
        "keyframe_every_n_frames":KeeMap.keyframe_every_n_frames,
        "source_rig_name":KeeMap.source_rig_name,
        "destination_rig_name":KeeMap.destination_rig_name,
        "bone_mapping_file":KeeMap.bone_mapping_file
        } 
        bone_list = context.scene.keemap_bone_mapping_list
        jsonbones = {}
        jsonbones['bones'] = []
        for bone in bone_list:
            jsonbones['bones'].append({
                'name': bone.name,
                'label': bone.label,
                'description': bone.description,
                'SourceBoneName': bone.SourceBoneName,
                'DestinationBoneName': bone.DestinationBoneName,
                'keyframe_this_bone': bone.keyframe_this_bone,
                'CorrectionFactorX': bone.CorrectionFactor.x,
                'CorrectionFactorY': bone.CorrectionFactor.y,
                'CorrectionFactorZ': bone.CorrectionFactor.z,
                'has_twist_bone': bone.has_twist_bone,
                'TwistBoneName': bone.TwistBoneName,
                'set_bone_position': bone.set_bone_position,
                'set_bone_rotation': bone.set_bone_rotation,
                'bone_rotation_application_axis': bone.bone_rotation_application_axis,
                'position_correction_factorX': bone.position_correction_factor.x,
                'position_correction_factorY': bone.position_correction_factor.y,
                'position_correction_factorZ': bone.position_correction_factor.z,
                'position_gain': bone.position_gain,
                'swap_yz': bone.swap_yz,
                'swap_xz': bone.swap_xz,
                'swap_xy': bone.swap_xy,
                'invert_x_rot': bone.invert_x_rot,
                'invert_y_rot': bone.invert_y_rot,
                'invert_z_rot': bone.invert_z_rot,
                'position_gain_vec_x': bone.position_gain_vec.x,
                'position_gain_vec_y': bone.position_gain_vec.y,
                'position_gain_vec_z': bone.position_gain_vec.z
            })
        jsonbones.update(rootParams)
        print(jsonbones)
        json.dump(jsonbones, file)  
        file.close()
        return{'FINISHED'} 
    
	
	
def register():
    bpy.utils.register_class(KEEMAP_BONE_UL_List)
    bpy.utils.register_class(KEEMAP_LIST_OT_NewItem)
    bpy.utils.register_class(KEEMAP_LIST_OT_DeleteItem)
    bpy.utils.register_class(KEEMAP_LIST_OT_MoveItem)
    bpy.utils.register_class(KEEMAP_LIST_OT_ReadInFile)
    bpy.utils.register_class(KEEMAP_LIST_OT_SaveToFile)


def unregister():
    bpy.utils.unregister_class(KEEMAP_BONE_UL_List)
    bpy.utils.unregister_class(KEEMAP_LIST_OT_NewItem)
    bpy.utils.unregister_class(KEEMAP_LIST_OT_DeleteItem)
    bpy.utils.unregister_class(KEEMAP_LIST_OT_MoveItem)
    bpy.utils.unregister_class(KEEMAP_LIST_OT_ReadInFile)
    bpy.utils.unregister_class(KEEMAP_LIST_OT_SaveToFile)