from . import model
from . import data
from importlib import reload
import io
from .objects import movable_names
from .objects import static_names


def preview(f):
    reload(model)
    reload(data)

    version = data.read_uint32(f)
    texture_samples_count = data.read_uint32(f)
    f.read(8 * texture_samples_count)
    bytes_size = data.read_uint32(f)
    f.read(bytes_size)
    mesh_pointers_count = data.read_uint32(f)
    f.read(mesh_pointers_count * 4)
    words_size = data.read_uint32(f)
    f.read(words_size * 2)
    animations_count = data.read_uint32(f)
    f.read(animations_count * 40)
    state_changes_count = data.read_uint32(f)
    f.read(state_changes_count * 6)
    dispatches_count = data.read_uint32(f)
    f.read(dispatches_count*8)
    words_size = data.read_uint32(f)
    f.read(words_size * 2)
    dwords_size = data.read_uint32(f)
    f.read(dwords_size * 4)
    keyframes_words_size = data.read_uint32(f)
    f.read(keyframes_words_size * 2)

    movables_count = data.read_uint32(f)
    movables_data = [data.Movable.decode(f) for _ in range(movables_count)]
    movables = [movable_names[mov.obj_ID] for mov in movables_data]

    statics_count = data.read_uint32(f)
    statics_data = [data.Static.decode(f) for _ in range(statics_count)]
    statics = [static_names[stat.obj_ID] for stat in statics_data]

    return movables, statics
