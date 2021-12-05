import sys
import pygame
import math
import main


class KeyState:
    def __init__(self):
        # state:
        # 0 = not pushed,
        # 1 = just pushed,
        # 2 = just released,

        self.state = 0
        self.pressed = False


class MainManager:
    def __init__(self):
        pygame.init()

        self.active_tiles = []
        self.all_behaviors = []
        self.keymap = {}
        self.mouse_map = []

        self.tile_count = math.ceil(1200 / 40) + 1, math.ceil(720 / 40) + 1
        row = [None] * (self.tile_count[0] + 10)
        for i in range(self.tile_count[1] + 10):
            self.active_tiles.append(row.copy())

        self.active_tiles_map = [False] * ((self.tile_count[0] + 10) * (self.tile_count[1] + 10))
        self.screen = pygame.display.set_mode((1200, 720), pygame.SRCALPHA)

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Calibri', 30, True)
        self.tiles = None
        self.players = {}
        self.local_player = None

        self.uiHandler = None
        self.lightingHandler = None
        self.multiplayerHandler = None
        self.delta = 0
        self.timer = 0

        for i in range(2):
            self.mouse_map.append(KeyState())

        self.big_sheet = pygame.Surface((40 * 13, 40))
        self.tile_cracks = [pygame.image.load("./assets/tile_cracks/cracked-0.png").convert_alpha(),
                            pygame.image.load("./assets/tile_cracks/cracked-1.png").convert_alpha(),
                            pygame.image.load("./assets/tile_cracks/cracked-2.png").convert_alpha(),
                            pygame.image.load("./assets/tile_cracks/cracked-3.png").convert_alpha()]

        self.connected = False

    def connect(self):
        import multiplayer

        self.multiplayerHandler = multiplayer.MultiplayerHandler()

    def init(self, players, local_id):
        import game
        import world
        import lighting
        import ui
        import inventory

        inventory.item_sprites = []
        for item in inventory.items:
            inventory.item_sprites.append(pygame.image.load(item["path"]).convert_alpha())

        self.players = {}
        self.local_player = None

        print(players)

        for value in players:
            position = value["position"]["x"], value["position"]["y"]
            local = value["id"] == local_id
            player = game.Player(position, local)
            self.players[value["id"]] = player
            if local:
                self.local_player = player

        self.tiles = world.TileGroup()
        self.uiHandler = ui.UIHandler()
        self.lightingHandler = lighting.LightingManager()
        self.connected = True

        pygame.transform.scale(self.tiles.tile_sheet, (40 * 13, 40), self.big_sheet)

    def get_key_state(self, keycode):
        if keycode not in self.keymap.keys():
            self.keymap[keycode] = KeyState()

        return self.keymap[keycode]

    def get_mouse_state(self, button):
        return self.mouse_map[button]

    def update(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            pushed = pygame.mouse.get_pressed(3)
            for button in range(2):
                i = button
                if button == 1:
                    i = 2

                if self.mouse_map[button].pressed != pushed[i]:
                    self.mouse_map[button].pressed = pushed[i]

                    if self.mouse_map[button].pressed:
                        self.mouse_map[button].state = 1
                    else:
                        self.mouse_map[button].state = 2

            if hasattr(event, "key"):
                if event.key not in self.keymap.keys():
                    self.keymap[event.key] = KeyState()

                if event.type == pygame.KEYDOWN:
                    self.keymap[event.key].state = 1
                    self.keymap[event.key].pressed = True

                if event.type == pygame.KEYUP:
                    self.keymap[event.key].state = 2
                    self.keymap[event.key].pressed = False

        pygame.transform.scale(self.uiHandler.backgrounds.background_surface, (1200, 720), self.screen)

        camera_pos = self.local_player.camera.position
        camera_by_40 = math.floor(camera_pos[0] / 40) - 5, math.floor(camera_pos[1] / 40) - 5
        camera_rem = camera_pos[0] % 40, camera_pos[1] % 40

        for x in range(self.tile_count[0] + 10):
            for y in range(self.tile_count[1] + 10):
                tile_position = int(camera_by_40[0] + x), int(camera_by_40[1] + y)
                tile = self.tiles.get_tile(tile_position)
                self.active_tiles[y][x] = tile
                self.active_tiles_map[(y * (self.tile_count[0] + 10)) + x] = tile is not None

                if tile is None:
                    continue

                tile_screen_position = (x - 5) * 40 - camera_rem[0], (y - 5) * 40 - camera_rem[1]
                x_offset = tile.tile_index * 40
                rect = (x_offset, 0, 40, 40)
                crack_index = -1

                if tile.health < .8:
                    crack_index = 0
                if tile.health < .6:
                    crack_index = 1
                if tile.health < .4:
                    crack_index = 2
                if tile.health < .2:
                    crack_index = 3

                try:
                    self.screen.blit(self.big_sheet, tile_screen_position, rect)
                    if crack_index != -1:
                        self.screen.blit(self.tile_cracks[crack_index], tile_screen_position)
                except:
                    print("CRASH REPORT:")
                    print()
                    print(tile_screen_position)
                    print(x_offset)
                    print(rect)

        for behavior in self.all_behaviors:
            if hasattr(behavior, "early_draw"):
                behavior.early_draw(self.screen)

        for behavior in self.all_behaviors:
            if hasattr(behavior, "draw"):
                behavior.draw(self.screen)

        for behavior in self.all_behaviors:
            if self.timer >= .0167777 and hasattr(behavior, "early_update"):
                behavior.early_update(self.timer)

        for behavior in self.all_behaviors:
            if self.timer >= .0167777 and hasattr(behavior, "update"):
                behavior.update(self.timer)

        if self.timer >= .0167777:
            self.timer = 0

            for key in self.keymap:
                self.keymap[key].state = 0

            for mouse in self.mouse_map:
                mouse.state = 0

        delta = self.clock.tick() / 1000
        self.timer += delta

        fpsText = self.font.render('FPS: ' + str(math.floor(self.clock.get_fps())), False, (255, 0, 0))
        self.screen.blit(fpsText, (25, 25))
        pygame.display.update((0, 0, 1200, 720))


if __name__ == "main":
    mainManager = MainManager()
    mainManager.connect()

    while True:
        if mainManager.connected:
            mainManager.update()
        else:
            mainManager.multiplayerHandler.update(0)
