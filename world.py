import math
import pygame


class Tile:
    def __init__(self, index, position, item_id):
        self.tile_index = index
        self.size = 40, 40
        self.position = position[0] * self.size[0], position[1] * self.size[1]
        self.health = 1
        self.item_drop = item_id

    def check_collide(self, position, size, check_edges):
        right = self.position[0] - (position[0] + size[0])
        bottom = self.position[1] - (position[1] + size[1])

        left = (self.position[0] + self.size[0]) - position[0]
        top = (self.position[1] + self.size[1]) - position[1]

        if right >= 0:
            return -1

        if left <= 0:
            return -1

        if bottom >= 0:
            return -1

        if top <= 0:
            return -1

        edges = [right, bottom, left, top]
        collided_edge = 0
        collided_factor = 1

        for edge in range(len(edges)):
            if check_edges[edge] is False:
                continue

            factor = 1
            if edge >= 2:
                factor = -1

            if edges[edge] * factor >= edges[collided_edge] * collided_factor:
                collided_edge = edge
                collided_factor = factor

        return collided_edge

    def collide(self, player, check_edges):
        below_pos = player.position[0], player.position[1] + 1
        on_floor = self.check_collide(below_pos, player.size, check_edges)
        if on_floor == 1:
            vertical_dist = self.position[1] - player.last_floor_height
            if vertical_dist >= 200:
                damage = vertical_dist / 1250
                player.damage(damage)

            player.on_floor = True
            player.last_floor_height = self.position[1]

        collide = self.check_collide(player.position, player.size, check_edges)
        if collide == -1:
            return

        if collide == 0:
            player.position = self.position[0] - player.size[0], player.position[1]
            player.velocity = 0, player.velocity[1]
        elif collide == 1:
            player.position = player.position[0], self.position[1] - player.size[1]
            player.velocity = player.velocity[0], 0
        elif collide == 2:
            player.position = self.position[0] + self.size[0], player.position[1]
            player.velocity = 0, player.velocity[1]
        elif collide == 3:
            player.position = player.position[0], self.position[1] + self.size[1]
            player.velocity = player.velocity[0], 0
            player.is_jumping = False


class TileGroup:
    def __init__(self):
        self.tile_sheet = pygame.image.load("./assets/tiles.png").convert_alpha()
        self._tiles = []
        self.height_map = []
        self.size = 200, 200
        self.build_tile_map()

    def init(self, size):
        self.size = size
        self.build_tile_map()

    def build_tile_map(self):
        self._tiles = []
        row = [None] * self.size[0]
        for i in range(self.size[1]):
            self._tiles.append(row.copy())

    def set_tile(self, position, tile, send_message):
        import main

        self._tiles[position[1]][position[0]] = tile
        if send_message:
            main.mainManager.multiplayerHandler.update_tile(position, tile)

    def get_tile(self, position):
        if position[1] < 0 or position[1] >= len(self._tiles):
            return None
        if position[0] < 0 or position[0] >= len(self._tiles[position[1]]):
            return None

        return self._tiles[position[1]][position[0]]

    def get_biome(self, x, y):
        import main

        h = math.ceil(x)
        if len(self.height_map) > h and self.height_map[h] + 10 < y:
            return 4

        return main.mainManager.local_player.biome
