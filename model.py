from collections import namedtuple, defaultdict
from dataclasses import dataclass
from typing import List, Tuple, Dict

Point = namedtuple('Point', ('x', 'y', 'z'))
Dispatch = namedtuple('Dispatch', ('inRange', 'outRange', 'nextAnim', 'frameIn'))


@dataclass
class Polygon:
    face: List[Tuple[int]]
    tbox: List[Tuple[float]]
    order: int
    intensity: int  # [0..31]
    shine: int  # on/off 1/0
    opacity: int

    """
    If opacity = 0, the texture is considered opaque ao =  the
    magenta colour is used to mark pixels that are to be made fully transparent.

    If opacity = 1, then colours are treated as translucent, after
    converting the magenta colour, if any, to black.
    """


@dataclass
class Mesh:
    vertices: List[Point]
    polygons: List[Polygon]
    normals: List[Point]
    boundingSphereCenter: Point
    boundingSphereRadius: int
    shades: List[int]


@dataclass
class Static:
    idx: int
    mesh: Mesh


@dataclass
class Keyframe:
    offset: Tuple[int]
    rotations: List[Tuple[float]]
    bb1: Tuple[int]
    bb2: Tuple[int]


@dataclass
class Animation:
    stateID: int
    keyFrames: List[Keyframe]
    stateChanges: Dict
    commands: List[Tuple[int]]
    frameDuration: int
    speed: int
    acceleration: int
    frameStart: int
    frameEnd: int
    frameIn: int
    nextAnimation: int


@dataclass
class Movable:
    idx: int
    meshes: List[Mesh]
    joints: List[List[int]]
    animations: List[Animation]


@dataclass
class Wad:
    version: int
    statics: List[Static]
    mapwidth: int
    mapheight: int
    textureMap: List[float]
    movables: List[Movable]
