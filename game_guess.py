import random
from game import Game, GameOverError

class GuessGame(Game):
    def setup_game(self) -> None:
        self.score = 100
        self.secret_number = random.randint(1, 10)
        self.guess_limit = 4
        self.guesses: list[int] = []

    def make_guess(self, guess: int) -> None:
        self.guesses.append(guess)
        if guess == self.secret_number:
            raise GameOverError("The number was guessed!")

        elif len(self.guesses) >= self.guess_limit:
            raise GameOverError("Exceeded attempts.")

        else:
            self.score -= 10