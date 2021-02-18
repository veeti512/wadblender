import bpy
 
class KeeMapToolsPanel(bpy.types.Panel):
    """Creates a Panel for the KeeMap animation retargetting rig addon"""
    bl_label = "KeeMap"
    bl_idname = "KEEMAP_PT_MAINPANEL"
    bl_space_type = "VIEW_3D"   
    bl_region_type = "UI"    
    bl_category = 'KeeMapRig'
    bl_context = "posemode"   

    @classmethod
    def poll(self,context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        scene = context.scene	
        row = layout.row() 
        row.label(text="KeeMap Script written by Nick Keeline")
        row = layout.row() 
        row.label(text="Subscribe to Checkered Bug on Youtube")
            
                            
class KeemapPanelOne(KeeMapToolsPanel, bpy.types.Panel):
    bl_idname = "KEEMAP_PT_TRANSFERSETTINGS"
    bl_label = "Transfer Settings"

    def draw(self, context):
        layout = self.layout
        KeeMap = bpy.context.scene.keemap_settings 
            
        #layout.label(text="Transfer Settings")
        layout.prop(KeeMap, "start_frame_to_apply")
        layout.prop(KeeMap, "number_of_frames_to_apply")
        layout.prop(KeeMap, "keyframe_every_n_frames")
        row = layout.row(align=True)
        row.prop(KeeMap, "source_rig_name")
        row.operator("wm.get_arm_name", text='', icon='EYEDROPPER').source = True
        row = layout.row(align=True)
        row.prop(KeeMap, "destination_rig_name")
        row.operator("wm.get_arm_name", text='', icon='EYEDROPPER').source = False
        layout.prop(KeeMap, "bone_mapping_file")
    
        row = layout.row()
        row.operator("wm.keemap_read_file")
        row.operator("wm.keemap_save_file")
        layout.operator("wm.perform_animation_transfer") 
          
class KeemapPanelTwo(KeeMapToolsPanel, bpy.types.Panel):
    bl_idname = "KEEMAP_PT_BONEMAPPING"
    bl_label = "Bone Mapping"

    def draw(self, context):
        layout = self.layout    
        scene = context.scene	
        KeeMap = bpy.context.scene.keemap_settings            
        row = layout.row()
        row.template_list("KEEMAP_BONE_UL_List", "The_Keemap_List", scene, "keemap_bone_mapping_list", scene,"keemap_bone_mapping_list_index")#, type='COMPACT')#, "index")
        row = layout.row() 
        row.operator('keemap_bone_mapping_list.new_item', text='NEW') 
        row.operator('keemap_bone_mapping_list.delete_item', text='REMOVE') 
        row.operator('keemap_bone_mapping_list.move_item', text='UP').direction = 'UP' 
        row.operator('keemap_bone_mapping_list.move_item', text='DOWN').direction = 'DOWN'
        row = layout.row() 
        row.label(text="List MUST be ordered Parent->Child")
        
        if scene.keemap_bone_mapping_list_index >= 0 and scene.keemap_bone_mapping_list: 
            item = scene.keemap_bone_mapping_list[scene.keemap_bone_mapping_list_index] 
            layout = self.layout    
            box = layout.box()
            box.prop(item, "name") 
            box.prop(item, "SourceBoneName") 
            box.prop(item, "DestinationBoneName")
            box.operator('wm.get_source_bone_name', text='GET NAME') 
            box.operator('wm.bone_selected', text='SELECT') 
            box.prop(item, "keyframe_this_bone")    
            row = layout.row() 
            row.prop(item, "set_bone_rotation")
            if item.set_bone_rotation:
                box = layout.box()
                box.prop(item, "bone_rotation_application_axis")
                box.prop(item, "bone_transpose_axis")
                box.prop(item, "CorrectionFactor")   
                box.operator('wm.get_bone_rotation_correction', text='CALC CORRECTiON') 
                row = box.row(align=True)
                row.label(text="Invert")
                row.prop(item, "invert_x_rot", text='X')
                row.prop(item, "invert_y_rot", text='Y')
                row.prop(item, "invert_z_rot", text='Z')
#                if not item.has_twist_bone: 
#                    box.operator('wm.get_bone_rotation_correction', text='CALC CORRECTiON') 
#                box.prop(item, "has_twist_bone")
#                if item.has_twist_bone:
#                    box.prop(item, "TwistBoneName")            
            row = layout.row() 
            row.prop(item, "set_bone_position")
            if item.set_bone_position:
                box = layout.box()
                box.prop(item, "position_correction_factor")
                #box.prop(item, "position_gain")

                box.prop(item, "position_gain_vec", text='Position Gain')

                row = box.row()
                row.label(text="Swap")
                row.prop(item, "swap_xy", text='XY')
                row.prop(item, "swap_xz", text='XZ')
                row.prop(item, "swap_yz", text='YZ')
            row = layout.row() 
            row.operator('wm.test_set_rotation_of_bone', text='TEST').index2pose = -1
            row.operator('wm.test_all_bones', text='TEST ALL').keyframe = KeeMap.keyframe_test
            layout.prop(KeeMap, "keyframe_test")

def register():
    bpy.utils.register_class(KeemapPanelOne)
    bpy.utils.register_class(KeemapPanelTwo)
    bpy.utils.register_class(KeeMapToolsPanel)


def unregister():
    bpy.utils.unregister_class(KeeMapToolsPanel)
    bpy.utils.unregister_class(KeemapPanelOne)
    bpy.utils.unregister_class(KeemapPanelTwo)