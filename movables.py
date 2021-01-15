import bpy
import math

from .objects import movable_names, movables2discard
from .common import apply_textures, create_animations, save_animations_data
import bmesh

def main(materials, wad, options):
    movable_objects = {}
    animations = {}
    main_collection = bpy.data.collections.get('Collection')
    col_movables = bpy.data.collections.new('Movables')
    main_collection.children.link(col_movables)
    for i, movable in enumerate(wad.movables):
        name = movable_names[movable.idx]
        if name in movables2discard:
            continue
        collection = bpy.data.collections.new(name)
        col_movables.children.link(collection)

        meshes = []        
        for j, m in enumerate(movable.meshes):
            verts = [[v / options.scale for v in e] for e in m.vertices]
            faces = [e.face for e in m.polygons]
            shine = [e.shine for e in m.polygons]
            shineIntensity = [e.intensity for e in m.polygons]
            opacity = [e.opacity for e in m.polygons]
            mesh_name = name + '.' + str(j).zfill(3)
            mesh_data = bpy.data.meshes.new(mesh_name)
            mesh_obj = bpy.data.objects.new(mesh_name, mesh_data)
            mesh_obj['boundingSphereCenter'] = [e / options.scale for e in m.boundingSphereCenter]
            mesh_obj['boundingSphereRadius'] = m.boundingSphereRadius / options.scale
            mesh_obj['shine'] = shine
            mesh_obj['shineIntensity'] = shineIntensity
            mesh_obj['opacity'] = opacity

            collection.objects.link(mesh_obj)
            bpy.context.view_layer.objects.active = mesh_obj
            mesh_data.from_pydata(verts, [], faces)
            if m.normals:
                for v, normal in zip(mesh_data.vertices, m.normals):
                    v.normal = normal

            bpy.ops.object.mode_set(mode='EDIT')
            bm = bmesh.from_edit_mesh(mesh_data)


            bpy.ops.object.mode_set(mode='OBJECT')
            apply_textures(m, mesh_obj, materials)
            mesh_data.flip_normals()
            meshes.append(mesh_obj)
            
        movable_objects[name] = meshes
        animations[name] = movable.animations

        meshnames = [m.name for m in meshes]
        
        parent = meshes[0].name
        prev = parent
        stack = [meshes[0].name] * 100
        cpivot_points = {}
        cpivot_points[meshes[0].name] = (0., 0., 0.)
        parents = {}
        if len(meshes) > 1:
            for j in range(1, len(meshes)):
                op, dx, dy, dz = movable.joints[j-1]
                cur = meshnames[j]
                if op == 0:
                    parent = prev
                elif op == 1:
                    parent = stack.pop()
                elif op == 2:
                    parent = prev
                    stack.append(parent)
                else:
                    parent = stack[-1]

                parents[cur] = parent
                px, py, pz = cpivot_points[parent]
                s = options.scale
                cpivot_points[cur] = (px + dx/s, py + dy / s, pz + dz / s)
                mesh_obj = next(mesh for mesh in meshes if mesh.name == cur)
                mesh_obj.location = cpivot_points[cur]
                prev = cur

            amt = bpy.data.armatures.new(name)
            rig = bpy.data.objects.new(name + '_RIG', amt)
            collection.objects.link(rig)
            bpy.context.view_layer.objects.active = rig

            bpy.ops.object.mode_set(mode='EDIT')
            for cur in meshnames:
                if cur not in parents:
                    bone = amt.edit_bones.new(cur)
                    bone.head, bone.tail = (0., 0., 0.), (0., 100 / options.scale, 0.)
                    bone = None
                else:
                    tail = [child for child, parent in parents.items() if parent == cur]
                    
                    if len(tail) > 0:
                        bone = amt.edit_bones.new(cur)
                        bone.head, bone.tail = cpivot_points[cur], cpivot_points[tail[0]]
                        if bone.head[1] > bone.tail[1]:
                            x, y, z = bone.head
                            bone.tail = (x, y + 100 / options.scale, z)
                        bone.parent = amt.edit_bones[parents[cur]]
                        if bone.head == bone.tail:
                            bone.tail[1] += 0.001
                        bone = None
                    else:
                        bone = amt.edit_bones.new(cur)
                        x, y, z = cpivot_points[cur]
                        bone.head, bone.tail = cpivot_points[cur], (x, y + 100 / options.scale, z)
                        bone.parent = amt.edit_bones[parents[cur]]
                        bone = None

            bone = None
            bpy.ops.object.mode_set(mode="OBJECT")

            for i in range(len(meshes)):
                mesh = meshes[i]
                bonename = mesh.name
                mesh.vertex_groups.new(name=bonename)
                mesh = None
                
            bpy.ops.object.mode_set(mode="OBJECT")
            for i in range(len(meshes)):
                mesh = meshes[i]
                bonename = mesh.name
                vertices = [vert.index for vert in mesh.data.vertices]
                bpy.ops.object.mode_set(mode="OBJECT")
                mesh.vertex_groups[bonename].add(vertices, 1.0, "ADD")
                mesh.parent = rig
                modifier = mesh.modifiers.new(type='ARMATURE', name=rig.name)
                modifier.object = rig



            if options.import_anims:
                create_animations(rig, meshnames, cpivot_points, animations[name], options)

            if options.export_json:
                save_animations_data(animations[name], options.path, name)
        

            bpy.context.view_layer.objects.active = rig

            if options.rotate:
                bpy.ops.object.mode_set(mode="OBJECT")
                bpy.context.object.rotation_euler[0] = -math.pi/2
                bpy.context.object.rotation_euler[2] = -math.pi
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        else:
            if options.rotate:
                bpy.ops.object.mode_set(mode="OBJECT")
                for obj in collection.objects:
                    obj.select_set(True)
                bpy.context.object.rotation_euler[0] = -math.pi/2
                bpy.context.object.rotation_euler[2] = -math.pi
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


        if options.export_fbx:
            filepath = options.path + '\\{}.fbx'.format(name)
            bpy.ops.object.select_all(action='DESELECT')

            bpy.context.view_layer.objects.active = rig
            for obj in collection.objects:
                obj.select_set(True)
            bpy.ops.export_scene.fbx(filepath=filepath, axis_forward='Z', use_selection=True, add_leaf_bones=False, bake_anim_use_all_actions =False)


        if options.export_obj:
            filepath = options.path + '\\{}.obj'.format(name)
            bpy.ops.object.select_all(action='DESELECT')

            bpy.context.view_layer.objects.active = rig
            for obj in collection.objects:
                obj.select_set(True)
            bpy.ops.export_scene.obj(filepath=filepath, axis_forward='Z', use_selection=True)
            
        bpy.context.view_layer.layer_collection.children['Collection'].children['Movables'].children[name].hide_viewport = True