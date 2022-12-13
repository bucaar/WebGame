import logging
from dataclasses import dataclass
from typing import Callable
from webserver import Request, Response

@dataclass
class RouterContext:
    type: str
    route: str
    additional: str

RouteHandler = Callable[[Request, RouterContext], Response]

class Router:
    def __init__(self, base_route: str = "") -> None:
        self.base_route = base_route
        self.static_routes: dict[str, RouteHandler] = {}
        self.prefix_routes: list[tuple[str, RouteHandler]] = []
        self.default_route: RouteHandler = None

    def add_static_route(self, route: str, handler: RouteHandler) -> None:
        route = self.base_route + route

        if route in self.static_routes:
            logging.warning("ROUTER duplicate static route added: %s" % route)
        
        self.static_routes[route] = handler

    def add_prefix_route(self, route: str, handler: RouteHandler) -> None:
        route = self.base_route + route

        for prefix, other_handler in self.prefix_routes:
            if route.startswith(prefix):
                logging.warning("ROUTER prefix route: %s is hidden by previously added route: %s" % (route, prefix))

        self.prefix_routes.append((route, handler))

    def add_default_route(self, handler: RouteHandler) -> None:
        if self.default_route:
            logging.warning("ROUTER duplicate default route added")
        
        self.default_route = handler

    def add_sub_router(self, base_route: str) -> "Router":
        sub_router = Router(self.base_route + base_route)
        self.add_prefix_route(base_route, sub_router.handle_subrouter_request)
        return sub_router

    def handle_subrouter_request(self, request: Request, router_context: RouterContext) -> Response:
        #TODO: Do we care about the context of a sub router call? It will be rebuilt anyways?
        return self.handle_request(request)

    def handle_request(self, request: Request) -> Response:
        if request.path in self.static_routes:
            context = RouterContext("static", request.path, "")
            return self.static_routes[request.path](request, context)

        for prefix, handler in self.prefix_routes:
            if request.path.startswith(prefix):
                additional = request.path[len(prefix):]
                context = RouterContext("prefix", prefix, additional)
                return handler(request, context)

        if self.default_route:
            context = RouterContext("default", "", request.path)
            return self.default_route(request, context)
        
        logging.warning("ROUTER '%s' could not route request %s" % (self.base_route, request))