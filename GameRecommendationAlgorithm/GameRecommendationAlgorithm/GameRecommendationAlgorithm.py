from GameRecommendationAlgorithm_Prep import *

LIBRARY_WEIGHT = 0.5
# use already built build scc_members, scc_map, and condensed graph from GameRecommendationAlgorithm_Prep
# to calculate the scores of the games to show the recommendation for the user
# Time Complexity: O(H × M × P + E' + Lg)
#    H = number of SCCs reached within max_hops < S(SCCs)
#    M = average members per SCC 
#    P = average games per user
#    E' = edges traversed in BFS
#    Lg = total games scanned via genre lookup
# Space Complexity: O (G + S + E)
#   G = number of games processed
#   E = edges in condensed graph
def computeRecommendationScores(target_uid, scc_members, scc_map, condensed, games_dict, max_hops=2, decay=0.5):
    targetSCC = scc_map[target_uid]
    targetUser = user_lookup[target_uid]       #to lookup the user object
    gameScores_dp = {}                        # game_id → score
    visitedScc = set()                     # avoid revisiting SCCs
    genreTable = gamesByGenre(games_dict)  # genre -> list of game_ids
   
    def neighPropagate():
        queue = deque()
        queue.append((targetSCC, 0))
        visitedScc.add(targetSCC)
        while queue:
            currentSCC, hop = queue.popleft()
            if hop > max_hops:                  # stop at max hops
                continue
            weight = decay ** hop               # full score at hop 0, decayed after
            for uid in scc_members[currentSCC]:
                user = user_lookup[uid]
                for gameId in user.games:
                    if gameId in targetUser.games:  # skip games target already owns
                        continue
                    game  = games_dict[gameId]
                    score = game.rating * weight * genreMatch(targetUser, game)
                    # keep highest score if game found at multiple hops
                    # highest socre here because the game could found in other scc
                    if gameId not in gameScores_dp or score > gameScores_dp[gameId]:
                        gameScores_dp[gameId] = score
            # This is to check neighrbor scc_group, we will only hop twic (Meaning two edges away)
            for neighborSCC in condensed[currentSCC]:
                if neighborSCC not in visitedScc:
                    visitedScc.add(neighborSCC)
                    queue.append((neighborSCC, hop + 1))
    # scan games of target's genre in game library
    def scoreFromGamesLib():
        relevantGenres = getPlayedGenres(targetUser, games_dict)
        relevantGenres.add(targetUser.favorite_genre)
        for genre in relevantGenres:
            if genre not in genreTable:
                continue
            for gameId in genreTable[genre]:
                if gameId in targetUser.games:    # skip owned games
                    continue
                game  = games_dict[gameId]
                gm    = genreMatch(targetUser, game)
                score = game.rating * LIBRARY_WEIGHT * gm
            # only add if not already scored higher by neighbor propagation
                if gameId not in gameScores_dp:
                    gameScores_dp[gameId] = score
    neighPropagate()
    scoreFromGamesLib()
    return gameScores_dp

if __name__ == "__main__":
    targetPlayerId = "001"
    targetPlayer = user_lookup[targetPlayerId]
    graph = buildFullTopkGraph(users, 3)
    sccs = getSCCs(graph)
    condensed,scc_map = condenseGraph(graph, sccs)
    scc_members = {i: scc for i, scc in enumerate(sccs)}
    game_scores = computeRecommendationScores(targetPlayerId, scc_members, scc_map, condensed,games, 2, 0.5)
    scored_list = list(game_scores.items())
    mergeSortGames(scored_list)
    print("=====================================================================")
    print("║                   Game Recommendation System                      ║")
    print("=====================================================================")
    print(f"Target Player ID : {targetPlayerId}")
    print(f"Name             : {targetPlayer}")
    print(f"Favourite Genre  : {targetPlayer.favorite_genre}")
    print("*********************************************************************")

    for i, (game_id, score) in enumerate(scored_list[:30], 1):
        game = games[game_id]
        print(f"  {i:<3} {game.title:<35} score={score:.2f}  genres={game.genres}")