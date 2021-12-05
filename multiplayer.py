import websocket
import threading
import json


class MultiplayerHandler:
    def __init__(self):
        import main
        main.mainManager.all_behaviors.append(self)

        self.open = False
        self.socket = websocket.WebSocketApp("ws://127.0.0.1:5000", on_message=self.on_message)
        self.socket.on_open = self.handle_open
        self.queue = []
        self.timer = 0

        wst = threading.Thread(target=self.socket.run_forever)
        wst.daemon = True
        wst.start()

    def handle_open(self, ws):
        self.open = True

    def update_player_pos(self, pos):
        if not self.open:
            return

        msg = Message()
        msg.type = "SetPosition"
        msg.position = pos
        self.socket.send(json.dumps(msg, default=lambda o: o.__dict__))

    def update_tile(self, pos, tile):
        if not self.open:
            return

        msg = Message()
        msg.type = "SetTile"
        msg.position = pos
        msg.tile = tile
        self.socket.send(json.dumps(msg, default=lambda o: o.__dict__))

    def on_message(self, ws, message):
        self.queue.append(message)

    def update(self, delta):
        import main

        if main.mainManager.local_player is not None:
            self.timer += delta

            if self.timer >= .1:
                self.timer = 0
                self.update_player_pos(main.mainManager.local_player.position)

        while len(self.queue) > 0:
            self.handle_message(self.queue[0])
            del self.queue[0]

    def handle_message(self, message):
        import main
        import world
        import game

        result = json.loads(message)

        if result["type"] == "world_data_":
            players_dict = result["players"]
            local_id = result["localId"]
            main.mainManager.init(players_dict, local_id)
            main.mainManager.local_player.position = result["spawnPosition"]["x"], result["spawnPosition"]["y"]
            main.mainManager.local_player.last_floor_height = result["spawnPosition"]["y"] + main.mainManager.local_player.size[1]
            size = int(result["size"]["x"]), int(result["size"]["y"])
            main.mainManager.tiles.init(size)
            main.mainManager.tiles.height_map = result["heightMap"]

        if not main.mainManager.connected:
            return

        if result["type"] == "biome":
            main.mainManager.local_player.biome = result["biome"]
        elif result["type"] == "chunk":
            main.mainManager.local_player.position = result["position"]["x"], result["position"]["y"]
            for tile in result["tiles"]:
                if tile is None:
                    continue

                position = int(tile["position"]["Item1"] / 40), int(tile["position"]["Item2"] / 40)
                tile = world.Tile(tile["tileIndex"], position, tile["itemDrop"])
                main.mainManager.tiles.set_tile(position, tile, False)
        elif result["type"] == "SetTile":
            tile = result["tile"]
            position = result["position"]

            if tile is not None:
                tile_obj = world.Tile(tile["tile_index"], position, tile["item_drop"])
                main.mainManager.tiles.set_tile(position, tile_obj, False)
            else:
                main.mainManager.tiles.set_tile(position, None, False)
        elif result["type"] == "player_joined":
            id = result["playerId"]
            main.mainManager.players[id] = game.Player((0, 0), False)
        elif result["type"] == "player_left":
            id = result["playerId"]
            main.mainManager.all_behaviors.remove(main.mainManager.players[id])
            main.mainManager.players[id] = None
        elif result["type"] == "set_player_position":
            id = result["playerId"]
            position = result["position"]["x"], result["position"]["y"]
            player = main.mainManager.players[id]

            if player is not None:
                player.position = position
                player.lerp_counter = 0


class Message(object):
    pass