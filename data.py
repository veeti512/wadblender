from dataclasses import dataclass
import struct
import io
from typing import List
from collections import Counter
from math import pi


def read_uint32(f):
    return struct.unpack('I', f.read(4))[0]


def read_int32(f):
    return struct.unpack('i', f.read(4))[0]


def read_uint16(f):
    return struct.unpack('H', f.read(2))[0]


def read_int16(f):
    return struct.unpack('h', f.read(2))[0]


def read_texture_map(f, texture_byte_size, map_width, map_height):
    """texture map is stored as a standard RAW 24bits [RGB] pixel file"""
    raw_data = f.read(texture_byte_size)
    pixels = []
    idx = 0
    for _y in range(map_height):
        row = []
        for _x in range(map_width):
            red, green, blue = raw_data[idx:idx + 3]
            idx += 3
            if red == 255 and green == 0 and blue == 255:  # magenta
                alpha = red = blue = 0
            else:
                alpha = 255

            row += [red, green, blue, alpha]

        pixels.append(row)

    # flip to move uv origin from bottom left to top left
    pixels.reverse()
    img_pixels = []
    for row in pixels:
        for val in row:
            img_pixels.append(val/255)

    return img_pixels


@dataclass
class DecoderInterface:
    size: int
    format: str

    @classmethod
    def decode(cls, f):
        data = struct.unpack(cls.format, f.read(cls.size))
        return cls(cls.size, cls.format, *data)


@dataclass
class TextureSamples(DecoderInterface):
    x: int  # anchor corner x pixel position
    y: int  # anchor corner y pixel position
    page: int  # page where the texture sample is stored
    flipX: int  # horizontal flip, yes or no, -1 or 0
    addW: int  # number of pixels to add to the width
    flipY: int  # vertical flip, yes or no, -1 or 0
    addH: int  # number of pixels to add to the height

    size = 8
    format = '2B H b B b B'

    def __post_init__(self):
        assert -1 <= self.flipX <= 0 and -1 <= self.flipY <= 0

        # map-relative coordinates
        self.mapX = self.x
        self.mapY = self.y + 256 * self.page
        self.width = self.addW + 1
        self.height = self.addH + 1


@dataclass
class BoundingSphere(DecoderInterface):
    cx: int  # centre’s coordinate in x
    cy: int  # centre’s coordinate in y
    cz: int  # centre’s coordinate in z
    radius: int  # radius of the sphere
    unk: int  # unknown

    size = 10
    format = '3h 2H'


@dataclass
class Polygon():
    shape: int  # a triangle (8), or a quad (9)
    vertices: List[int]  # vertices (first is anchor, others in clockwise dir)
    texture_flipped: int  # index and horizontal flip
    texture_shape: int
    texture_index: int
    intensity: int
    shine: int
    opacity: int

    @staticmethod
    def decode(f):
        shape = read_uint16(f)
        if shape == 8:
            vertices = struct.unpack('3H', f.read(6))
        else:
            vertices = struct.unpack('4H', f.read(8))

        texture = read_uint16(f)
        attributes = struct.unpack('B', f.read(1))[0]
        f.read(1)  # unknown

        texture_flipped = (texture & 0X8000) >> 15
        texture_shape = (texture & 0X7000) >> 12
        assert texture_shape in {0, 2, 4, 6, 7}

        if shape == 8:
            texture_index = texture & 0X0FFF
        else:
            texture_index = texture
            if texture_flipped:
                texture_index = 0X10000 - texture_index

        intensity = (attributes & 0X7C) >> 2
        shine = (attributes & 0X02) >> 1
        opacity = attributes & 0X01

        return Polygon(shape, vertices, texture_flipped, texture_shape,
                         texture_index, intensity, shine, opacity)


@dataclass
class ShortVector3D(DecoderInterface):
    vx: int
    vy: int
    vz: int

    size = 6
    format = '3h'

    def __truediv__(self, x):
        self.vx /= x
        self.vy /= x
        self.vz /= x
        return self


@dataclass
class StateChanges(DecoderInterface):
    state_ID: int  # ID of the state of the next animation
    num_dispatches: int  # number of animation dispatches
    dispatches_index: int  # index in the dispatches table

    size = 6
    format = '3H'


@dataclass
class Dispatches(DecoderInterface):
    in_range: int  # [frame-in] where this range starts, inclusive
    out_range: int  # ]frame-out[ where this range stops, exclusive
    next_anim: int  # index of the next animation in the Animations_Table
    frame_in: int  # [frame-in] index of the next animation

    size = 8
    format = '4H'


@dataclass
class Animation(DecoderInterface):
    keyframe_offset: int  # offset in Keyframes_Data_Package
    frame_duration: int  # engine ticks per frame
    keyframe_size: int  # size of the keyframe record, in words
    state_ID: int  # ID of the state of this animation
    unknown1: int  # unknown 2 bytes.
    speed: int  # ground speed
    acceleration: int  # easy-in and easy-out for the speed
    unknown2: int  # unknown 8 bytes
    frame_start: int  # [ frame-in ] index of this animation
    frame_end: int  # [ frame-out ] index of this animation
    next_animation: int  # index of the default next animation
    frame_in: int  # [ frame-in ] index of the next animation
    num_state_changes: int  # number of animation transitions
    changes_index: int  # index in State_Changes_Table
    num_commands: int  # number of commands
    commands_offset: int  # offset in Commands_Data_Package

    size = 40
    format = 'I 2B H 2h i q 8H'

    def __post_init__(self):
        self.acceleration_as_float = self.acceleration / 65536
        self.number_of_frames = self.frame_end - self.frame_start + 1


@dataclass
class Keyframes:
    bb1: ShortVector3D
    bb2: ShortVector3D
    off: ShortVector3D
    rotations: List[int]

    @staticmethod
    def decode(f, numMeshes, keyframeSize):
        bb1 = ShortVector3D.decode(f)
        bb2 = ShortVector3D.decode(f)
        off = ShortVector3D.decode(f)
        wordsLeft = keyframeSize - 9
        rotations = []
        for _ in range(numMeshes):
            angleSet = read_uint16(f)
            wordsLeft -= 1
            nextWord = 0
            axes = angleSet & 0XC000
            if axes == 0X0000:
                nextWord = read_uint16(f)
                wordsLeft -= 1
                angleSet = angleSet * 0X10000 + nextWord
                rotz = (angleSet & 0X3FF) * 2 * pi / 1024
                angleSet >>= 10
                roty = (angleSet & 0X3FF) * 2 * pi / 1024
                angleSet >>= 10
                rotx = (angleSet & 0X3FF) * 2 * pi / 1024
            elif axes == 0X4000:
                roty = rotz = 0.0
                rotx = (angleSet & 0X3FFF) * 2 * pi / 4096
            elif axes == 0X8000:
                rotx = rotz = 0.0
                roty = (angleSet & 0X3FFF) * 2 * pi / 4096
            elif axes == 0XC000:
                rotx = roty = 0.0
                rotz = (angleSet & 0X3FFF) * 2 * pi / 4096
            else:
                assert False

            rotations.append((rotx, roty, rotz))

        f.read(wordsLeft * 2)
        return Keyframes(bb1, bb2, off, rotations)


@dataclass
class Movable(DecoderInterface):
    obj_ID: int  # unique ID number for this Movable
    num_pointers: int  # number of mesh pointers
    pointers_index: int  # index in the pointers list
    links_index: int  # index of the pivot point links package
    keyframes_offset: int  # offset in the keyframes package
    anims_index: int  # index in the animations table

    size = 18
    format = 'I 2H 2I h'


@dataclass
class Static(DecoderInterface):
    obj_ID: int  # unique ID number for this Static.
    pointers_index: int  # index of a pointer to the mesh.
    vx1: int  # coordinate, visibility bounding box
    vx2: int
    vy1: int
    vy2: int
    vz1: int
    vz2: int
    cx1: int  # coordinate, collision bounding box
    cx2: int
    cy1: int
    cy2: int
    cz1: int
    cz2: int
    flags: int  # some unknown flags

    size = 32
    format = 'I H 12h H'
