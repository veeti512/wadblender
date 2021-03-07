# see https://blackpawn.com/texts/lightmaps/

class Rect:
    def __init__(self, left, top, right, bottom):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

    def width(self):
        return self.right - self.left + 1

    def height(self):
        return self.bottom - self.top + 1


class Node:
    def __init__(self):
        self.left = None
        self.right = None
        self.rect = None
        self.id = -1

    def insert(self, img):
        if self.left or self.right:
            node = None
            if self.left:
                node = self.left.insert(img)

            return node if node else self.right.insert(img)
        else:
            if self.id != -1:
                return None

            if img.width() > self.rect.width() or img.height() > self.rect.height():
                return None
            elif img.width() == self.rect.width() and img.height() == self.rect.height():
                self.id = img.id
                return self
            else:
                self.left = Node()
                self.right = Node()

                dw = self.rect.width() - img.width()
                dh = self.rect.height() - img.height()

                r = self.rect
                if dw > dh:
                    self.left.rect = Rect(r.left, r.top, r.left+img.width() - 1, r.bottom)
                    self.right.rect = Rect(r.left + img.width(), r.top, r.right, r.bottom)
                else:
                    self.left.rect = Rect(r.left, r.top, r.right, r.top + img.height() - 1)
                    self.right.rect = Rect(r.left, r.top + img.height(), r.right, r.bottom)

                return self.left.insert(img)


def pack(sizes, max_height=2048):
    root = Node()
    root.rect = Rect(0, 0, 255, max_height-1)
    res = []
    height = -1
    width = -1
    for i, sz in enumerate(sizes):
        w, h = sz
        img = Rect(0, 0, w - 1, h - 1)
        img.id = i
        res_node = root.insert(img)
        if res_node is None:
            return None

        rect = res_node.rect
        x, y = rect.left, rect.top
        height = max(height, y + h)
        width = max(width, x + w)
        res.append((x, y))

    return res, width, height


def pack_object_textures(meshes, texture_path):
    # load wad texture map
    import numpy as np
    from PIL import Image
    image = Image.open(texture_path)
    wad_texture_map = np.asarray(image)
    map_height = wad_texture_map.shape[0]

    # get distinct texture samples
    texture_rects = set()
    for mesh in meshes:
        texture_rects |= {(poly.x, poly.y, poly.tex_width, poly.tex_height) 
                           for poly in mesh.polygons}

    # sort by area
    texture_rects = sorted(texture_rects, key=lambda x: x[2] * x[3], reverse=True)

    cur_pos = [(e[0], e[1]) for e in texture_rects]  # top left corner
    tex_sizes = [(e[2], e[3]) for e in texture_rects]  # width and height

    # binary search to find smallest height (width is fixed to 256)
    lo, hi = 0, map_height
    new_pos = None
    while lo < hi:
        mid = (lo + hi) // 2
        cur = pack(tex_sizes, max_height=mid)
        if cur:
            new_pos, new_map_width, new_map_height = cur
            hi = mid
        else:
            lo = mid + 1
    
    # build new texture map
    new_texture_map = np.zeros((new_map_height, new_map_width, 4), dtype='uint8')
    new_texture_map[:,:, 3] = 1  # alpha channel
    for i in range(len(tex_sizes)):
        w, h = tex_sizes[i]
        x0, y0 = cur_pos[i]
        x, y = new_pos[i]
        new_texture_map[y:y+h, x:x+w, :] = wad_texture_map[y0:y0+h, x0:x0+w, :]

    # conversion table from old to new uvs
    uvtable = {}
    for i in range(len(tex_sizes)):
        w, h = tex_sizes[i]
        x0, y0 = cur_pos[i]
        x, y = new_pos[i]
        uvtable[(x0, y0, w, h)] = (x, y)

    return uvtable, new_texture_map
