import bpy
import math

from .objects import static_names
from .common import apply_textures, createMaterial


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


def main(path, wadname, w, scale, export_fbx):

    uvmap = bpy.data.images.new('textures', w.mapwidth, w.mapheight, alpha=True)
    uvmap.pixels = w.textureMap

    mat = createMaterial(uvmap)
    bpy.data.images["textures"].save_render(path + "textures.png")

    main_collection = bpy.data.collections.get('Collection')
    col = bpy.data.collections.new('Statics')
    main_collection.children.link(col)

    for static in w.statics:
        m = static.mesh
        verts = [[v/scale for v in e] for e in m.vertices]
        faces = [e.face for e in m.polygons]
        name = static_names[static.idx]
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)
        obj['shades'] = m.shades
        col.objects.link(obj)
        bpy.context.view_layer.objects.active = obj
        mesh.from_pydata(verts, [], faces)
        apply_textures(m, obj, mat)
        mesh.flip_normals()
        paint_vertex(obj)

        bpy.context.object.rotation_euler[0] = -math.pi/2
        bpy.context.object.rotation_euler[2] = -math.pi
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        obj.hide_set(True)

        if export_fbx:
            obj.select_set(True)
            filepath = path + '\\{}.fbx'.format(name)
            bpy.ops.export_scene.fbx(filepath=filepath, axis_forward='Z', use_selection=True, add_leaf_bones=False, bake_anim_use_all_actions =False)
