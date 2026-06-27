from UserModel import users
from GamesData import games
import random
import math
import heapq
from collections import deque


# lookup dict so we can find User by id
user_lookup = {user.user_id: user for user in users}

# find which genre the player played
# Time Complexity: O(N*M), N = number of games player played, M = number of genre
# But the average genre per games is not much, O(N)
# Space Complexity: O(N*G)
def getPlayedGenres(player,games_dict):
    played_genres = set()   # 
    #get the game id from game, get the genre of the games
    for game_id in player.games:
        game = games_dict[game_id]
        played_genres.update(game.genres)
    return played_genres
#testing getPlayedGenres            PASSED
# for player in users:
#     print(f"{player.name:<10}  {getPlayedGenres(player,games)}")

#lookup table that maps each genre to the list of game IDS
# {"SPORT" : ["G21","G30"]...}
# N = number of games, G = Genre of the game
# Time Complexity: O(N*G), Since G is small and fixed, O(N)
# Space Complexity: O(N*G) With a constant number of genre, simplifies to O(N)
def gamesByGenre(games_dict):
    table = {}  # genre -> list of game_ids
    for game_id, game in games_dict.items():
        for genre in game.genres:
            if genre not in table:
                table[genre] = []
            table[genre].append(game_id)
    return table

#This is the implementaion of cosine similarity metric
#This metric is to measure simlarity between two users' genre profiles
#The result is a similarity scorer of 0 to 1
## Equation:
# sim_score = Σ(Ai * Bi)/ (sqrt(Σ(Ai**2)) *sqrt(Σ(Bi**2)))
#Time Complexity: O(G)
#Space Complexity: O(1)
def cosSimlarity(playerA, playerB):
    dotP = sumSquareA = sumSquareB = 0.0
    for genre in playerA.genre_profile:
        a = playerA.genre_profile[genre]
        b = playerB.genre_profile[genre]
        dotP = dotP + (a * b)
        sumSquareA = sumSquareA + (a*a)
        sumSquareB = sumSquareB + (b*b)
    sqrtA = math.sqrt(sumSquareA)
    sqrtB = math.sqrt(sumSquareB)
    if sqrtA == 0 or sqrtB == 0:
        return 0.0
    return dotP/(sqrtA * sqrtB)
#Testing cosSimlarity
# print(f"Similarity Score betweem Alice and Bob: {cosSimlarity(users[0], users[1])}")


#This is the implementation of Jaccard Matric (Weighted)
# This metirc is to measure similarity based on overlap of games, weighted by each game global ratings
# Equation: score = Σmin(weightA, weightB)/ Σmax(weightA, weightB)
# Time Complexity: O(U) , U = numbers of games in union of both players
# Space Complexity: O(1)
def jaccardSimlarity(playerA,playerB):
    union = playerA.games | playerB.games
    x = 0.0
    y = 0.0
    for gameID in union:
        if gameID in playerA.games:
            weightA = games[gameID].rating
        else:
            weightA = 0.0
        if gameID in playerB.games:
            weightB = games[gameID].rating
        else:
            weightB = 0.0
        x = x + min(weightA,weightB)
        y = y + max(weightA,weightB)
    if y == 0.0: return 0.0
    return x / y
#Testing Jaccard Similarity Passed
# print(f"Alice vs Frank : {jaccardSimlarity(users[0], users[5]):.4f}")

#This is the combination of cosine similarity on the gener profiles and Jaccard Similariy
# This also uses dp to avoid recomputation in the future when the similarity score are genereated in the graph
# cosine similarity (70%), Jaccard Similariy (30%)
# Time Complexity = O(G+H), 
#       G = total unique game across player A and B from jaccard Simimlarity|
#       H = size of genre profile(cosine similarity)
# Space Complexity = O(P^2) P = number of users (storing all pairwise similarities)
def similarity(playerA, playerB, dp= {}):
    if dp is None:
        dp = {}
    if playerA.user_id == playerB.user_id:
        return 1
    k = (max(playerA.user_id, playerB.user_id), min(playerA.user_id, playerB.user_id))
    if k in dp:
        return dp[k]
    score = round(0.7* cosSimlarity(playerA, playerB) + 0.3 * jaccardSimlarity(playerA, playerB),5)
    dp[k] = score
    return score
#testing similarity score(combined version)            #PASSED  
# similarity(users[0], users[5])
# similarity(users[0], users[2])
# similarity(users[2], users[0])
# print(similarity.__defaults__)

#Before we compute the simlariy and connecting each player node:
# Builds a genre-based bucket index for all users
# each genre maps to a list of (player's score, id)
# Player score is derived from user's played games and user's declared favorite genre
# Sort each genre bucket using Python's built-in Timsort algorithm
# Time Complexity: O(U * G log G)
#   U = number of users
#   G = average number of genres per user
# Space Complexity: O(U * G)
def buildGenreBucket(all_users):
    buckets = {}
    for user in all_users:
        r = getPlayedGenres(user,games) #genres user played
        r.add(user.favorite_genre)              #add player's declared favorite genre to ensure if the player does not play thier fav genre yet
        for genre in r:
            if genre not in buckets:
                buckets[genre] = []
            score = user.genre_profile[genre]
            buckets[genre].append((score, user.user_id))
    for genre in buckets:
        buckets[genre].sort(key = lambda x: x[0])
    return buckets
#testing buildGenreBucket()                #PASSED
# buckets = buildGenreBucket(users)
# for genre, bucket in buckets.items():
#     print(f"\n {genre}")
#     for score, uid in bucket:
#         print(f"{user_lookup[uid].name:<10} -> {score}")

#This is the helper function 
# bineary search based funtion to find the insertion index in a sorted array
# based on left (lower bound) or right (upper bound) behavior.
# Time Complexity: O(log n)
# Space Complexity: O(1)
def binarySearchBound(arr, target, right = False):
    l, h = 0, len(arr)
    while l < h:
        mid = (l + h) // 2
        if right:
            if arr[mid] <= target:
                l = mid + 1
            else:
                h = mid
        else:
            if arr[mid] < target:
                l = mid + 1
            else:
                h = mid
    return l

# To find the candidates users for a given player
# genre-based filtering: get relevant genre for player
# for each genre, find users within a score window(+-0.2)
# get the qualified unique user_ids
# Time Complexity: O(G log U + K)
# G = number of genres for player
# U = users per bracket(binary search)
# K = number of candidates returned
# Space Complexity: O(K)
def findCandidates(player, genreBucket, windowGap = 0.2):
    candidates = set()
    relevantGenre = getPlayedGenres(player, games)
    relevantGenre.add(player.favorite_genre)
    for genre in relevantGenre:
        if genre not in genreBucket: #key error possible
            continue
        bucket = genreBucket[genre]
        scores = [s for s,_ in bucket]
        userGScore = player.genre_profile[genre]    #player's genre score
        left = binarySearchBound(scores, userGScore - windowGap, False)       #lower bound
        right = binarySearchBound(scores, userGScore + windowGap, True)       #upper bound
        for i in range(left,right):
            _,candidateId = bucket[i]      #retrive candidate id from bucket
            if candidateId != player.user_id:
                candidates.add(user_lookup[candidateId])
    return candidates

# to get the top k most similar neigbors for a given player, k = 3 in default
# use priority queue (min-heap)
# if heap size exceeds k, remove smallest similarity score user
# Time Complexity: O(C log K)
#  C = number of candidates
# Space Complexity: O(K)
def getTopKNeighbors(player, candidates, k = 3):
    heap = []
    for c in candidates:
        sim = similarity(player,c)
        heapq.heappush(heap,(sim,c.user_id))
        if len(heap) > k:
            popped = heapq.heappop(heap)
    return heap
#Testing            #need to test by hand
# buckets = buildGenreBucket(users)
# candidates = findCandidates(users[0], buckets)
# topK      = getTopKNeighbors(users[0], candidates, 3)
# for sim, uid in sorted(topK, reverse=True):
#     print(f"  {user_lookup[uid].name:<10} → sim={sim:.4f}")


# A full user-user graph using BFS traversal
# # Time Complexity: O(N * C log K)
#   N = number of visited users
#   C = number of candidates per user
#   K = top-K neighbors
# Space Complexity: O(N + E)
#   E = similarity edges
def buildFullTopkGraph(all_users, k=3):
    if not all_users:
        return {}
    genreBuckets = buildGenreBucket(all_users)
    graph = {user.user_id: {} for user in all_users}
    visited = set()
    def bfsGraph(start, buckets, graph, visited):
        """For the given user, finds the top 3 most similar neighbors and adds similarity edges.
           Then expands to each neighbor using BFS. This is the helper function for build Full Top-k Graph
           Time Complexity: O(C log K)
           Space Complexity: O(N + E)"""
        queue = deque()
        queue.append(start.user_id)
        visited.add(start.user_id)
        while queue:
            currentID = queue.popleft()
            currentUser = user_lookup[currentID]
            candidates = findCandidates(currentUser,buckets)
            if not candidates:
                continue
            topK = getTopKNeighbors(currentUser,candidates,3)      #find top 3
            for sim, neighborID in topK:
                graph[currentID][neighborID] = sim
                if neighborID not in visited:
                    visited.add(neighborID)
                    queue.append(neighborID)
    for user in all_users:
        if user.user_id not in visited:      #bfs for unvisited users
            bfsGraph(user, genreBuckets, graph, visited)
    return graph


# Print results             #Need to test by hand
# result = buildFullTopkGraph(users)    
# print("\n" + "=" * 70)
# print("RESULT GRAPH:")
# print("=" * 70)
# for user_id, neighbors in result.items():
#     user_name = user_lookup[user_id].name
#     print(f"{user_name} (ID {user_id}) : {neighbors}")
# if __name__ == "__main__":
#     print(f"*"*30)

#This is the helper function for Merge sort
# Time complexity: O(n)
# Space Complexity: O(1)
def merge(left,right,array):
    leftSize = len(array)//2
    rightSize = len(array) - leftSize
    i = l = r = 0
    while l < leftSize and r < rightSize:
        if left[l][1] >= right[r][1]:
            array[i] = left[l]
            i += 1
            l += 1
        else:
            array[i] = right[r]
            i += 1
            r += 1
    while l < leftSize:
        array[i] = left[l]
        i += 1
        l += 1
    while r < rightSize:
        array[i] = right[r]
        i += 1
        r += 1

# sorts the array using the merge Sort helper function
# Time Complexity: O(n log n)
# Space Complexity: O(n)
def mergeSortGames(array):
    n = len(array)
    if n <= 1: return
    mid = n//2
    left = [None]*mid
    right = [None]*(n-mid)
    j = 0
    for i in range(n):
        if i < mid:
            left[i] = array[i]
        else:
            right[j] = array[i]
            j += 1
    mergeSortGames(left)
    mergeSortGames(right)
    merge(left,right,array)


#use tarjan's method to find Strongly Connected Components(SCC) in the graph
# reference: geeksforgeeks.org, and modify for this project
# Time Complexity:  O(N + M) 
#   N = number of vertices
#   M = number of edges
# Space Complexity: O(N)     — stack + index + lowlink
def findSCC(u, graph, disc, low, inSt, st, timer, allSCCs):
    # initialize discovery time and low value
    timer[0] += 1
    disc[u]  = low[u] = timer[0]
    # push current vertex to stack
    st.append(u)
    inSt[u] = True
    # visit all neighbors
    for v in graph[u]:
        if v not in disc:               # case 1: tree edge — not visited
            findSCC(v, graph, disc, low, inSt, st, timer, allSCCs)
            low[u] = min(low[u], low[v])
        elif inSt.get(v,False):                   # case 2: back edge — still on stack
            low[u] = min(low[u], disc[v])
    # if u is root of SCC
    if low[u] == disc[u]:
        scc = []
        while True:
            x = st.pop()
            inSt[x] = False
            scc.append(x)
            if x == u:
                break
        allSCCs.append(scc)

 # initializes data, and runs Tarjan's algorithm directly on the user_id graph
 # find all SCCs in the graph
 # return the list of SCC groups, where each SCC is a list of user_id
 # [[id9,id1,id2],[id0],[id8,id7]]
 # Time Complexity: O(N + M)
 # Space Complexity: O(N + M)
def getSCCs(graph):
    disc = {}
    low = {}
    inSt = {}
    st = []
    timer = [0]
    allSCCs = []
    for i in graph:
        if i not in disc:
            findSCC(i, graph, disc, low, inSt, st, timer, allSCCs)
    return allSCCs


# Testingn for sccs         #Tested  based on the graph drawing-PASSED
# graph = buildFullTopkGraph(users, 3)
# sccs = getSCCs(graph)
# print("── Strongly Connected Components ────────")
# for i, scc in enumerate(sccs):
#     names = [user_lookup[uid].name for uid in scc]
#     print(f"  SCC {i+1}  → {names}")

# Condense the user-user graph into scc graph
# each scc group is treated as single node
# and edge between users become edges between sccs
# Time Complexity: O(N+M)
# N = number of users
# M = number of edges in the graph
# Space Complexity: O(N+M)
def condenseGraph(graph, sccs):
    scc_map = {}
    # id -> group belong
    for i, scc in enumerate(sccs):
        for uid in scc:
            scc_map[uid] = i
    condensed = {i: set() for i in range(len(sccs))}
    for playerID, neighbors in graph.items():
        p_scc = scc_map[playerID]
        for nid in neighbors:
            n_scc = scc_map[nid]
            if p_scc != n_scc:              # skip edges within same SCC
                condensed[p_scc].add(n_scc) # add edge between SCCs
    output = {}
    for i, neighbors in condensed.items():
        output[i] = list(neighbors)
    return output, scc_map      #return also scc_map so propagateScore fucntion does not need to calculate again
#Test in graph_drawing.py

#This is the helper function.
# This is to measure how strongly a game matches a player’s genre preferences
# based on the player’s genre profile.
# Time complexity: O(N)
# N = number of genres in the game
#Space complexity: O(1)
def genreMatch(player, game):
    # average of player's genre scores for this game's genres
    total = 0
    count = 0
    for g in game.genres:
        if g in player.genre_profile:
            total = total + player.genre_profile[g]
            count = count + 1
    if count <= 0:
        return 0.0
    return total/count