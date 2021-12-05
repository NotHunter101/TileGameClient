import pygame
import math


def load_image_scaled(path, scale):
    image = pygame.image.load(path).convert_alpha()
    image_size = image.get_size()
    image_size_scaled = image_size[0] * scale, image_size[1] * scale
    image = pygame.transform.scale(image, image_size_scaled)

    return image


def draw_text_with_outline(text, pos, font, surface):
    rendered = font.render(text, True, pygame.Color(225, 225, 225))
    out_rendered = font.render(text, True, pygame.Color(15, 15, 15))
    pos = pos[0] - rendered.get_size()[0] * .5, pos[1] - rendered.get_size()[1] * .5

    outline_parts = [ (pos[0] - 1, pos[1] - 1),
                      (pos[0] + 1, pos[1] - 1),
                      (pos[0] - 1, pos[1] + 1),
                      (pos[0] + 1, pos[1] + 1) ]

    for part in outline_parts:
        surface.blit(out_rendered, part)

    surface.blit(rendered, pos)


class UIHandler:
    def __init__(self):
        import inventory
        self.health_bar = HealthBar()
        self.backgrounds = BackgroundHandler()
        self.inventory = inventory.InventoryUI()


class HealthBar:
    def __init__(self):
        import main

        main.mainManager.all_behaviors.append(self)

        self.border = pygame.image.load("./assets/ui/health/border.png").convert_alpha()
        self.fill = pygame.image.load("./assets/ui/health/fill.png").convert_alpha()

    def draw(self, surface):
        import main

        surface.blit(self.border, (925, 25))
        surface.blit(self.fill, (925, 25), (0, 0, main.mainManager.local_player.health * 250, 26))


class BackgroundHandler:
    def __init__(self):
        import main

        main.mainManager.all_behaviors.append(self)

        self.biomes = [ pygame.image.load("./assets/backgrounds/forest.png").convert_alpha(),
                        pygame.image.load("./assets/backgrounds/sand.png").convert_alpha(),
                        pygame.image.load("./assets/backgrounds/snow.png").convert_alpha(),
                        pygame.image.load("./assets/backgrounds/jungle.png").convert_alpha(),
                        pygame.image.load("./assets/backgrounds/cave.png").convert_alpha() ]

        self.current_biome = 0
        self.last_biome = 0
        self.last_switch = 0
        self.background_surface = pygame.Surface((1200 / 8, 720 / 8), pygame.SRCALPHA)

    def update(self, delta):
        import main

        alpha = min(255, self.last_switch * 255 * 2)
        self.biomes[self.current_biome].set_alpha(alpha)

        if alpha != 255:
            self.background_surface.blit(self.biomes[self.last_biome], (0, 0))
        self.background_surface.blit(self.biomes[self.current_biome], (0, 0))

        self.last_switch += delta
        biome = main.mainManager.tiles.get_biome(main.mainManager.local_player.position[0] / 40, main.mainManager.local_player.position[1] / 40)

        if self.current_biome != math.floor(biome):
            self.last_switch = 0
            self.last_biome = self.current_biome
            self.biomes[self.last_biome].set_alpha(255)
            self.current_biome = math.floor(biome)
