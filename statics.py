import bpy
import math
import os

from .create_materials import apply_textures, pack_textures


def paint_vertex(obj):
    mesh = obj.data

    vcol_layer = mesh.vertex_colors.new(name='shade')


    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            loop_vert_index = mesh.loops[loop_index].vertex_index
            if loop_vert_index >= len(obj['shades']):
                # static has dynamic lighting info
                return
            shade = 1 - obj['shades'][loop_vert_index] / 255
            vcol_layer.data[loop_index].color = [1 - shade, ] * 3 + [1.0]


def main(context, materials, wad, options):
    main_collection = bpy.data.collections.get('Collection')
    if bpy.data.collections.find('Statics') == -1:
        col = bpy.data.collections.new('Statics')
    else:
        col = bpy.data.collections['Statics']

    if 'Statics' not in main_collection.children:
        main_collection.children.link(col)

    for static in wad.statics:
        idx = str(static.idx)
        if idx in options.static_names:
            name = options.static_names[idx]
        else:
            name = 'STATIC' + idx

        if options.single_object and name != options.object:
            continue

        m = static.mesh
        verts = [[v/options.scale for v in e] for e in m.vertices]
        faces = [e.face for e in m.polygons]
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)
        obj['shades'] = m.shades
        col.objects.link(obj)
        bpy.context.view_layer.objects.active = obj
        mesh.from_pydata(verts, [], faces)
        if options.one_material_per_object:
            pack_textures(context, [m], [obj], options, name)
        else:
            apply_textures(context, m, obj, materials, options, name)
        if options.flip_normals:
            mesh.flip_normals()
        paint_vertex(obj)

        bpy.context.object.select_set(True)
        bpy.context.object.rotation_euler[0] = -math.pi/2
        bpy.context.object.rotation_euler[2] = -math.pi
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        if options.export_fbx:
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.object.select_set(True)
            filepath = os.path.join(options.path, '{}.fbx'.format(name))
            bpy.ops.export_scene.fbx(filepath=filepath, axis_forward='Z',
                                     use_selection=True, add_leaf_bones=False,
                                     bake_anim_use_all_actions=False)

        if options.export_obj:
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.object.select_set(True)
            filepath = os.path.join(options.path, '{}.obj'.format(name))
            bpy.ops.export_scene.obj(filepath=filepath, axis_forward='Z',
                                     use_selection=True)

            mtl_path = filepath[:-3] + 'mtl'
            line1 = 'map_Ka {}.png\n'.format(name)
            line2 = 'map_Kd {}.png'.format(name)
            with open(mtl_path, 'a') as f:
                f.write(line1)
                f.write(line2)

        if not options.single_object:
            obj.hide_set(True)
