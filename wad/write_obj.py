import bpy
import bmesh
from math import floor
from .write import get_textures, verify_vcol_layer


def createShineOpacityMaterials(name, uvmap):
    materials = []
    for i in range(64):
        mat = bpy.data.materials.new(name=name + '_' + str(i))
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
        texImage.image = bpy.data.images.load(uvmap)
        mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])
        mat.node_tree.nodes["Image Texture"].interpolation = 'Closest'
        if i < 32:  # opacity on
            bsdf.inputs[7].default_value = 1.0 - i / 31  # roughness
            bsdf.inputs[18].default_value = 1.0  # alpha
        else:
            bsdf.inputs[7].default_value = 1.0 - (i-32) / 31  # roughness
            bsdf.inputs[18].default_value = 0.0  # alpha

        print(i, bsdf.inputs[7].default_value, bsdf.inputs[18].default_value)
        print(bsdf.inputs[7], bsdf.inputs[18])

        mat.blend_method = 'CLIP'
        materials.append(mat)

    return materials


def write_obj(obj_orig, filepath, context, scale):
    log = []
    # duplicate object
    obj = obj_orig.copy()
    obj.data = obj_orig.data.copy()
    obj.data.materials.clear()
    bpy.context.collection.objects.link(obj)

    # blender normals are opposite to TRLE wrt vertices order
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for face in bm.faces:
        face.normal_flip()

    bm.to_mesh(obj.data)
    bm.from_mesh(obj.data)


    # if there's not opacity nor shine let's save it as it is
    if 'shine' not in obj.data.vertex_colors and 'opacity' not in obj.data.vertex_colors:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.ops.export_scene.obj(filepath=filepath, axis_forward='Z', use_selection=True, keep_vertex_order=True, global_scale=scale)

        bpy.data.objects.remove(obj, do_unlink=True)
        log.append("File written successfully.")

        return {'FINISHED'}, log

    textures = get_textures(obj_orig)

    if len(textures) > 1 :
        log.append('WOnly one texture map supported.')
        log.append('WOperation cancelled.')
        return {'CANCELLED'}, log
    elif len(textures) == 0:
        log.append('WNo texture found.')
        log.append('WOperation cancelled.')
        return {'CANCELLED'}, log

    texture = textures[0]
    texture.filepath_raw = filepath[:-3] + 'png'
    texture.file_format = 'PNG'
    texture.save()

<<<<<<< Updated upstream
    obj.data.materials += createShineOpacityMaterials(obj.name, texture.filepath_raw)
=======
    mats = createShineOpacityMaterials(obj.name, texture.filepath_raw)

    for m in mats:
        obj.data.materials.append(m)
>>>>>>> Stashed changes

    shine_layer = verify_vcol_layer(bm, 'shine', 0)
    opacity_layer = verify_vcol_layer(bm, 'opacity', 1)
    for face in bm.faces:
        shine = 0
        opacity = 0
        for loop in face.loops:
            shine = max(shine, loop[shine_layer][0])
            opacity = max(opacity, loop[opacity_layer][0])

        if opacity < 0.5:
            face.material_index = floor(shine*31)
        else:
            face.material_index = floor(shine*31) + 32

    bm.to_mesh(obj.data)

    obj.data.vertex_colors.remove(obj.data.vertex_colors['shine'])
    obj.data.vertex_colors.remove(obj.data.vertex_colors['opacity'])

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.export_scene.obj(filepath=filepath, axis_forward='Z', use_selection=True, global_scale=scale, keep_vertex_order=True)
    bpy.data.objects.remove(obj, do_unlink=True)
    log.append("File written successfully.")
<<<<<<< Updated upstream
=======
    # mtl_path = filepath[:-3] + 'mtl'
    # line1 = 'map_Ka {}.png\n'.format(texture.filepath_raw)
    # line2 = 'map_Kd {}.png'.format(texture.filepath_raw)
    # with open(mtl_path, 'a') as f:
    #     f.write(line1)
    #     f.write(line2)
>>>>>>> Stashed changes

    return {'FINISHED'}, log
