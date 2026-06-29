# game-recommender-algorithm
## Description
This is the game recommendation algorithm that suggests games to players basedon what similar players enjoy. The recommendation process works as follows:
1. Find similar players by comparing users' game preferences, and user's owned games
2. Use the graph alogirthms to ... "Strongly Connected Components"
3. Compute the recommendations score for the game that target player has not played.
My solution is based on the idea that "If I love the same horro games as you, I probably like the similar action games too."
### How It Works?
#### Measuring the similariy between player
  - scosine similariy is used to mesure the simlarity between two users' genre profiles
  - Jaccard similariy to measure the overlap between the games two users have played. The overlap is weighted by each game's global rating.
   - 70% genre preference similariy(Cosine similariy) and 30% weighted shared-game similariy(Jaccard similariy) is used to compute overall similariy score.
#### Building the Network of Players
  - For each player, find the top 3 most similar players and connect them. This creates a network where similariy players are connected.
  - **Tarjan's algorithm** is used to find groups of plauers who are all connnected to each other. (Strongly Connected Components/SCCs)
In our test, we have 100 players, and it formed the 10 SCCs. So, instead of tracking 100 individual players, the algorithm first identify the SCC to which the target player belongs. Recommendation are genenrated by considering players withing that SCC, and its neighbors.
#### Recommendation Games
##### Check Similar Players
  - We look at the target player's community, look at nearyby communites(in this program max_hop == 2), find games similar players own that target's player does not have, and compute the recommendation score for that game.
##### Backup - Check the Game Library
  - If the algorithm cannot find enough recommended games, or if the target player does not belong to any SCC, it falls back to the player's declared favorite genre. Games matching that genre aer then recommended to ensure player gets the relevanat suggestions.
## Files in this project
game-recommendation-system/GameRecommendationAlgorithm
   1. ***GameRecommendationAlgorithm.py***  <- Run this/ **Main**
   2. GameRecommendationAlgorithm_Prep.py ← Helper functions
   3. ***graph_drawing.py***              ← Run this/ **To show the network visually**
   4. UserModel.py                        <- build player object
   5. UserData.py                         <- 100 players info
   6. GameModel.py                        <- build game object
   7. GamesData.py                        <- 500 Games info
   8. README.md                           <- this page
* testForRecommendation.py wtth ~ 30 test cases and will be updated later.
**Use This command** to run the python test case: python -m pytest tests/testForRecommendation.py -v
## Requirements
  - Python 3.7 or newer version is needed to run this.
## Run to see Recommendations
  - Run: python GameRecommendationAlgorithm.py
##### What the result looks like
=====================================================================
║                   Game Recommendation System                      ║
=====================================================================
Target Player ID : 100
Name             : Farah
Favourite Genre  : Horror
*********************************************************************
  1   Silent Hill 2 (Remastered)                         score=6.79  genres=['Horror']
  2   Silent Hill 2 GOTY Edition                         score=6.79  genres=['Horror']
  3   Metal Gear Solid 3: Snake Eater GOTY Edition       score=6.72  genres=['Action']
  4   Batman: Arkham City Definitive Edition             score=6.65  genres=['Action']
  5   Resident Evil 4 Complete Edition                   score=6.65  genres=['Horror', 'Action']
  6   Alan Wake 2 Complete Edition                       score=6.58  genres=['Horror', 'Action']
  7   Alan Wake 2 GOTY Edition                           score=6.58  genres=['Horror', 'Action']
  8   Alan Wake 2 Definitive Edition                     score=6.58  genres=['Horror', 'Action']
  9   Alien: Isolation GOTY Edition                      score=6.44  genres=['Horror']
  10  Dead Space Remake GOTY Edition                     score=6.37  genres=['Horror']
  11  Dead Space Remake Complete Edition                 score=6.37  genres=['Horror']
  12  SOMA (Remastered)                                  score=6.37  genres=['Horror']
  13  Elden Ring Deluxe Edition                          score=6.37  genres=['RPG', 'Action']
  14  SOMA Complete Edition                              score=6.37  genres=['Horror']
  15  Control GOTY Edition                               score=6.23  genres=['Action']
  16  Control                                            score=6.23  genres=['Action']
  17  Control Definitive Edition                         score=6.23  genres=['Action']
  18  Hades GOTY Edition                                 score=6.04  genres=['Action', 'RPG']
  19  Cyberpunk 2077 GOTY Edition                        score=5.85  genres=['RPG', 'Action']
  20  Cyberpunk 2077 Deluxe Edition                      score=5.85  genres=['RPG', 'Action']
### Interpretation
  - Farrah's player ID is 100, and Farrah is Horror games fans. Based on our algorithm, the top recommendation for Farrah is Silent Hill 2 (Remasted)
## Run to see Graphs
  - Install: python -m pip install networkx
  - Install: pip install matplotlib
  - Run: python graph_drawing.py
### Interpretation
  - Each node represents a player and each edge represents a connection between players based on the similariy metric defined. (This will show how 100 players are connected to each other)
  - SCCs computed using Tarjan's algorithm show groups of players where each player is reachable from every other player in the same group
## Test Cases
 
 | Core: Test Case | Input | Expected | Actual |
 |-----------------|-------|----------|--------|
 |T1-typical player |Id=’009’ |Top results-Simulation, score for Microsoft Flight Simulator= 8.37 no duplicate games |Microsoft Flight Simulator Score = 8.37, genre – simulation, no duplicate games found Passed |
