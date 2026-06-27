from UserData import raw_users
from GamesData import games,all_genres

#function to build the player's favourite game play rating
# Favorite genre = 70, others = 30
# Each owned game adds +5 to its genre score
def build_player_genre_profile(favorite_genre, games_played, games_dict):
    genre_vector = {genre: 30 for genre in all_genres}
    genre_vector[favorite_genre] = 70
    for game_id in games_played:
        game = games_dict[game_id]
        for genre in game.genres:
            genre_vector[genre] += 10
    for genre,score in genre_vector.items():
        if score > 100:     #to prevent a player who reaches score >= 200
            score = 100
        genre_vector[genre] = round(score / 100, 2)
    return genre_vector

# user_id         : unique identifier
# name            : player's name
# games           : set of owned game IDs
# favorite_genre  : player's declared favorite genre
# genre_profile   : weighted genre preference vector
# neighbors       : top-K similar users in the recommendation graph
class User:
    def __init__(self, user_id, name, games, favorite_genre, genre_profile):
        self.user_id = user_id
        self.name = name
        self.games = set(games)
        self.favorite_genre = favorite_genre
        self.genre_profile = genre_profile
        self.neighbors = []

    def __repr__(self):
        return f"User({self.user_id})"

users = []
for user_id, name, games_played, favorite_genre in raw_users:
    genre_profile = build_player_genre_profile(favorite_genre, games_played, games)
    users.append(User(user_id, name, games_played, favorite_genre, genre_profile))


# print(build_player_genre_profile(users[0].favorite_genre,users[0].games,games))
# print(build_player_genre_profile(users[1].favorite_genre,users[1].games,games))
