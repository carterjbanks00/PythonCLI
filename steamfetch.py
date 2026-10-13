# imported fetcher just in case I need it, but probably won't since it's assumed the json folder already exists
import fetcher
import os
import json
import networkx as nx
# for read/write of the graph cache
# citation:
# https://networkx.org/documentation/stable/release/migration_guide_from_2.x_to_3.0.html#deprecated-code
import pickle
# matplotlib just in case for visualization, probably won't use it for time constraints (irl, not runtime)
import matplotlib.pyplot as plt
from itertools import combinations
from collections import defaultdict
from collections import deque
from math import log
# used for progress bar
# citation:
# https://www.geeksforgeeks.org/python/python-how-to-make-a-terminal-progress-bar-using-tqdm/
from tqdm import tqdm

# loads the data from the folder of jsons
def loadUserData(folderPath="gamesCacheInUse"):
    '''
    Loads Steam user data from the JSON files in the folderPath

    variables:
    folderPath - path to the JSON folder

    returns:
    userInfo - dict mapping Steam IDs and game data
    '''
    userInfo = {}

    for filename in os.listdir(folderPath):
        # jsons are named in the format [steamid].json
        # replace the .json with nothing so it's just id
        userID = filename.replace(".json", "")

        # make the full path for later
        fullFilePath = os.path.join(folderPath, filename)

        # try and except just in case
        try:
            with open(fullFilePath, "r") as f:
                data = json.load(f)
            # the json structure is response { games [ {gameA}, {gameB}]}
            userInfo[userID] = data.get("response", {}).get("games", [])
        
        except Exception as e:
            print("Error, could not load " + fullFilePath)
            continue

    return userInfo

# DEPRECATED - no longer needed since a version is built into buildGraph()
# helper function to get user playtime per game
def getPlaytime(games, gameID):
    '''
    Uses the games list and gameID to get the playtime for that game from the user

    variables:
    games - list of games from the user
    gameID - appid of the game

    returns:
    the playtime in minutes for that game, or 0 if not found
    '''
    for game in games:
        if game["appid"] == gameID:
            return game.get("playtime_forever", 0)
    return 0

# builds the graph
def buildGraph(userInfo):
    '''
    Builds a graph from the data in userInfo
    
    variables:
    userInfo - dict mapping Steam IDs and game data

    returns:
    gameGraph - graph made with networkx with games as nodes, edges weighted by cooccurrences in libraries

    networkx citation:
    To cite NetworkX please use the following publication:
    Aric A. Hagberg, Daniel A. Schult and Pieter J. Swart, “Exploring network structure, dynamics, and function using NetworkX”, in Proceedings of the 7th Python in Science Conference (SciPy2008), Gäel Varoquaux, Travis Vaught, and Jarrod Millman (Eds), (Pasadena, CA USA), pp. 11-15, Aug 2008
    '''
    # initialize vars
    gameGraph = nx.Graph()
    # initialize counter for game occurrences
    # using defaultdict to avoid key errors
    # citation:
    # https://www.geeksforgeeks.org/python/defaultdict-in-python/
    gameCounts = defaultdict(int)
    # initialize counter for cooccurrences
    gameWeights = defaultdict(float)

    # count games and cooccurrences
    # deprecated for loop, added tqdm for progress bar since the graph takes a long time to build
    # for games in userInfo.values():
    for games in tqdm(userInfo.values(), total=len(userInfo), desc="Building Graph"):
        # create dict to hold playtiems
        # saves on time by not calling it over and over in the inner loop
        gamePlaytimes = {}
        for game in games:
            if "appid" in game:
                gamePlaytimes[game["appid"]] = game.get("playtime_forever", 0)

        # make list of played game ids
        # saves on time by not having to check if playtime == 0 in the inner loop
        # ensure that games with a playtime of 0 are not included, to avoid free games skewing results (ie, everyone has TF2, but most people don't play it)
        playedGameIDs = []
        for gameID, playtime in gamePlaytimes.items():
            if playtime > 0:
                playedGameIDs.append(gameID)

        # DEPRECATED - replaced by playedgame
        # make list of game ids
        # gameIDs = []
        # for innergame in games:
            # if "appid" in innergame:
                # gameIDs.append(innergame["appid"])

        # add an occurrence for each game
        for gameID in playedGameIDs:
            gameCounts[gameID] += 1

        # add cooccurrences for each pair
        # itertools citation:
        # https://www.geeksforgeeks.org/python/itertools-combinations-module-python-print-possible-combinations/
        for gameIDA, gameIDB in combinations(playedGameIDs, 2):
            # weight playtime and then apply log scaling so outliers don't mess up my results
            gameWeights[(gameIDA, gameIDB)] += log(min(gamePlaytimes[gameIDA], gamePlaytimes[gameIDB]) + 1)

            # below is deprecated, had too many calls which slowed down the creation of the graph
            # playtimeA = getPlaytime(games, gameIDA)
            # playtimeB = getPlaytime(games, gameIDB)
            # ignore if either game is unplayed
            # if playtimeA == 0 or playtimeB == 0:
                # continue

            # below is deprecated, only weighted by min of two values
            # but outliwers skewed results a lot (ie, lots of time in CSGO)
            # gameWeights[(gameIDA, gameIDB)] += min(playtimeA, playtimeB)

            # below is deprecated for the non-weighted version
            # gameWeights[(gameIDA, gameIDB)] += 1
        
    # create nodes
    for gameID, count in gameCounts.items():
        # node will have gameID, number_of_owners, and the name (set later in this function)
        gameGraph.add_node(gameID, number_of_owners=count, name=None)
    
    # create edgees
    for (gameIDA, gameIDB), weight in gameWeights.items():
        gameGraph.add_edge(gameIDA, gameIDB, weight=weight)

    # set the names
    # visited is deprecated, slower than just checking if name is none
    # keep track of ids we've seen so we don't keep setting the name over and over
    # visitedID = {}
    for games in userInfo.values():
        for innergame in games:
            gamesID = innergame["appid"]
            if gamesID in gameGraph.nodes and gameGraph.nodes[gamesID]["name"] is None:
                gameGraph.nodes[gamesID]["name"] = innergame.get("name", "Unknown")
                # visitedID[gamesID] = True

    return gameGraph

# class which handles the methods with which hte user will interact with the data and graph
class SteamGraph:
    def __init__(self, userInfo):
        '''
        Initializes userInfo and builds graph

        variables:
        userInfo - dict mapping Steam IDs and ganme data
        gameGraph - graph made with networkx, games are nodes, cooccurrence weighted by playtime as edges
        '''
        self.userInfo = userInfo
        self.gameGraph = buildGraph(userInfo)

    # Interaction Mode #1
    # search games with a given term in the name, return gameID, name
    def searchGames(self, searcher):
        '''
        Given a search term, return a list of pairs (gameID, name) for which the name contains the term

        variables:
        searcher - string to use to search game names

        returns:
        searchResults - list of pairs matching the term
        '''
        searchResults = []

        # loop through
        for node, data in self.gameGraph.nodes(data=True):
            if searcher.lower() in data["name"].lower():
                # each node is a gameID, data is a dict where name is a key
                searchResults.append((node, data["name"]))
        return searchResults

    # Interaction Mode #2
    # game recommendation based off id
    def recommendGames(self, gameID, numRecs=3):
        '''
        Given a gameID, recommend [numRecs] games

        variables:
        gameID - appid of the game we're making the recommendation for
        numRecs - number of recommendations to make, default to top 3

        returns:
        recs - sorted list of top 3 recommended games as gameID, name, weight
        '''
        # check if provided gameID is in the graph
        if gameID not in self.gameGraph:
            return []
        
        # get adjacent games and their weights
        adjGames = self.gameGraph[gameID]
        recs = []

        for adj in adjGames:
            # append as a tuple of id, name, weight (strength of connection)
            recs.append((adj, self.gameGraph.nodes[adj]["name"], adjGames[adj]["weight"]))
        
        # sort by weight, descending (-x[2])
        # in event of same weight (rare), sort by name ascending (x[1])
        recs.sort(key=lambda x: (-x[2], x[1]))

        # return only the specified number
        return recs[:numRecs]

    # Interaction Mode #3
    # find shortest path between two games
    def pathFinder(self, gameIDA, gameIDB):
        '''
        Given two gameids, find the shortest path between them

        variables:
        gameIDA, gameIDB - appids for the starting and ending games

        returns:
        thePath - list of gameids representing the shortest path, along with their names
        length - length of thePath
        [], 0 if no path is found, or if either game is not in the graph

        note:
        even though nx has a built in shortest path function, I felt it was in the spirit of the project to implement my own using bfs
        '''
        # make sure both gameids are in the graph
        if gameIDA not in self.gameGraph or gameIDB not in self.gameGraph:
            return [], 0
        
        # BFS similar to kevin bacon project
        # slightly different since bacon number went actor -> movie -> actor, but this goes game -> game
        queue = deque([gameIDA])
        visited = {gameIDA}
        parents = {gameIDA: None}

        while queue:
            current = queue.popleft()

            if current == gameIDB:
                break

            for neighbor in self.gameGraph.neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parents[neighbor] = current
                    queue.append(neighbor)

        if gameIDB not in parents:
            return [], 0

        # reconstruct the path
        thePath = []
        placeTracker = gameIDB
        while placeTracker is not None:
            thePath.append((placeTracker, self.gameGraph.nodes[placeTracker].get("name", "Unknown")))
            placeTracker = parents[placeTracker]

        thePath.reverse()

        return thePath, len(thePath) - 1

    # Interaction Mode #4
    # find most central games
    def centerFold(self, numCen=1):
        '''
        Finds the most central game(s) using centrality

        variables:
        numCen - number of central games we're looking for, default to top 1

        returns:
        theCenter - list of gameids representing the most central games

        note:
        even though nx has a built in centrality function, I felt it was in the spirit of the project to implement my own using bfs
        '''
        # calc centrality (num neighbors / all nodes - 1)
        # make a dict of centrality values, convert to list of tuples (easier to work with for me cuz I'm bad with dicts), sort descending order
        centralityVals = {}

        for node in self.gameGraph.nodes():
            centralityVals[node] = self.gameGraph.degree(node) / (len(self.gameGraph.nodes) - 1)

        theCenter = []
        for key in centralityVals:
            theCenter.append((key, self.gameGraph.nodes[key].get("name", "Unknown"), centralityVals[key]))
        
        # sorts by centrality values descending, then uses id to break ties
        theCenter.sort(key=lambda x: (-x[2], x[0]))
        
        return theCenter[:numCen]

def main():
    # added way to cache the graph so it doesn't need to build at runtime
    graphFile = "steam_graph.gpickle"

    # check if cached graph is there
    # I'm sure I could've wrapped this in a function or something to make it cleaner, but since it's just used once I just implemented directly in main
    if os.path.exists(graphFile):
        print("Loading cached graph file: " + graphFile)
        with open(graphFile, "rb") as f:
            cacheGraph = pickle.load(f)
        # skip init to not rebuild the graph
        steamGraph = SteamGraph.__new__(SteamGraph)
        # manually set graph and userInfo (userInfo not needed since graph is cached)
        steamGraph.gameGraph = cacheGraph
        steamGraph.userInfo = {}
    else:
        print("No graph cache found, building from jsons")
        userInfo = loadUserData("gamesCacheInUse")
        steamGraph = SteamGraph(userInfo)
        # save it
        # IMPORTANT: resulting file, using the included jsons, is over 2 GB. PLEASE make sure you have enough space before running the code. It will take a few minutes to write the file. Comment out the below if you don't want to save it - saving takes longer than building the graph. I have also included this information in the README.
        saveChoice = input("Would you like to cache the graph to a file for later use?\n IMPORTANT: The resulting file may be large (2+ GB). Make sure you have enough space before proceeding. (Y/N): ")
        if saveChoice.lower() == "y":
            print("Caching graph to file: " + graphFile)
            with open(graphFile, "wb") as f:
                pickle.dump(steamGraph.gameGraph, f)
            print("Graph successfully constructed and cached in: " + graphFile)
        else:
            print("Graph will not be cached, proceeding to next step.")

    # Command Line Interface (uncomment once finished)
    print("Steam Grapher Interface")

    while True:
        print("\nOptions:")
        print("1. Search for games by keyword")
        print("2. Recommend games from a game ID")
        print("3. Find the shortest path between two games")
        print("4. Find the most central games")
        print("5. Exit")
        
        choice = input("Please enter a number (1-5): ")

        match choice:
            # run Interaction Mode #1
            case "1":
                term = input("Please enter a search term: ")
                results = steamGraph.searchGames(term)
                print("Search results for " + term + ":")
                for gameID, name in results:
                    print("Game ID: " + str(gameID) + " || Name: " + name)
                print("End of results.\n Would you like to perform another action?")
                decision = input("Enter 1 to perform another action, any other key to exit: ")
                if decision == "1":
                    continue
                else:
                    print("See ya!")
                    break
            
            # run Interaction Mode #2
            case "2":
                gid = input("Please enter a game ID to get recommendations for: ")
                numRecs = input("Please enter a number of recommendations to get (default is 3): ")
                if not numRecs.isdigit():
                    print("Invalid entry, defaulting to 3 recommendations.")
                    numRecs = 3
                if not gid.isdigit():
                    print("Invalid game ID entry, please enter a number for ID.")
                    continue
                recList = steamGraph.recommendGames(int(gid), int(numRecs))
                if len(recList) == 0:
                    print("Sorry, no recommendations were found. Please ensure the game ID is valid (option 1).")
                    continue
                print("Top " + str(numRecs) + " recommendations for game ID " + str(gid) + ":")
                for recID, recName, recWeight in recList:
                    print("Game ID: " + str(recID) + " || Name: " + recName + " || Recommendation Strength: " + str(recWeight))
                print("End of recommendations.\n Would you like to perform another action?")
                decision = input("Enter 1 to perform another action, any other key to exit: ")
                if decision == "1":
                    continue
                else:
                    print("See ya!")
                    break
                    
            # run Interaction Mode #3
            case "3":
                gameIDA = input("Please enter the first game ID: ")
                gameIDB = input("Please enter the second game ID: ")
                path, length = steamGraph.pathFinder(int(gameIDA), int(gameIDB))
                if length == 0:
                    print("Could not find a path between the two games. Either the path does not exist, or one of the IDs is invalid.")
                    continue
                print("Shortest path between " + str(gameIDA) + " and " + str(gameIDB) + ":")
                for gameID, gameName in path:
                    print("Game ID: " + str(gameID) + " || Name: " + gameName)
                print("Length of path found: " + str(length))
                print("End of pathfinding.\n Would you like to perform another action?")
                decision = input("Enter 1 to perform another action, any other key to exit: ")
                if decision == "1":
                    continue
                else:
                    print("See ya!")
                    break
            
            # run Interaction Mode #4
            case "4":
                cenLimits = input("Please enter a number for how many nodes you wish to limit the list to (default is 1): ")
                if not cenLimits.isdigit():
                    print("Invalid entry, defaulting to 1 central node.")
                    cenLimits = 1
                centralityValues = steamGraph.centerFold(int(cenLimits))
                for nodeID, nodeName, centralityVal in centralityValues:
                    print("Node's game ID: " + str(nodeID) + " || Name: " + nodeName + " || Degree of centrality: " + str(centralityVal))
                print("End of centrality.\n Would you like to perform another action?")
                decision = input("Enter 1 to perform another action, any other key to exit: ")
                if decision == "1":
                    continue
                else:
                    print("See ya!")
                    break

            # exit
            case "5":
                print("See ya!")
                break
                
            # invalid, try again
            case _:
                print("Sorry, invalid choice. Please enter a number between 1 and 5.")
                continue

if __name__ == '__main__':
    main()
