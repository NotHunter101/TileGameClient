import pygame
import json

file = open('./items.json', mode='r')
data = file.read()
file.close()
items = json.loads(data)
item_sprites = []


class InventoryUI:
    def __init__(self):
        import ui
        import main

        main.mainManager.all_behaviors.append(self)
        self.background = ui.load_image_scaled("./assets/ui/inventory/background.png", 5)
        self.border = ui.load_image_scaled("./assets/ui/inventory/slot.png", 5)
        self.border_s = ui.load_image_scaled("./assets/ui/inventory/slot_small.png", 5)
        self.border_b = ui.load_image_scaled("./assets/ui/inventory/slot_big.png", 5)
        self.border_h = ui.load_image_scaled("./assets/ui/inventory/slot_highlight.png", 5)
        self.tooltip_box = ui.load_image_scaled("./assets/ui/inventory/tooltip.png", 1)
        self.background_size = self.background.get_size()
        self.inventory_open = False
        self.selected_slot = 0
        self.content_font = pygame.font.SysFont("Calibri", 18, True)

    def update(self, delta):
        import main

        if main.mainManager.get_key_state(pygame.K_ESCAPE).state == 1:
            self.inventory_open = not self.inventory_open

        background_pos = 600 - self.background_size[0] * .5, 360 - self.background_size[1] * .5
        mouse_pos = pygame.mouse.get_pos()
        left_clicked = main.mainManager.get_mouse_state(0).state == 1
        right_clicked = main.mainManager.get_mouse_state(1).state == 1

        for i in range(6):
            key = pygame.K_1 + i
            if main.mainManager.get_key_state(key).state == 1:
                self.selected_slot = i
                main.mainManager.local_player.selected_item = i

        if self.inventory_open:
            for x in range(6):
                for y in range(3):
                    item_index = (y * 6) + x
                    item = main.mainManager.local_player.items[item_index]

                    border_size = self.border.get_size()
                    pos = 175 + (background_pos[0] + x * 60), 25 + (background_pos[1] + y * 60)
                    diff = mouse_pos[0] - pos[0], mouse_pos[1] - pos[1]
                    hovered = 0 <= diff[0] < border_size[0] and 0 <= diff[1] < border_size[1]

                    if hovered and right_clicked:
                        if item is not None:
                            if main.mainManager.local_player.mouse_item is None:
                                item.count -= 1
                                main.mainManager.local_player.mouse_item = Item(item.id, 1)
                                if item.count <= 0:
                                    main.mainManager.local_player.items[item_index] = None
                            elif main.mainManager.local_player.mouse_item.id == item.id:
                                item.count -= 1
                                main.mainManager.local_player.mouse_item.count += 1
                                if item.count <= 0:
                                    main.mainManager.local_player.items[item_index] = None

                    if hovered and left_clicked:
                        if item is not None and main.mainManager.local_player.mouse_item is not None:
                            if main.mainManager.local_player.mouse_item.id == item.id and item.stackable:
                                item.count += main.mainManager.local_player.mouse_item.count
                                main.mainManager.local_player.mouse_item = None
                                return

                        old_mouse_item = main.mainManager.local_player.mouse_item
                        main.mainManager.local_player.mouse_item = item
                        main.mainManager.local_player.items[item_index] = old_mouse_item
                        main.mainManager.local_player.selected_item = self.selected_slot

    def draw(self, surface):
        import ui
        import main

        if not self.inventory_open:
            for i in range(6):
                sprite = self.border

                if self.selected_slot == i:
                    sprite = self.border_h

                border_size = sprite.get_size()
                pos = 420 + (i * 60), 650
                surface.blit(sprite, pos)

                item = main.mainManager.local_player.items[i]
                if item is not None:
                    offset = pos[0] + (border_size[0] * .5 - 15), pos[1] + (border_size[1] * .5 - 15)
                    surface.blit(item.sprite, offset)
                    if item.count == 1:
                        continue

                    ui.draw_text_with_outline(str(item.count), offset, self.content_font, surface)

            return
            
        background_pos = 600 - self.background_size[0] * .5, 360 - self.background_size[1] * .5
        surface.blit(self.background, background_pos)
        surface.blit(self.border_b, (background_pos[0] + 22, background_pos[1] + 26))

        mouse_pos = pygame.mouse.get_pos()

        for x in range(4):
            pos = 103 + (background_pos[0]), 26 + (background_pos[1] + x * 43)
            surface.blit(self.border_s, pos)
        
        for x in range(6):
            for y in range(3):
                sprite = self.border

                if y == 0 and self.selected_slot == x:
                    sprite = self.border_h

                border_size = sprite.get_size()
                pos = 175 + (background_pos[0] + x * 60), 25 + (background_pos[1] + y * 60)
                diff = mouse_pos[0] - pos[0], mouse_pos[1] - pos[1]
                surface.blit(sprite, pos)

                item_index = (y * 6) + x
                item = main.mainManager.local_player.items[item_index]

                if item is not None:
                    offset = pos[0] + (border_size[0] * .5 - 15), pos[1] + (border_size[1] * .5 - 15)
                    surface.blit(item.sprite, offset)
                    if item.count == 1:
                        continue

                    ui.draw_text_with_outline(str(item.count), offset, self.content_font, surface)

        if main.mainManager.local_player.mouse_item is not None:
            centered_mouse_pos = mouse_pos[0] - 15, mouse_pos[1] - 15
            surface.blit(main.mainManager.local_player.mouse_item.sprite, centered_mouse_pos)
            if main.mainManager.local_player.mouse_item.count != 1:
                ui.draw_text_with_outline(str(main.mainManager.local_player.mouse_item.count), centered_mouse_pos, self.content_font, surface)

    def draw_tooltip_box(self, surface):
        mouse = pygame.mouse.get_pos()
        surface.blit(self.tooltip_box, mouse)


class Item:
    def __init__(self, id, count):
        if len(items) <= id:
            print(id + " is an invalid item ID.")
            return
        
        item = items[id]
        self.id = id
        self.name = item["name"]
        self.type = item["type"]
        self.stackable = item["stackable"]
        self.sprite = item_sprites[id]
        self.count = count

        if self.type == "axe" or self.type == "pickaxe":
            self.power = item["power"]
        elif self.type == "block":
            self.block_id = item["block_id"]
