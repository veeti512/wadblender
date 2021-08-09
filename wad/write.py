import struct
import numpy as np
import bpy
import bmesh
from math import floor, pi

from .data import TextureSamples, BoundingSphere, ShortVector3D, Static, Movable
from .data import pack_int16, pack_uint32, pack_uint16

class WADBlenderException(Exception):
    pass


def verify_vcol_layer(bm, layer_name, val):
    if layer_name not in bm.loops.layers.color:
        v = 0
        vcolor_layer = bm.loops.layers.color.new(layer_name)
        for face in bm.faces:
            for loop in face.loops:
                loop[vcolor_layer] = (val, val, val, 1)
                v += 1
    else:
        vcolor_layer = bm.loops.layers.color[layer_name]

    return vcolor_layer


def get_textures(obj):
    textures = []
    for mat_slot in obj.material_slots:
        if mat_slot.material:
            if mat_slot.material.node_tree:
                for x in mat_slot.material.node_tree.nodes:
                    if x.type=='TEX_IMAGE':
                        textures.append(x.image)
                        break

    return textures


def writeWAD(obj_orig, obj_id, filepath, name, is_static=False, scale=512):
    log = []
    textures = get_textures(obj_orig)
    if len(textures) != len(obj_orig.material_slots):
        log.append('W{} materials but {} images only.'.format(len(obj_orig.material_slots), len(textures)))
        log.append("WOperation cancelled.")
        return {'CANCELLED'}, log
    log.append("Processed {} materials.".format(len(textures)))

    # duplicate object
    obj = obj_orig.copy()
    obj.data = obj_orig.data.copy()
    bpy.context.collection.objects.link(obj)

    # axis swap
    obj.rotation_euler[0] = pi/2
    obj.rotation_euler[1] = pi
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.parent_clear(type='CLEAR')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obj.select_set(False)
    
    # blender normals are opposite to TRLE wrt vertices order
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for face in bm.faces:
        face.normal_flip()

    # concatenate textures vertically
    from PIL import Image
    imgs = []
    images_hw = {}
    for i, texture in enumerate(textures):
        width, height = texture.size[0], texture.size[1]
        pixels = np.array(texture.pixels[:]) * 255
        img = np.flipud(pixels.astype(np.uint8).reshape((height, width, 4)))
        images_hw[i] = height, width

        if width < 256:
            img = np.pad(img, [(0, 0), (0, 256-width), (0, 0)], mode='constant')
            log.append("Image {} padded".format(texture.name))
            log.append("from {}x{} to {}x{}".format(width,height, 256, height))
        elif width > 256:
            pil_img = Image.fromarray(img)
            wpercent = (256 / float(pil_img.size[0]))
            hsize = int((float(pil_img.size[1]) * float(wpercent)))
            img = pil_img.resize((256, hsize))
            img = np.array(img)
            log.append("WImage {} resized".format(texture.name))
            log.append("Wfrom {}x{} to {}x{}".format(width,height, 256, hsize))

        imgs.append(img)

    image = np.concatenate(imgs)

    # convert RGB+A image to RGB with magenta to indicate transparency
    wad_texture_map = np.array(image)
    new_texture_map = wad_texture_map[:, :, :3]
    for y in range(wad_texture_map.shape[0]):
        for x in range(wad_texture_map.shape[1]):
            if wad_texture_map[y][x][3] < 0.5:
                new_texture_map[y][x][0] = 255
                new_texture_map[y][x][1] = 0
                new_texture_map[y][x][2] = 255

    # texture map is stored as a standard RAW 24bits [RGB] pixel file
    raw_img = Image.fromarray(new_texture_map).tobytes('raw', 'RGB', 0, 1)
    map_bytes_size = len(raw_img)
    h = new_texture_map.shape[0]
    log.append('Generated:')
    log.append('texture 256x{} ({} pages)'.format(h,1 + h//256))

    uv_layer = bm.loops.layers.uv.verify()
    uvrects = {}  # uv coordinates for each face
    rect2text_id = {}  # from texture sample coordinates to texture sample id
    face_texture = {}  # texture sample id for each face
    triangles = quads = 0
    poly_shape = {}
    

    texture_samples = []
    text_sample_map_wh = {}
    # add dummy texture sample to avoid ambiguous representation of 
    # first texture sample when flipped
    texture_samples.append((0, 0, 1, 1))
    text_sample_map_wh[0] = (1, 1)

    faces2remove = []
    for face in bm.faces:
        mat = face.material_index
        map_height, map_width, _ = imgs[mat].shape
        uvrect = []
        for loop in face.loops:
            u, v = loop[uv_layer].uv
            u, v = round(u*map_width), round((1 - v)*map_height)
            for img in imgs[:mat]:
                v += img.shape[0]
            uvrect.append((u, v))

        if len(set(uvrect)) != len(uvrect):
            print('removed', face.index, uvrect)
            faces2remove.append(face)

    bmesh.ops.delete( bm, geom = faces2remove, context = 'FACES_ONLY' )

    # bm.to_mesh(obj.data)
    # bm.from_mesh(obj.data)
    poly_count = len(bm.faces)

    for face in bm.faces:
        mat = face.material_index
        map_height, map_width = images_hw[mat] # imgs[mat].shape
        if len(face.verts) == 4:
            poly_shape[face.index] = 9
            quads += 1
        elif len(face.verts) == 3:
            poly_shape[face.index] = 8
            triangles += 1
        else:
            log.append("WFound ngon on face{} but".format(face.index))
            log.append("Wonly triangles or quads are supported.") 
            log.append("WOperation cancelled.")
            bpy.data.objects.remove(obj, do_unlink=True)
            return {'CANCELLED'}, log

        uvrect = []
        left = top = float('inf')
        right = bottom = 0
        for loop in face.loops:
            u, v = loop[uv_layer].uv
            u, v = round(u*map_width), round((1 - v)*map_height)
            for img in imgs[:mat]:
                v += img.shape[0]
            left = min(u, left)
            top = min(v, top)
            right = max(u, right)
            bottom = max(v, bottom)
            uvrect.append((u, v))

        if len(set(uvrect)) != len(uvrect):
            log.append("Collapsed vertices on face {}: {}".format(face.index, uvrect))
            log.append("WOperation cancelled.")
            bpy.data.objects.remove(obj, do_unlink=True)
            return {'CANCELLED'}, log
        
        uvrects[face.index] = uvrect

        text_sample = (left, top, right, bottom)
        if text_sample not in rect2text_id:
            rect2text_id[text_sample] = len(texture_samples)
            text_sample_map_wh[len(texture_samples)] = images_hw[mat]
            texture_samples.append(text_sample)

        face_texture[face.index] = rect2text_id[text_sample]

    log.append('{} texture samples'.format(len(texture_samples)-1))
    log.append('{} polygons'.format(triangles + quads))
    flip = {}
    poly_order = {}
    order_encoder = {'abd': 0, 'abc': 2, 'bcd': 4, 'acd': 6, 'abcd': 7,
                     'acb': 0, 'adb': 2, 'adc': 4, 'bdc': 6, 'adcb': 7}

    first_vertex = {0: 'a', 2: 'b', 4: 'c', 6: 'd', 7: 'a'}
    first_vertex_flip = {0: 'b', 2: 'a', 4: 'd', 6: 'c', 7: 'b'}

    vertex_indices = {}
    for face in bm.faces:
        vindices = [loop.vert.index for loop in face.loops]
        left, top, right, bottom = texture_samples[face_texture[face.index]]
        texture_sample = [(left, top), (right, top), (right, bottom), (left, bottom)]
        vertices_order = [texture_sample.index(e) for e in uvrects[face.index]]
        pivot = vertices_order.index(min(vertices_order))
        vertices_order = vertices_order[pivot:] + vertices_order[:pivot]
        vindices = vindices[pivot:] + vindices[:pivot]
        
        order = ''.join('abcd'[i] for i in vertices_order)
        poly_order[face.index] = order_encoder[order]

        flip[face.index] = (vertices_order != sorted(vertices_order))
        if flip[face.index]:
            anchor_vertex = first_vertex_flip[poly_order[face.index]]
        else:
            anchor_vertex = first_vertex[poly_order[face.index]]

        pivot = order.index(anchor_vertex)
        vertices_order = vertices_order[pivot:] + vertices_order[:pivot]
        vindices = vindices[pivot:] + vindices[:pivot]
        vertex_indices[face.index] = vindices

    texture_samples_pkg = []
    for i, (left, top, right, bottom) in enumerate(texture_samples):
        map_height, map_width = text_sample_map_wh[i]
        x, y = left, top
        page, y = divmod(y, 256)
        page, bottom = divmod(bottom, 256)

        addW = right - left - 1
        addH = bottom - top - 1

        w, h = addW, addH
        if not (x + w <= map_width and y + h <= map_height):
            log.append("Texture sample {} is out of bounds.".format(i))
            log.append("WOperation cancelled.")
            bpy.data.objects.remove(obj, do_unlink=True)
            return {'CANCELLED'}, log

        ts = TextureSamples(TextureSamples.size, TextureSamples.format,
                            x, y, page, -1, addW, -1, addH)

        texture_samples_pkg.append(ts)

    texture_samples_count = len(texture_samples_pkg)
    mesh_pointers_count = 1
    mesh_pointers = 0
    bs = BoundingSphere(BoundingSphere.size, BoundingSphere.format, 0, 0, 0, 0, 0)

    vertices = []
    for v in bm.verts:
        x, y, z = [floor(e*scale) for e in v.co]
        vec = ShortVector3D(ShortVector3D.size, ShortVector3D.format, x, y, z)
        vertices.append(vec)

    vertices_cnt = len(vertices)
    log.append('{} vertices.'.format(vertices_cnt))
    shades = []
    normals = []
    if is_static:
        shade_layer = verify_vcol_layer(bm, 'shade', 0.5)
        shades = [0] * vertices_cnt
        for face in bm.faces:
            for loop in face.loops:
                shades[loop.vert.index] = 8191 - floor(loop[shade_layer][0] * 8191)
    else:
        normals = [0] * vertices_cnt
        shine_layer = verify_vcol_layer(bm, 'shine', 0)
        opacity_layer = verify_vcol_layer(bm, 'opacity', 0)
        for face in bm.faces:
            for loop in face.loops:
                x, y, z = (floor(16300*co) for co in loop.vert.normal)
                vec = ShortVector3D(ShortVector3D.size, ShortVector3D.format, x, y, z)
                normals[loop.vert.index] = vec


        # bnormals = [vertex.normal for vertex in obj.data.vertices]
        # for norm in bnormals:

        face_shine = {}
        is_face_translucent = {}
        for face in bm.faces:
            shine = 0
            opacity = 0
            for loop in face.loops:
                shine = max(shine, loop[shine_layer][0])
                opacity = max(opacity, loop[opacity_layer][0])
            face_shine[face.index] = shine
            is_face_translucent[face.index] = opacity > 0

    texture = {}
    for face in bm.faces:
        flipped = 1 if flip[face.index] else 0
        index = face_texture[face.index]
        order = poly_order[face.index]
        shape = poly_shape[face.index]
        if shape == 8:
            texture[face.index] = index + (order << 12) + (flipped << 15)
        else:
            texture[face.index] = index
            if flipped == 1:
                texture[face.index] = 0X10000 - texture[face.index]
                # this should not happen
                if texture[face.index] == 0X10000:
                    texture[face.index] = 0XFFFF


    output = []
    output.append(pack_uint32(129)) # version
    output.append(pack_uint32(texture_samples_count))
    for ts in texture_samples_pkg:
        print(ts)
        output.append(ts.encode())
    output.append(pack_uint32(map_bytes_size))
    output.append(raw_img)
    output.append(pack_uint32(mesh_pointers_count))
    output.append(pack_uint32(mesh_pointers))

    offset_idx = 16 + 6 * vertices_cnt + 12 * poly_count + 2 * len(shades) + 6 * len(normals) + 2 * quads
    if quads % 2 == 1:
        offset_idx += 2

    output.append(pack_uint32(offset_idx // 2))

    # POLYGONS
    output.append(bs.encode())
    output.append(pack_uint16(vertices_cnt))
    for v in vertices:
        output.append(v.encode())

    if is_static:
        output.append(pack_int16(-vertices_cnt))
        assert vertices_cnt == len(shades)
        output += [pack_int16(s) for s in shades]
    else:
        output.append(pack_int16(vertices_cnt))
        output += [normal.encode() for normal in normals]
        assert vertices_cnt == len(normals)


    output.append(pack_uint16(poly_count))
    for face in bm.faces:
        ps = poly_shape[face.index]
        assert ps == 8 or ps == 9
        output.append(pack_uint16(ps))
        if ps == 9:
            a = struct.pack('4H', *(e for e in vertex_indices[face.index]))
        else:
            a = struct.pack('3H', *(e for e in vertex_indices[face.index]))

        output.append(a)
        output.append(pack_uint16(texture[face.index]))
        if is_static:
            output.append(struct.pack('B', 0))  # attributes
        else:
            intensity = floor(face_shine[face.index])
            shine = intensity > 0
            opacity = is_face_translucent[face.index]
            attributes = (intensity << 2) + (shine << 1) + opacity
            output.append(struct.pack('B', attributes))  # attributes

        output.append(struct.pack('B', 0))  # unknown

    if quads % 2 == 1:
        output.append(pack_uint16(0))  # padding

    # MOVABLES STUFF
    output += [pack_uint32(0)] * 6

    if is_static:
        movables_count = 0
        output.append(pack_uint32(movables_count))
    else:
        movables_count = 1
        output.append(pack_uint32(movables_count))
        mov = Movable(Movable.size, Movable.format, obj_id, 1, 0, 0, 0, 0)
        output.append(mov.encode())


    # STATICS STUFF
    if is_static:
        statics_count = 1
        output.append(pack_uint32(statics_count))
        static = Static(Static.size, Static.format, obj_id, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        output.append(static.encode())
    else:
        statics_count = 0
        output.append(pack_uint32(statics_count))

    with open(filepath, 'wb') as f:
        for e in output:
            f.write(e)

    was_filepath = filepath[:-3] + 'was'
    with open(was_filepath, 'w') as f:
        line = '{}:Z:\WADBLENDER\{}.prk\n'.format(name, name)
        f.write(line)

    bpy.data.objects.remove(obj, do_unlink=True)
    log.append("File written successfully.")
    return {'FINISHED'}, log
