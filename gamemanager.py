
from dataclasses import dataclass, field
from game import Game
import random
import string
import logging

@dataclass
class Player:
    name: str
    lobby: "Lobby" = None
    game: Game = None

@dataclass
class Lobby:
    name: str
    game_factory: type[Game]
    min_players: int
    max_players: int
    players: list[Player] = field(default_factory=list)
    games: list[Game] = field(default_factory=list)

class GameManagerError(Exception):
    pass

class GameManager:
    def __init__(self) -> None:
        self.lobbies: list[Lobby] = []
        self.lobby_name_map: dict[str, Lobby] = {}

        self.players: list[Player] = []
        self.player_name_map: dict[str, Player] = {}

        self.games: list[Game] = []
        self.game_id_map: dict[str, Game] = {}

    def add_lobby(self, name: str, game_factory: type[Game], min_players: int, max_players: int = 0) -> None:
        if name in self.lobby_name_map:
            raise GameManagerError("Lobby already exists: %s" % name)

        logging.info("GAMEMANAGER adding lobby %s" % name)
        lobby = Lobby(name, game_factory, min_players, max_players)
        self.lobbies.append(lobby)
        self.lobby_name_map[name] = lobby

    def add_player(self, name: str) -> None:
        if name in self.player_name_map:
            raise GameManagerError("Player already exists: %s" % name)

        logging.info("GAMEMANAGER adding player %s" % name)
        player = Player(name)
        self.players.append(player)
        self.player_name_map[name] = player

    def remove_player(self, name: str) -> None:
        if name not in self.player_name_map:
            raise GameManagerError("Player cannot be removed, they do not exist: %s" % name)

        player = self.player_name_map[name]

        if player.lobby is not None:
            self.leave_lobby(player.lobby.name, player.name)

        if player.game is not None:
            self.leave_game(player.game.id, player.name)

        logging.info("GAMEMANAGER removing player %s" % name)
        self.players.remove(player)
        del self.player_name_map[name]

    def join_lobby(self, lobby_name: str, player_name: str) -> None:
        if lobby_name not in self.lobby_name_map:
            raise GameManagerError("Lobby does not exist: %s" % lobby_name)
        if player_name not in self.player_name_map:
            raise GameManagerError("Player does not exist: %s" % player_name)

        lobby = self.lobby_name_map[lobby_name]
        player = self.player_name_map[player_name]

        if player.game is not None:
            raise GameManagerError("Player %s is already in another game: %s" % (player_name, player.game.id))
        if player.lobby is lobby:
            raise GameManagerError("Player %s is already in lobby: %s" % (player_name, lobby_name))
        if player.lobby is not None:
            raise GameManagerError("Player %s is already in another lobby: %s" % (player_name, player.lobby.name))

        logging.info("GAMEMANAGER player %s joining lobby %s" % (player_name, lobby_name))
        player.lobby = lobby
        lobby.players.append(player)

    def leave_lobby(self, lobby_name: str, player_name: str) -> None:
        if lobby_name not in self.lobby_name_map:
            raise GameManagerError("Lobby does not exist: %s" % lobby_name)
        if player_name not in self.player_name_map:
            raise GameManagerError("Player does not exist: %s" % player_name)

        lobby = self.lobby_name_map[lobby_name]
        player = self.player_name_map[player_name]

        if player.lobby is None:
            raise GameManagerError("Player %s cannot leave lobby, they are not in one" % player_name)
        if player.lobby is not lobby:
            raise GameManagerError("Player %s cannot leave lobby, they are in another lobby: %s" % (player_name, player.lobby.name))

        logging.info("GAMEMANAGER player %s leaving lobby %s" % (player_name, lobby_name))
        player.lobby = None
        lobby.players.remove(player)

    def random_game_id(self, length: int) -> str:
        for attempt in range(10):
            id = ""
            while len(id) < length:
                id += random.choice(string.ascii_lowercase)
            
            if id not in self.game_id_map:
                return id

        raise GameManagerError("Could not generate unique game id after %d attempts" % (attempt + 1))

    def start_game(self, lobby_name: str) -> None:
        if lobby_name not in self.lobby_name_map:
            raise GameManagerError("Lobby does not exist: %s" % lobby_name)
        
        lobby = self.lobby_name_map[lobby_name]

        players = lobby.players[:]
        if len(players) < lobby.min_players:
            raise GameManagerError("Cannot start game, lobby %s does not have enough players. (%d/%d)" % (lobby_name, len(lobby.players), lobby.min_players))

        if lobby.max_players > 0 and len(players) > lobby.max_players:
            players = random.sample(players, lobby.max_players)
        else:
            random.shuffle(players)

        game_id = self.random_game_id(6)
        names = [player.name for player in players]
        game = lobby.game_factory(game_id, names)

        for player in players:
            self.leave_lobby(lobby.name, player.name)
            player.game = game

        logging.info("GAMEMANAGER starting game %s (%s) with players %s" % (game_id, game.get_name(), names))
        self.games.append(game)
        self.game_id_map[game_id] = game

    def leave_game(self, game_id: str, player_name: str) -> None:
        if game_id not in self.game_id_map:
            raise GameManagerError("Game does not exist: %s" % game_id)
        if player_name not in self.player_name_map:
            raise GameManagerError("Player does not exist: %s" % player_name)

        game = self.game_id_map[game_id]
        player = self.player_name_map[player_name]

        if player.game is None:
            raise GameManagerError("Player %s cannot leave game, they are not in one" % player_name)
        if player.game is not game:
            raise GameManagerError("Player %s cannot leave game, they are in another game: %s" % (player_name, player.game.id))

        logging.info("GAMEMANAGER player %s leaving game %s (%s)" % (player_name, game_id, game.get_name()))
        player.game = None
        #TODO: remove the game from the game manager?