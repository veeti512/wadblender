import bpy

def bake(obj):
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.duplicate()
    obj.select_set(False)
    obj2 = bpy.context.object
    obj2.name = obj.name + "_WAD_READY"
    bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.uv.smart_project(stretch_to_bounds=True)
    bpy.ops.uv.lightmap_pack(PREF_IMG_PX_SIZE=256, PREF_BOX_DIV=48,PREF_MARGIN_DIV=0.25)

    image_name = obj.name + '_BakedTexture'
    img = bpy.data.images.new(image_name,256,256)
    mat = bpy.data.materials.new(name=obj.name + '_material')
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
    texImage.image = img
    mat.node_tree.nodes["Image Texture"].interpolation = 'Closest'
    bpy.ops.object.mode_set(mode='OBJECT')
    obj2.data.materials.clear()
    obj2.data.materials.append(mat)
    obj2.active_material_index = 0
    bpy.ops.object.material_slot_assign()
    old_engine = bpy.context.scene.render.engine
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.render.bake.use_pass_direct = False
    bpy.context.scene.render.bake.use_pass_indirect = False
    bpy.context.scene.render.bake.max_ray_distance = 1

    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj2
    bpy.ops.object.bake(type='DIFFUSE', use_selected_to_active=True)
    # for mat in obj.data.materials:
    bpy.context.scene.render.engine = old_engine

    #mat.use_nodes = True #Here it is assumed that the materials have been created with nodes, otherwise it would not be possible to assign a node for the Bake, so this step is a bit useless
    nodes = mat.node_tree.nodes
    texture_node =nodes.new('ShaderNodeTexImage')
    texture_node.interpolation = 'Closest'
    #     texture_node.name = 'Bake_node'
    #     texture_node.select = True
    #     nodes.active = texture_node
    texture_node.image = bpy.data.images[image_name] #Assign the image to the node
    mat.node_tree.links.new(bsdf.inputs['Base Color'], texture_node.outputs['Color'])


    # bpy.context.view_layer.objects.active = obj
    # bpy.ops.object.bake(type='DIFFUSE', save_mode='EXTERNAL')
    # img.save_render(filepath='baked.png')


if __name__ == '__main__':
    bake()