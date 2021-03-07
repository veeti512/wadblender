from os import path
from math import floor

import bpy
import bmesh

from . import sprytile_utils as sprytile

def generateNodesSetup(name, uvmap):
    if name in bpy.data.materials:
        return bpy.data.materials[name]

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.blend_method = 'CLIP'
    mat.alpha_threshold = 0.5

    # Get the material texture (if any) so we can keep it
    mat_texture = bpy.data.images.load(uvmap)

    # Setup nodes
    nodes = mat.node_tree.nodes
    nodes.clear()

    # Input image
    texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
    texImage.interpolation = 'Closest'

    # Shader
    bsdf = mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')

    # Output
    output_n = nodes.new(type='ShaderNodeOutputMaterial')

    # Vertex colors nodes
    shine_node = mat.node_tree.nodes.new('ShaderNodeVertexColor')
    shine_node.layer_name = 'shine'
    opacity_node = mat.node_tree.nodes.new('ShaderNodeVertexColor')
    opacity_node.layer_name = 'opacity'
    shade_node = nodes.new("ShaderNodeVertexColor")
    shade_node.layer_name = 'shade'
    mul_node = nodes.new("ShaderNodeMixRGB")
    mul_node.blend_type = 'MULTIPLY'
    mul_node.inputs[0].default_value = 1.0
    invert_roughness_node = nodes.new('ShaderNodeInvert')
    invert_alpha_node = nodes.new('ShaderNodeInvert')
    invert_luminosity_node = nodes.new('ShaderNodeInvert')

    # Links
    links = mat.node_tree.links
    links.new(shine_node.outputs['Color'], invert_roughness_node.inputs['Color'])
    links.new(invert_roughness_node.outputs['Color'], bsdf.inputs['Roughness'])
    links.new(opacity_node.outputs['Color'], invert_alpha_node.inputs['Color'])
    links.new(invert_alpha_node.outputs['Color'], bsdf.inputs['Alpha'])

    links.new(texImage.outputs["Color"], mul_node.inputs['Color1'])

    links.new(shade_node.outputs["Color"], invert_luminosity_node.inputs['Color'])
    links.new(invert_luminosity_node.outputs['Color'], mul_node.inputs['Color2'])
    links.new(mul_node.outputs['Color'], bsdf.inputs['Base Color'])

    links.new(bsdf.outputs['BSDF'], output_n.inputs['Surface'])

    # reorder
    bsdf.location = (240, 180)
    shine_node.location = (-140, -94)
    opacity_node.location = (-140, -252)
    shade_node.location = (-540, -100)
    mul_node.location = (-40, 180)
    texImage.location = (-460, 180)
    output_n.location = (540, 180)
    invert_roughness_node.location = (40, -52)
    invert_alpha_node.location = (40, -210)
    invert_luminosity_node.location = (-360, -100)

    if mat_texture:
        texImage.image = mat_texture

    return mat


def setShineOpacity(obj, face, polygon, roughness_layer, opacity_layer):
    if obj.get('opacity') is not None:
        for loop in face.loops:
            intensity = 1 - polygon.intensity / 31 if polygon.shine == 1 else 0
            loop[roughness_layer] = (intensity, intensity, intensity, 1)

            alpha = polygon.opacity
            loop[opacity_layer] = (alpha, alpha, alpha, 1)
    else:
        for loop in face.loops:
            intensity = 0
            loop[roughness_layer] = (0, 0, 0, 1)
            loop[opacity_layer] = (0, 0, 0, 1)


def setUV(face, polygon, uvrect, uv_layer):
    a, b, c, d = uvrect
    if len(polygon.face) == 4:
        uv = (a, b, c, d)
    else:
        if polygon.order == 0:
            uv = (a, b, d)
        elif polygon.order == 2:
            uv = (b, c, a)
        elif polygon.order == 4:
            uv = (c, d, b)
        else:
            uv = (d, a, c)

    k = 0
    for loop in face.loops:
        loop[uv_layer].uv = uv[k]
        k += 1


def createPageMaterial(filepath, context):
    sprytile_installed = sprytile.check_install()
    obj = context.object

    material_name = filepath[filepath.rindex(path.sep) + 1: filepath.rindex('.')]
    mat = generateNodesSetup(material_name, filepath)
        
    set_idx = len(obj.material_slots)
    bpy.ops.object.material_slot_add()
    obj.active_material_index = set_idx
    obj.material_slots[set_idx].material = mat
    bpy.data.materials.update()

    target_mat = obj.material_slots[obj.active_material_index].material
    target_mat.name = material_name

    if sprytile_installed:
        sprytile.update(context)

    return target_mat



def pack_textures(context, meshes, objects, options, name):
    from PIL import Image
    from .texture_packer import pack_object_textures

    sprytile_installed = sprytile.check_install()

    texture_path = options.path + options.wadname + ".png"
    uvtable, new_texture_map = pack_object_textures(meshes, texture_path)

    im = Image.fromarray(new_texture_map)
    if name == '':
        name = objects[0].name
    path = options.path + name + ".png"
    im.save(path)
    mats = [generateNodesSetup(name, path)]

    for mesh, obj in zip(meshes, objects):
        sprytile.assign_material(context, obj, mats[0], sprytile_installed)
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.verify()
        roughness_layer = bm.loops.layers.color.new("shine")
        opacity_layer = bm.loops.layers.color.new("opacity")
        sprytile.verify_bmesh_layers(bm)
        for face_idx, (polygon, face) in enumerate(zip(mesh.polygons, bm.faces)):
            a, b, c, d = polygon.tbox

            x0, y0 = polygon.x, polygon.y
            w, h = polygon.tex_width, polygon.tex_height
            mw, mh = new_texture_map.shape[1], new_texture_map.shape[0]

            p = uvtable[(x0, y0, w, h)]  # top left corner
            left, top = p[0] / mw, 1 - p[1] / mh
            right, bottom = (p[0] + w) / mw, 1 - (p[1] + h) / mh

            a = (left, top)
            b = (right, top)
            c = (right, bottom)
            d = (left, bottom)

            tile = min(a, b, c, d)
            tile_x, tile_y = tile
            tile_x = floor(tile_x * (mw+1))
            tile_y = floor(tile_y * (mh+1))

            uvrect = [a, b, c, d]
            if polygon.flipX:
                uvrect = [b, a, d, c]

            if polygon.flipY:
                uvrect = [d, c, b, a]

            face.material_index = 0
            setUV(face, polygon, uvrect, uv_layer)
            setShineOpacity(obj, face, polygon, roughness_layer, opacity_layer)

            if sprytile_installed:
                sprytile.write_metadata(
                    context, obj, face_idx, bm, 
                    polygon.tex_width, polygon.tex_height, 
                    tile_x, tile_y, polygon.flipX, polygon.flipY, mw
                )

        bm.to_mesh(obj.data)


def apply_textures(context, mesh, obj, materials, options, name=''):
    sprytile_installed = sprytile.check_install()
    for i in range(len(materials)):
        obj.data.materials.append(materials[i])

    bm = bmesh.new()
    bm.from_mesh(obj.data)

    uv_layer = bm.loops.layers.uv.verify()
    roughness_layer = bm.loops.layers.color.new("shine")
    opacity_layer = bm.loops.layers.color.new("opacity")
    sprytile.verify_bmesh_layers(bm)
    for idx, (polygon, face) in enumerate(zip(mesh.polygons, bm.faces)):
        tile = min(polygon.tbox)
        tile_x, tile_y = tile
        tile_x = floor(tile_x * 256)
        tile_y = floor(tile_y * 256)

        face.material_index = polygon.page
        setUV(face, polygon, polygon.tbox, uv_layer)
        setShineOpacity(obj, face, polygon, roughness_layer, opacity_layer)

        if sprytile_installed and options.texture_pages:
            sprytile.write_metadata(
                context, obj, idx, bm, 
                polygon.tex_width, polygon.tex_height, 
                tile_x, tile_y, polygon.flipX, polygon.flipY
            )

    bm.to_mesh(obj.data)
