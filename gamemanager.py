from dataclasses import dataclass, field
from game import Game, GameOverError
import random
import string
import logging
import asyncio

@dataclass
class Player:
    name: str
    lobby_name: str = None
    game_id: str = None

@dataclass
class Lobby:
    name: str
    game_factory: type[Game]
    min_players: int
    max_players: int
    players: list[Player] = field(default_factory=list)

@dataclass
class GameState:
    id: str
    game: Game
    name: str
    lobby_name: str
    round: int = 0
    player_expected_output: list[bool] = field(default_factory=list)
    game_data: list["str | None"] = field(default_factory=list)
    player_output: list["str | None"] = field(default_factory=list)

class GameManagerError(Exception):
    pass

class GameManager:
    def __init__(self) -> None:
        self.lobbies: list[Lobby] = []
        self.lobby_name_map: dict[str, Lobby] = {}

        self.players: list[Player] = []
        self.player_name_map: dict[str, Player] = {}

        self.games: list[GameState] = []
        self.active_games: list[GameState] = []
        self.game_id_map: dict[str, GameState] = {}

    def add_lobby(self, name: str, game_factory: type[Game], min_players: int, max_players: int = 0) -> None:
        if name in self.lobby_name_map:
            raise GameManagerError("Lobby already exists: %s" % name)

        logging.info("GAMEMANAGER adding lobby %s" % name)
        lobby = Lobby(name, game_factory, min_players, max_players)
        self.lobbies.append(lobby)
        self.lobby_name_map[name] = lobby

    def player_join(self, name: str) -> None:
        if name in self.player_name_map:
            raise GameManagerError("Player already exists: %s" % name)

        logging.info("GAMEMANAGER adding player %s" % name)
        player = Player(name)
        self.players.append(player)
        self.player_name_map[name] = player

    def player_disconnect(self, name: str) -> None:
        if name not in self.player_name_map:
            raise GameManagerError("Player cannot be removed, they do not exist: %s" % name)

        player = self.player_name_map[name]
        player_lobby_name = player.lobby_name
        player_game_id = player.game_id

        if player_lobby_name is not None:
            self.lobby_leave(player_lobby_name, player.name)

        if player_game_id is not None:
            self.game_leave(player_game_id, player.name)

        logging.info("GAMEMANAGER removing player %s" % name)
        self.players.remove(player)
        del self.player_name_map[name]

    def lobby_join(self, lobby_name: str, player_name: str) -> None:
        if lobby_name not in self.lobby_name_map:
            raise GameManagerError("Lobby does not exist: %s" % lobby_name)
        if player_name not in self.player_name_map:
            raise GameManagerError("Player does not exist: %s" % player_name)

        lobby = self.lobby_name_map[lobby_name]
        player = self.player_name_map[player_name]
        player_lobby_name = player.lobby_name
        player_game_id = player.game_id

        if player_game_id is not None:
            raise GameManagerError("Player %s is already in another game: %s" % (player_name, player_game_id))
        if player_lobby_name == lobby_name:
            raise GameManagerError("Player %s is already in lobby: %s" % (player_name, lobby_name))
        if player_lobby_name is not None:
            raise GameManagerError("Player %s is already in another lobby: %s" % (player_name, player_lobby_name))

        logging.info("GAMEMANAGER player %s joining lobby %s" % (player_name, lobby_name))
        player.lobby_name = lobby_name
        lobby.players.append(player)

    def lobby_leave(self, lobby_name: str, player_name: str) -> None:
        if lobby_name not in self.lobby_name_map:
            raise GameManagerError("Lobby does not exist: %s" % lobby_name)
        if player_name not in self.player_name_map:
            raise GameManagerError("Player does not exist: %s" % player_name)

        lobby = self.lobby_name_map[lobby_name]
        player = self.player_name_map[player_name]
        player_lobby_name = player.lobby_name

        if player_lobby_name is None:
            raise GameManagerError("Player %s cannot leave lobby, they are not in one" % player_name)
        if player_lobby_name != lobby_name:
            raise GameManagerError("Player %s cannot leave lobby, they are in another lobby: %s" % (player_name, player_lobby_name))

        logging.info("GAMEMANAGER player %s leaving lobby %s" % (player_name, lobby_name))
        player.lobby_name = None
        lobby.players.remove(player)

    def random_game_id(self, length: int) -> str:
        for attempt in range(10):
            id = ""
            while len(id) < length:
                id += random.choice(string.ascii_lowercase)
            
            if id not in self.game_id_map:
                return id

        raise GameManagerError("Could not generate unique game id after %d attempts" % (attempt + 1))

    def game_start(self, lobby_name: str) -> None:
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
        game = lobby.game_factory(names)
        game_name = game.get_name()
        game_state = GameState(game_id, game, game_name, lobby_name)

        for player in players:
            self.lobby_leave(lobby.name, player.name)
            player.game_id = game_id

        logging.info("GAMEMANAGER starting game %s (%s) with players %s" % (game_id, game_name, names))
        self.games.append(game_state)
        self.active_games.append(game_state)
        self.game_id_map[game_id] = game_state

        logging.info("GAMEMANAGER set up game %s (%s)" % (game_id, game_name))
        game.setup_game()

    def game_leave(self, game_id: str, player_name: str) -> None:
        if game_id not in self.game_id_map:
            raise GameManagerError("Game does not exist: %s" % game_id)
        if player_name not in self.player_name_map:
            raise GameManagerError("Player does not exist: %s" % player_name)

        game_state = self.game_id_map[game_id]
        game = game_state.game
        player = self.player_name_map[player_name]
        player_game_id = player.game_id

        if player_game_id is None:
            raise GameManagerError("Player %s cannot leave game, they are not in one" % player_name)
        if player_game_id != game_id:
            raise GameManagerError("Player %s cannot leave game, they are in another game: %s" % (player_name, player_game_id))

        logging.info("GAMEMANAGER player %s leaving game %s (%s)" % (player_name, game_id, game.get_name()))
        player.game_id = None
        #TODO: remove the game from the game manager?

    def set_player_output(self, player_name: str, player_output: str) -> None:
        if player_name not in self.player_name_map:
            raise GameManagerError("Player does not exist: %s" % player_name)
        if not player_output:
            raise GameManagerError("Player output must be provided")

        player = self.player_name_map[player_name]
        player_game_id = player.game_id

        if player_game_id is None:
            raise GameManagerError("Player %s is not in a game" % (player_name))
        if player_game_id not in self.game_id_map:
            raise RuntimeError("Player game id %s does not exist" % player_game_id)

        player_game_state = self.game_id_map[player_game_id]

        if player_name not in player_game_state.game.players:
            raise RuntimeError("Player %s is not in game players %s" % (player_name, player_game_state.game.players))

        player_index = player_game_state.game.players.index(player_name)
        if player_game_state.player_output[player_index] is not None:
            raise GameManagerError("Player %s has already provided output" % player_name)

        logging.info("GAMEMANAGER player %s provided output for game %s (%s)" % (player_name, player_game_state.id, player_game_state.name))
        player_game_state.player_output[player_index] = player_output

    async def start_game_loop(self) -> None:
        try:
            while True:
                self.update_games()
                await asyncio.sleep(5)

        except asyncio.CancelledError as ex:
            logging.warning("GAMEMANAGER ERROR game loop cancelled", exc_info=ex)

    def update_games(self) -> None:
        logging.info("GAMEMANAGER updating games")
        active_game_states = self.active_games[:]

        for game_state in active_game_states:
            try:
                self.update_game(game_state)
            except GameOverError as ex:
                logging.warning("GAMEMANAGER ERROR game over encountered in game %s (%s)" % (game_state.id, game_state.name), exc_info=ex)
                self.active_games.remove(game_state)
            except GameManagerError as ex:
                logging.error("GAMEMANAGER ERROR while updating game %s (%s)" % (game_state.id, game_state.name), exc_info=ex)
                self.active_games.remove(game_state)
            except Exception as ex:
                logging.critical("GAMEMANAGER ERROR while updating game %s (%s)" % (game_state.id, game_state.name), exc_info=ex)
                self.active_games.remove(game_state)

    def update_game(self, game_state: GameState) -> None:
        logging.info("GAMEMANAGER updating game %s (%s)" % (game_state.id, game_state.name))

        if game_state.round == 0:
            self.set_up_round(game_state)
            return

        if self.is_round_over(game_state):
            logging.info("GAMEMANAGER update round %d for game %s (%s)" % (game_state.round, game_state.id, game_state.name))
            game_state.game.update_round(game_state.round, game_state.player_output)

            self.set_up_round(game_state)

    def set_up_round(self, game_state: GameState) -> None:
        game = game_state.game
        players = game.players[:]
        game_state.round += 1
        logging.info("GAMEMANAGER set up round %d for game %s (%s)" % (game_state.round, game_state.id, game_state.name))

        if not players:
            raise RuntimeError("Cannot update game with no players. %s (%s)" % (game_state.id, game_state.name))

        game_state.player_expected_output = []
        game_state.game_data = []
        game_state.player_output = []
        for player_index, player_name in enumerate(players):
            expected = game.get_player_expected_output(game_state.round, player_index)
            data = game.get_game_data(game_state.round, player_index, expected)

            game_state.player_expected_output.append(expected)
            game_state.game_data.append(data)
            game_state.player_output.append(None)

    def is_round_over(self, game_state: GameState) -> None:
        if not game_state.player_expected_output:
            raise RuntimeError("Cannot determine if the round is over, there is no player expected output")

        #If we aren't expecting any output
        #then the round is over if there is any input at all
        if not any(game_state.player_expected_output):
            return any(game_state.player_output)

        #If we are expecting output
        #then the round is over when all expected responses have been provided
        responses = (response[1] for response in zip(
            game_state.player_expected_output, 
            game_state.player_output
        ) if response[0])
        if not responses:
            raise RuntimeError("No responses were returned. %r, %r" % (game_state.player_expected_output, game_state.player_output))
        
        return all(responses)
