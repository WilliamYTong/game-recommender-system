class Game:
    def __init__(self, game_id, title, genres, rating):
        self.game_id = game_id
        self.title = title
        self.genres = genres
        self.rating = rating

    def __repr__(self):
        return f"Game({self.title})"
