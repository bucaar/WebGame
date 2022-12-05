
from router import Router, RouterContext
from gamemanager import GameManager, GameManagerError
from webserver import Request, Response
from util import parse_url_path

class GameManagerApi:
    def __init__(self, game_manager: GameManager) -> None:
        self.game_manager = game_manager

    def player_join(self, request: Request, router_context: RouterContext) -> Response:
        try:
            path = parse_url_path(router_context.additional)
            self.game_manager.add_player(path[0])
            return self.build_response(True)

        except GameManagerError as ex:
            return self.build_response(False, str(ex))

    def player_disconnect(self, request: Request, router_context: RouterContext) -> Response:
        try:
            path = parse_url_path(router_context.additional)
            self.game_manager.remove_player(path[0])
            return self.build_response(True)

        except GameManagerError as ex:
            return self.build_response(False, str(ex))

    def player_list(self, request: Request, router_context: RouterContext) -> Response:
        players = [{
            "name": player.name,
            "lobby": player.lobby.name if player.lobby else None,
            "game": player.game.id if player.game else None
        } for player in self.game_manager.players]

        return self.build_response(True, extra={
            "players": players
        })

    def lobby_join(self, request: Request, router_context: RouterContext) -> Response:
        try:
            path = parse_url_path(router_context.additional)
            self.game_manager.join_lobby(path[0], path[1])
            return self.build_response(True)

        except GameManagerError as ex:
            return self.build_response(False, str(ex))

    def lobby_leave(self, request: Request, router_context: RouterContext) -> Response:
        try:
            path = parse_url_path(router_context.additional)
            self.game_manager.leave_lobby(path[0], path[1])
            return self.build_response(True)

        except GameManagerError as ex:
            return self.build_response(False, str(ex))

    def lobby_list(self, request: Request, router_context: RouterContext) -> Response:
        lobbies = [{
            "name": lobby.name,
            "players": [player.name for player in lobby.players],
            "min_players": lobby.min_players,
            "max_players": lobby.max_players,
            "player_count": len(lobby.players)
        } for lobby in self.game_manager.lobbies]

        return self.build_response(True, extra={
            "lobbies": lobbies
        })

    def game_start(self, request: Request, router_context: RouterContext) -> Response:
        try:
            path = parse_url_path(router_context.additional)
            self.game_manager.start_game(path[0])
            return self.build_response(True)

        except GameManagerError as ex:
            return self.build_response(False, str(ex))

    def game_leave(self, request: Request, router_context: RouterContext) -> Response:
        try:
            path = parse_url_path(router_context.additional)
            self.game_manager.leave_game(path[0], path[1])
            return self.build_response(True)

        except GameManagerError as ex:
            return self.build_response(False, str(ex))

    def game_list(self, request: Request, router_context: RouterContext) -> Response:
        games = [{
            "id": game.id,
            "name": game.get_name(),
            "players": game.players[:],
            "player_count": len(game.players)
        } for game in self.game_manager.games]

        return self.build_response(True, extra={
            "games": games
        })

    def build_response(self, success: bool, message: str = "", extra: dict = {}) -> Response:
        response = {}
        status = ""

        if success:
            response["status"] = "success"
            status = "200"
        else:
            response["status"] = "error"
            status = "400"

        if message:
            response["message"] = message

        if extra:
            response.update(extra)

        return Response(response, status)
        
    def setup_routes(self, router: Router) -> None:
        router.add_prefix_route("player_join", self.player_join)
        router.add_prefix_route("player_disconnect", self.player_disconnect)
        router.add_prefix_route("player_list", self.player_list)

        router.add_prefix_route("lobby_join", self.lobby_join)
        router.add_prefix_route("lobby_leave", self.lobby_leave)
        router.add_prefix_route("lobby_list", self.lobby_list)

        router.add_prefix_route("game_start", self.game_start)
        router.add_prefix_route("game_leave", self.game_leave)
        router.add_prefix_route("game_list", self.game_list)
