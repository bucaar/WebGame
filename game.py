
class GameOverError(Exception):
    pass

class Game:
    def __init__(self, players: list[str]) -> None:
        self.players: list[str] = players
        self.scores = [0 for _ in players]

    def get_name(self) -> str:
        return ""

    def set_score(self, player_index: int, score: int) -> None:
        self.scores[player_index] = score

    def add_score(self, player_index: int, score: int) -> None:
        self.scores[player_index] += score

    def setup_game(self) -> None:
        pass

    def get_player_expected_output(self, round: int, player_index: int) -> bool:
        pass

    def get_game_data(self, round: int, player_index: int, expected_output: bool) -> str:
        pass

    def update_round(self, round: int, player_output: list["str | None"]):
        pass