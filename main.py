import asyncio
import logging
from datetime import datetime
from webserver import Server
from router import Router, RouterContext
from webserver import Request, Response
from gamemanager import GameManager
from gamemanagerapi import GameManagerApi
from game_guess import GuessGame

def main():
    logging.info("MAIN starting")
    
    server = Server()
    game_manager = GameManager()

    game_manager.add_lobby("NumberGuess", GuessGame, 1)

    router = Router("/")
    router.add_static_route("", index)
    router.add_static_route("index", index)
    router.add_static_route("test", test)
    api_router = router.add_sub_router("api/")
    router.add_default_route(default)

    game_manager_api = GameManagerApi(game_manager)
    game_manager_api.setup_routes(api_router)
    api_router.add_default_route(api)

    server.connection_handler = router.handle_request
    
    logging.info("MAIN starting server")
    asyncio.run(server.start_server())

def index(request: Request, router_context: RouterContext) -> Response:
    return Response(load_static_file("index.html"))

def test(request: Request, router_context: RouterContext) -> Response:
    return Response(load_static_file("test.html"))

def default(request: Request, router_context: RouterContext) -> Response:
    return Response(load_static_file("notfound.html"), status="404")

def load_static_file(file_name: str) -> str:
    with open("static/%s" % file_name) as f:
        return f.read()

def api(request: Request, router_context: RouterContext) -> Response:
    return Response("Invalid API call: %s" % request.path, status="400")

if __name__ == "__main__":
    today = datetime.now()
    date_string = today.strftime("%Y-%m-%d %H:%M:%S")
    logging.basicConfig(filename="log/webserver %s.log" % date_string, encoding="utf-8", level=logging.INFO)
    # logging.basicConfig(filename="log/webserver %s.log" % date_string, encoding="utf-8", level=logging.DEBUG)
    # logging.basicConfig(level=logging.INFO)
    # logging.basicConfig(level=logging.DEBUG)

    try:
        main()
    except Exception as ex:
        logging.critical("MAIN ERROR fatal error", exc_info=ex)