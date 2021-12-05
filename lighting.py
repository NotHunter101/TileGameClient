import math
import numpy
import pygame
import ctypes
import os


class LightingManager:
    def __init__(self):
        import main

        main.mainManager.all_behaviors.append(self)

        self.light_map_size_extra = 10, 10
        self.light_map_size = main.mainManager.tile_count[0] + self.light_map_size_extra[0], main.mainManager.tile_count[1] + self.light_map_size_extra[1]
        self.size_range = range(self.light_map_size[0]), range(self.light_map_size[1])

        self.lighting_surface_size = 1200 + 40 + self.light_map_size_extra[0] * 40, 720 + 40 + self.light_map_size_extra[1] * 40
        self.lighting_surface = pygame.Surface(self.lighting_surface_size, pygame.SRCALPHA).convert_alpha()
        self.lighting_surface.fill((0, 0, 0, 225))
        self.light_map = [0] * (self.light_map_size[0] * self.light_map_size[1])

        self.last_cam_pos = main.mainManager.local_player.camera.position[0] % 40, main.mainManager.local_player.camera.position[1] % 40

        # Let's cheat a little bit and use a custom C++ library to speed up the shadow processing
        os.add_dll_directory(os.getcwd() + "\\dependencies")
        self.lighting_dll = ctypes.WinDLL('./dependencies/LightingHelper.dll')
        self.lighting_dll.generate_lightmap.restype = numpy.ctypeslib.ndpointer(dtype=ctypes.c_int, shape=((self.light_map_size[0] * 40) * (self.light_map_size[1] * 40)))

    def get_light_at_pos(self, x, y):
        return self.light_map[(y * self.light_map_size[0]) + x]

    def early_update(self, delta):
        import main

        if main.mainManager.get_key_state(pygame.K_q).pressed:
            return

        self.last_cam_pos = main.mainManager.local_player.camera.position
        camera_pos = main.mainManager.local_player.camera.position
        extra_size = self.light_map_size_extra[0], self.light_map_size_extra[1]
        camera_by_40 = ctypes.c_float(math.floor(camera_pos[0] / 40) - extra_size[0] * .5), ctypes.c_float(math.floor(camera_pos[1] / 40) - extra_size[1] * .5)
        camera_rem = main.mainManager.local_player.camera.position[0] % 40, main.mainManager.local_player.camera.position[1] % 40

        # Pass a bunch of stuff to our C++ library so it can process the shadows for us
        tile_map = (ctypes.c_bool * len(main.mainManager.active_tiles_map))(*main.mainManager.active_tiles_map)
        self.light_map = self.lighting_dll.generate_lightmap(self.light_map_size[0], self.light_map_size[1], tile_map,
                                                             main.mainManager.tile_count[0] + 10, main.mainManager.tile_count[1] + 10, camera_by_40[0],
                                                             camera_by_40[1], ctypes.c_float(camera_rem[0]),
                                                             ctypes.c_float(camera_rem[1]), extra_size[0], extra_size[1])

        # Open a debug "Pixel Array" which lets us apply changes to our lighting
        # surface with less of a performance hit than repeated blit calls
        pixels = pygame.PixelArray(self.lighting_surface)

        for x in self.size_range[0]:
            pos_x = int(x * 40 - camera_rem[0]) - (extra_size[0] * 12)

            if pos_x + 40 < 0 or pos_x + 40 > 1199 + (extra_size[0] * 40):
                continue

            for y in self.size_range[1]:
                pos_y = int(y * 40 - camera_rem[1]) - (extra_size[1] * 12)

                if pos_y < 0 or pos_y > 719 + (extra_size[1] * 40):
                    continue

                tile_light = (5 - self.get_light_at_pos(x, y)) / 5
                alpha = int(tile_light * 240)
                dist = int(1199 + (extra_size[0] * 40) - pos_x), int(719 + (extra_size[1] * 40) - pos_y)
                pixels[pos_x:pos_x + min(40, dist[0]), pos_y:pos_y + min(40, dist[1])] = pygame.Color(5, 5, 5, alpha)

        # Release our debug "Pixel Array" and unlock the lighting surface
        del pixels

    def early_draw(self, surface):
        import main

        if main.mainManager.get_key_state(pygame.K_q).pressed:
            return

        # Calculate the difference between the camera's position the last time the shadows were updated and now
        camera_diff = self.last_cam_pos[0] - main.mainManager.local_player.camera.position[0], self.last_cam_pos[1] - main.mainManager.local_player.camera.position[1]
        # Blit the shadow surface onto the screen using the calculated difference to negate/remove jitter
        # and shakiness caused by a mismatch in draw speed and shadow update speed
        surface.blit(self.lighting_surface, (camera_diff[0] - 80, camera_diff[1] - 80, 1200, 720))
