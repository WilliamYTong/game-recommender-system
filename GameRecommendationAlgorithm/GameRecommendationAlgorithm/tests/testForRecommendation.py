import sys
import pytest

sys.setrecursionlimit(5000)
# ── shared imports ────────────────────────────────────────────────────────────
from GamesData import games, all_genres
from UserData import raw_users
from UserModel import users, User, build_player_genre_profile
from GameRecommendationAlgorithm_Prep import (
    user_lookup,
    getPlayedGenres,
    gamesByGenre,
    cosSimlarity,
    jaccardSimlarity,
    similarity,
    buildGenreBucket,
    findCandidates,
    getTopKNeighbors,
    buildFullTopkGraph,
    getSCCs,
    condenseGraph,
    genreMatch,
    mergeSortGames,
)
from GameRecommendationAlgorithm import computeRecommendationScores

@pytest.fixture(scope="session")
def graph():
    return buildFullTopkGraph(users, k=3)
@pytest.fixture(scope="session")
def scc_data(graph):
    sccs = getSCCs(graph)
    condensed, scc_map = condenseGraph(graph, sccs)
    scc_members = {i: scc for i, scc in enumerate(sccs)}
    return sccs, condensed, scc_map, scc_members

class TestDataLayer:
    #Testing user and game counts
    def test_game_catalogue_size(self):
        assert len(games) == 500
    def test_user_count(self):
        assert len(users) == 100

class TestGenreProfile:
    #Genre profile must contain every genre in all_genres.
    def test_profile_keys_match_all_genres(self):
        for u in users:
            assert set(u.genre_profile.keys()) == set(all_genres)
    #All genre scores must be in [0.0, 1.0].
    def test_profile_values_in_unit_interval(self):
        for u in users:
            for genre, score in u.genre_profile.items():
                assert 0.0 <= score <= 1.0, f"User {u.user_id} is out of [0,1]"
    #A user with no games should have their favourite genre score (0.70) strictly greater than any other genre (0.30).
    def test_favourite_genre_gets_highest_base(self):
        profile = build_player_genre_profile("Action", [], games)
        assert profile["Action"] > profile["Adventure"]
        assert profile["Action"] > profile["RPG"]
    #Owning games in a genre must raise that genre's score above the base value for users with few games.
    def test_played_games_boost_genre(self):
        profile_before = build_player_genre_profile("Action", [], games)
        profile_after  = build_player_genre_profile("Action", ["55055"], games)
        assert profile_after["RPG"]    >= profile_before["RPG"]
        assert profile_after["Action"] >= profile_before["Action"]
        assert profile_after["Racing"] >= profile_before["Racing"]
    def test_played_games_boost_genre123(self):
        profile_before = build_player_genre_profile("Action", [], games)
        profile_after  = build_player_genre_profile("Action", ["55035"], games)
        assert profile_after["RPG"]    >= profile_before["RPG"]
        assert profile_after["Action"] >= profile_before["Action"]
        assert profile_after["Racing"] >= profile_before["Racing"]
    #No genre score may exceed 1.0 even for harcore users with many games in the same genre.
    def test_profile_capped_at_one(self):
        hardcore = users[61]  # Owen: 25 games
        for score in hardcore.genre_profile.values():
            assert score <= 1.0

class TestSimilarityMetrics:
    #cosSimlarity must return a value in [0, 1]
    def test_cosine_range(self):
        for i in range(19):
            score = cosSimlarity(users[i], users[i + 1])
            assert 0.0 <= score <= 1.0
    def test_cosine_range1(self):
        for i in range(65,80):
            score = cosSimlarity(users[i], users[i + 1])
            assert 0.0 <= score <= 1.0
    #JACCAARD similarity test: all games the same, and emopty game list
    def test_jaccard_same_similarity(self):
        user_a = User("X1", "TestA", ["55001","55002","55003","55004","55005"], "Action", build_player_genre_profile("Action", ["55001","55002","55003","55004","55005"], games))
        user_b = User("X2", "TestB", ["55001","55002","55003","55004","55005"], "Action", build_player_genre_profile("Action", ["55001","55002","55003","55004","55005"], games))
        assert jaccardSimlarity(user_a, user_b) == pytest.approx(1.0)
    #jaccardSimlarity must return 0.0 when both users own no games.
    def test_jaccard_empty_library(self):
        empty_a = User("X1", "TestA", [], "Action", build_player_genre_profile("Action", [], games))
        empty_b = User("X2", "TestB", [], "Action", build_player_genre_profile("Action", [], games))
        assert jaccardSimlarity(empty_a, empty_b) == 0.0
    #similarity(A, B) must equal similarity(B, A).
    def test_combined_similarity_symmetry(self):
        for i in range(0, 20, 2):
            assert similarity(users[i], users[i + 1]) == similarity(users[i + 1], users[i])
    #similarity(A, A) must return 1 (handled by identity shortcut).
    def test_combined_similarity_self_is_one(self):
        for u in users[:5]:
            assert similarity(u, u) == 1
    #Combined similarity must be in [0, 1].
    def test_combined_similarity_range(self):
        for i in range(15):
            s = similarity(users[i], users[i + 3])
            assert 0.0 <= s <= 1.0, f"Combined Similarity is not in the range[0,1]"
    def test_combined_similarity_range1(self):
        for i in range(80,95):
            s = similarity(users[i], users[i + 3])
            assert 0.0 <= s <= 1.0, f"Combined Similarity is not in the range[0,1]"

class TestUserToUserGraphBuilding:
    #Every user_id appear as a node in the graph."""
    def test_graph_has_all_users(self, graph):
        for u in users:
            assert u.user_id in graph, f"User {u.user_id} is not found in the graph"
    #Graph have exactly 300 directed edges (100 users × top-3)."""
    def test_graph_edge_count(self, graph):
        total_edges = sum(len(nbrs) for nbrs in graph.values())
        assert total_edges == 300
    #Every similarity weight stored on an edge must be in [0, 1]."""
    def test_edge_weights_in_range(self, graph):
        for uid, nbrs in graph.items():
            for nid, sim in nbrs.items():
                assert 0.0 <= sim <= 1.0, (f"not in [0,1]")
    #No user should be their own neighbour."""
    def test_no_self_loops(self, graph):
        for uid, nbrs in graph.items():
            assert uid not in nbrs, f"Self-loop: {uid}"

class TestSCCAndCondensation:
    #Every user must appear in exactly one SCC."""
    def test_all_users_in_exactly_one_scc(self, scc_data):
        sccs, _, scc_map, _ = scc_data
        covered = [uid for scc in sccs for uid in scc]
        assert len(covered) == len(users)
        assert len(set(covered)) == len(users)
    #Condensed graph must have one node per SCC."""
    def test_condensed_graph_nodes(self, scc_data):
        sccs, condensed, *_ = scc_data
        assert set(condensed.keys()) == set(range(len(sccs)))
    #No SCC super-node should point to itself."""
    def test_condensed_graph_no_self_loops(self, scc_data):
        _, condensed, *_ = scc_data
        for node, nbrs in condensed.items():
            assert node not in nbrs, f"self-loop: {node}"
    #The condensed graph must be a DAG (no cycles), since SCCs absorb all strongly connected subgraphs."""
    def test_condensed_is_dag(self, scc_data):
        _, condensed, *_ = scc_data
        # DFS cycle check
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {n: WHITE for n in condensed}
        def dfs(u):
            color[u] = GRAY
            for v in condensed[u]:
                if color[v] == GRAY:
                    return True 
                if color[v] == WHITE and dfs(v):
                    return True
            color[u] = BLACK
            return False
        for node in condensed:
            if color[node] == WHITE:
                assert not dfs(node), "Cycle Alerts"

class TestRecommendation:
    # Test Case 1 from the final project submission
    # TC1 – Ivy (009): Simulation, 5 owned games.
    def test_tc1_ivy_simulation_fan(self, scc_data):
        _, condensed, scc_map, scc_members = scc_data
        scores = computeRecommendationScores("009", scc_members, scc_map, condensed, games, 2, 0.5)
        ranked = list(scores.items())
        mergeSortGames(ranked)
        assert len(ranked) >= 400, "Expected ≥ 400 candidate games for Ivy"
        assert ranked[0][1] > 5.0, "Top score should exceed 5.0"
    def test_tc1NoOwned_games(self, scc_data):
        _, condensed, scc_map, scc_members = scc_data
        scores = computeRecommendationScores("009", scc_members, scc_map, condensed, games, 2, 0.5)
        ivy_library = user_lookup["009"].games
        for gid in scores:
            assert gid not in ivy_library, f"Owned game {gid} found in the results"
    #Test cae 2 from the submission
    #TC2 – Ben (002): Adventure fan, 18 owned games.
    def test_tc2_ben_large_library(self, scc_data):
        _, condensed, scc_map, scc_members = scc_data
        scores = computeRecommendationScores("002", scc_members, scc_map, condensed, games, 2, 0.5)
        ranked = list(scores.items())
        mergeSortGames(ranked)
        assert len(ranked) >= 400
        assert ranked[0][1] >= 9.0, f"Expected top score ≥ 9.0 for Ben, got {ranked[0][1]}"
    # Test case 3 from the submission.
    # TC3 – Grace (007): Racing fan, zero owned games.
    def test_tc3_grace_cold_start(self, scc_data):
        _, condensed, scc_map, scc_members = scc_data
        scores = computeRecommendationScores("007", scc_members, scc_map, condensed, games, 2, 0.5)
        ranked = list(scores.items())
        mergeSortGames(ranked)
        assert len(ranked) > 0, "new player must have recommendations"
        assert len(ranked) >= 300, "Expected ≥ 300 candidates from library fallback"
        assert ranked[0][1] > 0.0, "Top score must be positive"
    #TC3 – Grace's top recommendations should include Racing titles.
    def test_tc3_top_games_include_racing(self, scc_data):
        _, condensed, scc_map, scc_members = scc_data
        scores = computeRecommendationScores("007", scc_members, scc_map, condensed, games, 2, 0.5)
        ranked = list(scores.items())
        mergeSortGames(ranked)
        top20_genres = [g for gid, _ in ranked[:20] for g in games[gid].genres]
        assert "Racing" in top20_genres, "Racing genre should appear in Grace's top-20 recommendations"
    #Test Case 4 from the submission
    #TC4 – David (004): Strategy fan, 5 owned games.
    def test_tc4_david_strategy_fan(self, scc_data):
        _, condensed, scc_map, scc_members = scc_data
        scores = computeRecommendationScores("004", scc_members, scc_map, condensed, games, 2, 0.5)
        ranked = list(scores.items())
        mergeSortGames(ranked)
        assert len(ranked) >= 400
        top_game = games[ranked[0][0]]
        assert "Strategy" in top_game.genres, f"Expected Strategy in top game, got {top_game.genres}"
    #TC4 – Results must not include any game David already owns.
    def test_tc4_NoOwnedGames(self, scc_data):
        """TC4 – Results must not include any game David already owns."""
        _, condensed, scc_map, scc_members = scc_data
        scores = computeRecommendationScores("004", scc_members, scc_map, condensed, games, 2, 0.5)
        david_library = user_lookup["004"].games
        for gid in scores:
            assert gid not in david_library
    # With 2 hops, we should have at least as many candidates as 1 hop
    def test_decay_reduces_hop2_scores(self, scc_data):
        _, condensed, scc_map, scc_members = scc_data
        twoHop = computeRecommendationScores("009", scc_members, scc_map, condensed, games, 2, 0.5)
        oneHop = computeRecommendationScores("009", scc_members, scc_map, condensed, games, 1, 0.5)
        assert len(twoHop) >= len(oneHop)\
    # No game should receive a negative recommendation score.
    def test_all_scores_non_negative(self, scc_data):
        _, condensed, scc_map, scc_members = scc_data
        for uid in ["009", "002", "007", "004"]:
            scores = computeRecommendationScores(uid, scc_members, scc_map, condensed, games, 2, 0.5)
            for gid, score in scores.items():
                assert score >= 0.0, f"Negative score found: {uid})"
