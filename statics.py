import bpy
import math

from .objects import static_names
from .common import apply_textures


def paint_vertex(obj):
    mesh = obj.data
    if mesh.vertex_colors:
        vcol_layer = mesh.vertex_colors.active
    else:
        vcol_layer = mesh.vertex_colors.new()

    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            loop_vert_index = mesh.loops[loop_index].vertex_index
            vcol_layer.data[loop_index].color = [1 - obj['shades'][loop_vert_index] / 255, ] * 3 + [1.0]


def main(materials, wad, options):

    main_collection = bpy.data.collections.get('Collection')
    col = bpy.data.collections.new('Statics')
    main_collection.children.link(col)

    for static in wad.statics:
        m = static.mesh
        verts = [[v/options.scale for v in e] for e in m.vertices]
        faces = [e.face for e in m.polygons]
        name = static_names[static.idx]
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)
        obj['shades'] = m.shades
        col.objects.link(obj)
        bpy.context.view_layer.objects.active = obj
        mesh.from_pydata(verts, [], faces)
        apply_textures(m, obj, materials)
        mesh.flip_normals()
        paint_vertex(obj)

        if options.rotate:
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.context.object.select_set(True)
            bpy.context.object.rotation_euler[0] = -math.pi/2
            bpy.context.object.rotation_euler[2] = -math.pi
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        if options.export_fbx:
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.object.select_set(True)
            filepath = options.path + '\\{}.fbx'.format(name)
            bpy.ops.export_scene.fbx(filepath=filepath, axis_forward='Z', use_selection=True, add_leaf_bones=False, bake_anim_use_all_actions =False)

        if options.export_obj:
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.object.select_set(True)
            filepath = options.path + '\\{}.obj'.format(name)
            bpy.ops.export_scene.obj(filepath=filepath, axis_forward='Z', use_selection=True)

        obj.hide_set(True)