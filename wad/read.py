import io
from . import model
from . import data


def read_mesh(mesh, texture_samples, map_width, map_height, options):
    vertices = [(e.vx, e.vy, e.vz) for e in mesh["vertices"]]
    normals = [(e.vx, e.vy, e.vz) for e in mesh["normals"]]
    bs = mesh["bounding_sphere"]
    bounding_sphere_center = model.Point(bs.cx, bs.cy, bs.cz)
    bounding_sphere_radius = bs.radius
    shades = mesh["shades"]
    polygons = []
    for polygon in mesh["polygons"]:
        tex = texture_samples[polygon.texture_index]

        if options.texture_pages:
            # top left in uv coordinates
            x0 = tex.x / 256
            y0 = 1 - tex.y / 256

            # bottom right in uv coordinates
            x1 = (tex.x + tex.width) / 256
            y1 = 1 - (tex.y + tex.height) / 256
        else:
            # top left in uv coordinates
            x0 = tex.mapX / map_width
            y0 = 1 - tex.mapY / map_height

            # bottom right in uv coordinates
            x1 = (tex.mapX + tex.width) / map_width
            y1 = 1 - (tex.mapY + tex.height) / map_height

        """
        a         b
        ###########
        #         #
        #         #
        ###########
        d         c
        """

        a = (x0, y0)
        b = (x1, y0)
        c = (x1, y1)
        d = (x0, y1)


        uvrect = [a, b, c, d]
        flipX = tex.flipX
        if tex.flipX == 0:
            uvrect = [b, a, d, c]

        if tex.flipY == 0:
            uvrect = [d, c, b, a]

        if polygon.texture_flipped == 1:
            flipX = not flipX
            uvrect = [b, a, d, c]

        sample = tex
        x, y, w, h = sample.mapX, sample.mapY, sample.width, sample.height
        assert x + w <= map_width and y + h <= map_height

        assert tex.mapX + tex.width <= map_width
        assert tex.mapY + tex.height <= map_height

        poly_model = model.Polygon(polygon.vertices,
                                   uvrect,
                                   polygon.texture_shape,
                                   polygon.intensity,
                                   polygon.shine,
                                   polygon.opacity,
                                   tex.page,
                                   tex.width,
                                   tex.height,
                                   not flipX,
                                   not tex.flipY,
                                   a,
                                   tex.mapX,
                                   tex.mapY,
                                   )

        polygons.append(poly_model)

    return model.Mesh(vertices, polygons, normals,
                      bounding_sphere_center, bounding_sphere_radius, shades)


def readWAD(f, options):
    version = data.read_uint32(f)
    assert 129 <= version <= 130

    #####################
    ### TEXTURES DATA ###
    #####################

    # extract position, size and attitude of each texture sample
    texture_samples_count = data.read_uint32(f)
    texture_samples = [data.TextureSamples.decode(f)
                       for _ in range(texture_samples_count)]

    # extract texture map
    bytes_size = data.read_uint32(f)
    map_width = 256
    map_height = bytes_size // 256 // 3
    texture_map, raw_data = data.read_texture_map(f, bytes_size, map_width, map_height)
    if options.texture_pages:
        textureMaps = data.read_splitted_texture_map(raw_data, bytes_size, map_width, map_height)
    else:
        textureMaps = []

    _pages_count = bytes_size // 256 // 256 // 3

    for sample in texture_samples:
        x, y, w, h = sample.mapX, sample.mapY, sample.width, sample.height
        assert x + w <= map_width and y + h <= map_height

    ###################
    ### MESHES DATA ###
    ###################

    mesh_pointers_count = data.read_uint32(f)
    mesh_pointers = [data.read_uint32(f) for _ in range(mesh_pointers_count)]

    # extract meshes
    words_size = data.read_uint32(f)
    mesh_data = []
    offset_idx = 0
    offsets = set()
    while offset_idx < words_size * 2:  # for each mesh
        offsets.add(offset_idx)
        mesh = {}
        mesh["idx"] = offset_idx
        mesh["bounding_sphere"] = data.BoundingSphere.decode(f)

        # table storing the XYZ coordinates of the vertices
        vertices_count = data.read_uint16(f)
        mesh["vertices"] = [data.ShortVector3D.decode(f)
                            for _ in range(vertices_count)]

        ns = data.read_int16(f)  # number of normals Or shades

        normals_count = max(0, ns)
        mesh["normals"] = [data.ShortVector3D.decode(f)
                           for _ in range(normals_count)]
        # normalization
        for normal in mesh["normals"]:
            normal /= 16300

        shades_count = max(0, -ns)
        shades = [data.read_int16(f) for _ in range(shades_count)]
        mesh["shades"] = [int(255 - shade * 255 / 8191)
                          for shade in shades]

        # extract mesh polygons
        poly_count = data.read_uint16(f)
        mesh["polygons"] = [data.Polygon.decode(f) for _ in range(poly_count)]

        # if the number of quads is odd, there is a 2 bytes padding
        quads_count = 0
        for polygon in mesh["polygons"]:
            assert 0 <= polygon.texture_index < len(texture_samples)
            if polygon.shape == 9:
                quads_count += 1

        if quads_count % 2 == 1:
            f.read(2)
            offset_idx += 2

        offset_idx += 16 + 6 * vertices_count + 12 * poly_count + \
            6 * normals_count + 2 * shades_count + 2 * quads_count

        mesh_data.append(mesh)

    for address in mesh_pointers:
        assert address in offsets

    assert offset_idx == words_size * 2

    #######################
    ### ANIMATIONS DATA ###
    #######################

    animations_count = data.read_uint32(f)
    animations_data = [data.Animation.decode(f)
                       for _ in range(animations_count)]

    for animation in animations_data:
        assert 0 <= animation.next_animation < len(animations_data)

    state_changes_count = data.read_uint32(f)
    state_changes_data = [data.StateChanges.decode(f)
                          for _ in range(state_changes_count)]

    dispatches_count = data.read_uint32(f)
    dispatches_data = [data.Dispatches.decode(f)
                       for _ in range(dispatches_count)]

    for dispatch in dispatches_data:
        if not 0 <= dispatch.next_anim < len(animations_data):
            print("Dispatch pointing to invalid animation {}".format(dispatch))

    # extract commands for all the animation segments
    words_size = data.read_uint32(f)
    commands_data = []
    idx = 0
    while idx < words_size * 2:
        command = data.read_uint16(f)
        instruction = [command]
        if command == 1:
            instruction += [data.read_int16(f) for _ in range(3)]
        elif command == 2:
            instruction += [data.read_int16(f) for _ in range(2)]
        elif command == 5 or command == 6:
            instruction += [data.read_uint16(f) for _ in range(2)]

        commands_data.append((idx, instruction))
        idx += len(instruction) * 2

    # extract links between meshes (also called joints, skeleton or mesh tree)
    dwords_size = data.read_uint32(f)
    links_data = [data.read_int32(f) for _ in range(dwords_size)]

    # animations keyframes (will be parsed later)
    keyframes_words_size = data.read_uint32(f)
    keyframes_data_bytes = f.read(2 * keyframes_words_size)

    ###################
    ### MODELS DATA ###
    ###################

    movables_count = data.read_uint32(f)
    movables_data = [data.Movable.decode(f) for _ in range(movables_count)]

    statics_count = data.read_uint32(f)
    statics_data = [data.Static.decode(f) for _ in range(statics_count)]

    assert f.read(1) == b''  # check end of file

    #######################
    ### POST PROCESSING ###
    #######################

    # collect all the data relative to each movable
    movables = []
    for mov_idx, mov_data in enumerate(movables_data):
        movable = {}
        movable['idx'] = mov_data.obj_ID

        # get the index of its meshes in the meshes data package
        movable['mesh_indices'] = []
        meshes_count = mov_data.num_pointers
        first_mesh_pointer = mov_data.pointers_index
        for i in range(meshes_count):
            mesh_pointer = mesh_pointers[first_mesh_pointer + i]
            mesh_idx = next(idx
                            for idx, mesh in enumerate(mesh_data)
                            if mesh["idx"] == mesh_pointer)
            movable['mesh_indices'].append(mesh_idx)

        # get links data (op, dx, dy, dz)
        first_link_pointer = mov_data.links_index
        links_count = meshes_count - 1
        movable['links'] = []
        for i in range(links_count):
            pointer = first_link_pointer + i * 4
            movable['links'].append(links_data[pointer:pointer + 4])

        # get animation data
        idx = mov_idx
        mov_anims_count = 0
        while mov_data.anims_index >= 0:
            idx += 1

            if idx >= movables_count:
                mov_anims_count = len(animations_data) - mov_data.anims_index
                break

            if movables_data[idx].anims_index >= 0:
                mov_anims_count = movables_data[idx].anims_index - \
                    mov_data.anims_index
                break

        if mov_anims_count > 0:
            movable['animations'] = []
            for anim_idx in range(mov_anims_count):
                cur_anim = animations_data[mov_data.anims_index + anim_idx]

                # get next animation to deternime the keyframe buffer size
                next_anim = None
                next_anim_idx = mov_data.anims_index + anim_idx
                while True:
                    next_anim_idx += 1
                    if next_anim_idx >= animations_count:
                        break

                    if animations_data[next_anim_idx].keyframe_size > 0:
                        next_anim = animations_data[next_anim_idx]
                        break

                # parse animation keyframes
                if cur_anim.keyframe_size > 0:
                    if next_anim:
                        keyframes_count = next_anim.keyframe_offset - cur_anim.keyframe_offset
                    else:
                        keyframes_count = keyframes_words_size * 2 - cur_anim.keyframe_offset

                    keyframes_count //= cur_anim.keyframe_size * 2

                    f = io.BytesIO(keyframes_data_bytes)
                    f.seek(cur_anim.keyframe_offset)
                    keyframes_data = [data.Keyframes.decode(f, meshes_count, cur_anim.keyframe_size)
                                      for _ in range(keyframes_count)]
                else:
                    keyframes_count = 0
                    keyframes_data = []

                keyframes = []
                for kf in keyframes_data:
                    offset_idx = (kf.off.vx, kf.off.vy, kf.off.vz)
                    bb1 = (kf.bb1.vx, kf.bb1.vy, kf.bb1.vz)
                    bb2 = (kf.bb2.vx, kf.bb2.vy, kf.bb2.vz)

                    keyframe = model.Keyframe(
                        offset_idx, kf.rotations, bb1, bb2)
                    keyframes.append(keyframe)

                next_animation = cur_anim.next_animation - mov_data.anims_index

                # Get animation state changes
                anim_state_changes_count = cur_anim.num_state_changes
                state_changes = {}
                for i in range(anim_state_changes_count):
                    state_change_data = state_changes_data[cur_anim.changes_index + i]
                    if state_change_data.num_dispatches > 0:
                        # get animation dispatches
                        dispatches = []
                        for j in range(state_change_data.num_dispatches):
                            d = dispatches_data[state_change_data.dispatches_index + j]
                            dispatch = model.Dispatch(
                                d.in_range, 
                                d.out_range, 
                                d.next_anim - mov_data.anims_index, 
                                d.frame_in)
                            dispatches.append(dispatch)

                        state_changes[state_change_data.state_ID] = dispatches

                # Get animation commands
                commands = []
                if cur_anim.num_commands > 0:
                    try:
                        command_it = next(i for i, c in enumerate(commands_data) if c[0] == 2 * cur_anim.commands_offset)
                        for idx in range(cur_anim.num_commands):
                            if command_it + idx < len(commands):
                                e = tuple(commands_data[command_it + idx][1])
                                commands.append(e)

                    except StopIteration:
                        print("Invalid command")

                animation = model.Animation(
                    cur_anim.state_ID, keyframes, state_changes, commands, 
                    cur_anim.frame_duration, cur_anim.speed, 
                    cur_anim.acceleration, cur_anim.frame_start, 
                    cur_anim.frame_end, cur_anim.frame_in, next_animation)
                movable['animations'].append(animation)

        else:
            movable['animations'] = []

        movables.append(movable)

    # for each static
    statics_model = []
    for static in statics_data:
        mesh_pointer = mesh_pointers[static.pointers_index]
        mesh_idx = next(addressIndex
                        for addressIndex, mesh in enumerate(mesh_data)
                        if mesh["idx"] == mesh_pointer)

        mesh = read_mesh(mesh_data[mesh_idx],
                         texture_samples, map_width, map_height, options)
        statics_model.append(model.Static(static.obj_ID, mesh))

    movables_model = []
    for movable in movables:
        meshesTO = [mesh_data[i] for i in movable['mesh_indices']]
        meshes = []
        for meshto in meshesTO:
            mesh = read_mesh(meshto, texture_samples, map_width, map_height, options)
            meshes.append(mesh)

        movable = model.Movable(
            movable['idx'], meshes, movable['links'], movable['animations'])
        movables_model.append(movable)

    return model.Wad(version, statics_model, map_width, map_height, texture_map, movables_model, textureMaps)
