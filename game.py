
class GameOverError(Exception):
    pass

class Game:
    def __init__(self, id: str, players: list[str]) -> None:
        self.id = id
        self.players: list[str] = players
        self.scores = [0 for _ in players]

    def get_name(self) -> str:
        return ""

    def setup_game(self) -> None:
        pass