import math
import pygame


class Camera:
    def __init__(self, position):
        import main

        main.mainManager.all_behaviors.append(self)

        self.position = position
        self.zoom = 1

    def update(self, delta):
        import main

        if main.mainManager.get_key_state(pygame.K_LCTRL).pressed:
            self.zoom += 10
        elif main.mainManager.get_key_state(pygame.K_LSHIFT).pressed:
            self.zoom -= 10


class Player:
    def __init__(self, position, local):
        import main
        import inventory

        main.mainManager.all_behaviors.append(self)

        self.position = position
        self.draw_pos = 0, 0
        self.lerp_counter = 0
        self.velocity = 0, 0
        self.local = local
        self.camera = Camera((0, 0))
        self.size = 50, 90

        self.is_jumping = False
        self.jump_timer = 0
        self.on_floor = False
        self.last_floor_height = self.position[1] + self.size[1]
        self.health = 1
        self.biome = 0
        
        self.items = [None] * 18
        self.armor = [None] * 4
        self.mouse_item = None
        self.hovered_block = None
        self.selected_item = 0
        self.hover_guide = pygame.image.load("./assets/guide.png").convert_alpha()

        self.items[0] = inventory.Item(0, 20)
        self.items[1] = inventory.Item(9, 1)

    def give_item(self, id, count):
        import inventory

        for item in self.items:
            if item is not None and item.id == id:
                item.count += count
                return

        for item in range(len(self.items)):
            if self.items[item] is None:
                self.items[item] = inventory.Item(id, count)
                return

    def add_vel(self, vel):
        self.velocity = self.velocity[0] + vel[0], self.velocity[1] + vel[1]

    def damage(self, damage):
        self.health -= damage

    def update(self, delta):
        import world
        import main

        if not self.local:
            dist = math.dist(self.draw_pos, self.position)
            if dist != 0:
                self.lerp_counter += .1667
                lerp_factor = min(self.lerp_counter, 1)
                self.draw_pos = tuple(pygame.math.Vector2(self.draw_pos).lerp(self.position, lerp_factor))
            return

        # -- DEBUG --

        '''if main.mainManager.get_key_state(pygame.K_x).state == 1:
            mouse_screen = pygame.mouse.get_pos()
            mouse_pos = self.camera.position[0] + mouse_screen[0], self.camera.position[1] + mouse_screen[1]
            self.position = mouse_pos
            self.velocity = 0, 0
            self.last_floor_height = self.position[1] + self.size[1]

        if main.mainManager.get_key_state(pygame.K_z).pressed:
            mouse_screen = pygame.mouse.get_pos()
            mouse_pos = self.camera.position[0] + mouse_screen[0], self.camera.position[1] + mouse_screen[1]
            mouse_tile = math.floor(mouse_pos[0] / 40), math.floor(mouse_pos[1] / 40)
            main.mainManager.tiles.set_tile(mouse_tile, world.Tile(0, mouse_tile, 0), True)
            
        if not main.mainManager.get_key_state(pygame.K_c).pressed:
            size = main.mainManager.tiles.size
            self.camera.position = min(max(0, self.position[0] - 600), (size[0] * 40) - 1200), min(max(0, self.position[1] - 360), (size[1] * 40) - 720)'''

        # -- DEBUG --

        selected_item = self.items[self.selected_item]
        if self.hovered_block is not None and selected_item is not None:
            tile = main.mainManager.tiles.get_tile(self.hovered_block)

            if main.mainManager.get_mouse_state(0).pressed and tile is not None:
                if selected_item.type == "pickaxe":
                    tile.health -= (1 / 30) * selected_item.power

                    if tile.health < 0:
                        self.give_item(tile.item_drop, 1)
                        main.mainManager.tiles.set_tile(self.hovered_block, None, True)
            elif tile is not None:
                tile.health = 1

            if main.mainManager.get_mouse_state(1).pressed and tile is None:
                if selected_item.type == "block":
                    new_tile = world.Tile(selected_item.block_id, self.hovered_block, selected_item.id)
                    main.mainManager.tiles.set_tile(self.hovered_block, new_tile, True)
                    selected_item.count -= 1

                    if selected_item.count <= 0:
                        self.items[self.selected_item] = None

        self.health += 1 / (60 * 45)
        self.health = max(0, min(1, self.health))

        dist = math.dist(self.velocity, (0, 0))
        if dist != 0:
            lerp_factor = min(.2 / dist, 1)
            self.velocity = tuple(pygame.math.Vector2(self.velocity).lerp(pygame.math.Vector2(0, 0), lerp_factor))

        running_speed = 7
        running_acceleration = .375

        if main.mainManager.get_key_state(pygame.K_d).pressed:
            if self.velocity[0] < running_speed:
                self.add_vel((running_acceleration, 0))

        if main.mainManager.get_key_state(pygame.K_a).pressed:
            if self.velocity[0] > -running_speed:
                self.add_vel((-running_acceleration, 0))

        if main.mainManager.get_key_state(pygame.K_SPACE).state == 2 or self.jump_timer >= .5:
            self.is_jumping = False

        if main.mainManager.get_key_state(pygame.K_SPACE).state == 1:
            if self.on_floor:
                self.is_jumping = True
                self.jump_timer = 0

        if main.mainManager.get_key_state(pygame.K_SPACE).pressed and self.is_jumping:
            jump_timer_new = self.jump_timer + 1
            decelerate_factor = 1 - (jump_timer_new / math.pow(jump_timer_new, 10))

            self.add_vel((0, (-2.25 + (decelerate_factor * 2.25))))
            self.jump_timer += delta

        if self.on_floor is False:
            self.velocity = self.velocity[0], min(self.velocity[1] + .5, 17.5)
        elif self.velocity[1] > 0:
            self.velocity = self.velocity[0], 0

        self.position = self.position[0] + self.velocity[0], self.position[1] + self.velocity[1]

        size = main.mainManager.tiles.size
        self.camera.position = min(max(0, self.position[0] - 600), (size[0] * 40) - 1200), min(
            max(0, self.position[1] - 360), (size[1] * 40) - 720)

        tile_count = 3, 4
        camera_by_40 = math.ceil(self.position[0] / 40) - 1, math.ceil(self.position[1] / 40) - 1

        self.on_floor = False
        for x in range(tile_count[0]):
            for y in range(tile_count[1]):
                tile_position = int(camera_by_40[0] + x), int(camera_by_40[1] + y)
                tile = main.mainManager.tiles.get_tile(tile_position)

                if tile is None:
                    continue

                edge_tiles = [(tile_position[0] - 1, tile_position[1]), (tile_position[0], tile_position[1] - 1),
                              (tile_position[0] + 1, tile_position[1]), (tile_position[0], tile_position[1] + 1)]
                check_edges = [True, True, True, True]

                for edge in range(len(edge_tiles)):
                    if main.mainManager.tiles.get_tile(edge_tiles[edge]) is not None:
                        check_edges[edge] = False

                if any(check_edges):
                    tile.collide(self, check_edges)

    def draw(self, surface):
        import main

        if self.local:
            old_hovered_block = self.hovered_block
            self.hovered_block = None

            camera_pos = self.camera.position
            mouse_screen_pos = pygame.mouse.get_pos()
            tile_pos = math.floor((mouse_screen_pos[0] + camera_pos[0]) / 40), math.floor((mouse_screen_pos[1] + camera_pos[1]) / 40)
            tile_world_pos = tile_pos[0] * 40, tile_pos[1] * 40
            player_pos = self.position[0] + self.size[0] * .5, self.position[1] + self.size[1] * .5
            dist = math.dist(player_pos, tile_world_pos)

            if dist < 5 * 40:
                rect_pos = tile_world_pos[0] - camera_pos[0], tile_world_pos[1] - camera_pos[1]
                surface.blit(self.hover_guide, rect_pos)
                self.hovered_block = tile_pos

            if old_hovered_block != self.hovered_block and old_hovered_block is not None:
                tile = main.mainManager.tiles.get_tile(old_hovered_block)
                if tile is not None:
                    tile.health = 1

            self.draw_pos = self.position

        target = self.draw_pos[0] - main.mainManager.local_player.camera.position[0], self.draw_pos[1] - main.mainManager.local_player.camera.position[1]
        pygame.draw.rect(surface, (255, 0, 0), pygame.Rect(target, self.size))
