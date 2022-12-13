
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
            self.game_manager.player_join(path[0])
            return self.build_response(True)

        except GameManagerError as ex:
            return self.build_response(False, str(ex))

    def player_disconnect(self, request: Request, router_context: RouterContext) -> Response:
        try:
            path = parse_url_path(router_context.additional)
            self.game_manager.player_disconnect(path[0])
            return self.build_response(True)

        except GameManagerError as ex:
            return self.build_response(False, str(ex))

    def player_list(self, request: Request, router_context: RouterContext) -> Response:
        players = [{
            "name": player.name,
            "lobby": player.lobby_name,
            "game": player.game_id
        } for player in self.game_manager.players]

        return self.build_response(True, extra={
            "players": players
        })

    def lobby_join(self, request: Request, router_context: RouterContext) -> Response:
        try:
            path = parse_url_path(router_context.additional)
            self.game_manager.lobby_join(path[0], path[1])
            return self.build_response(True)

        except GameManagerError as ex:
            return self.build_response(False, str(ex))

    def lobby_leave(self, request: Request, router_context: RouterContext) -> Response:
        try:
            path = parse_url_path(router_context.additional)
            self.game_manager.lobby_leave(path[0], path[1])
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
            self.game_manager.game_start(path[0])
            return self.build_response(True)

        except GameManagerError as ex:
            return self.build_response(False, str(ex))

    def game_leave(self, request: Request, router_context: RouterContext) -> Response:
        try:
            path = parse_url_path(router_context.additional)
            self.game_manager.game_leave(path[0], path[1])
            return self.build_response(True)

        except GameManagerError as ex:
            return self.build_response(False, str(ex))

    def set_player_output(self, request: Request, router_context: RouterContext) -> Response:
        try:
            path = parse_url_path(router_context.additional)
            self.game_manager.set_player_output(path[0], path[1])
            return self.build_response(True)

        except GameManagerError as ex:
            return self.build_response(False, str(ex))

    def game_list(self, request: Request, router_context: RouterContext) -> Response:
        games = [{
            "id": game_state.id,
            "name": game_state.name,
            "lobby": game_state.lobby_name,
            "players": game_state.game.players[:],
            "player_count": len(game_state.game.players)
        } for game_state in self.game_manager.games]

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
        player_router = router.add_sub_router("player/")
        player_router.add_prefix_route("join", self.player_join)
        player_router.add_prefix_route("disconnect", self.player_disconnect)
        player_router.add_prefix_route("list", self.player_list)

        lobby_router = router.add_sub_router("lobby/")
        lobby_router.add_prefix_route("join", self.lobby_join)
        lobby_router.add_prefix_route("leave", self.lobby_leave)
        lobby_router.add_prefix_route("list", self.lobby_list)

        game_router = router.add_sub_router("game/")
        game_router.add_prefix_route("start", self.game_start)
        game_router.add_prefix_route("leave", self.game_leave)
        game_router.add_prefix_route("list", self.game_list)

        game_router = router.add_sub_router("play/")
        game_router.add_prefix_route("output", self.set_player_output)
