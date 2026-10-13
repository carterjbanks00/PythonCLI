This is the README for the data portions of this project.

# Data Sources
## Data Source 1:
Steam IDs from the -MHW- Steam group
URL: https://steamcommunity.com/groups/-MHW-/memberslistxml/?xml=1&p=1
Format: XML (converted to .txt)
Description: Unique identifying ID numbers for each Steam user in the -MHW- user group.
Example: 76561198885273212

## Data Source 2:
Steam game ownership data
Base URL: https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/
Example URL: http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=XXXXXXXXXXXXXXXXX&steamid=76561197960434622&format=json
URL note: API key is required, see Data Access Techniques below
Format: json
Description: jsons containing the following relevant information (each user is represented by one unique json, titled [userid.json]):
1. The user's games owned
2. Game appids in the user's library
3. The user's playtime for that game
4. The game's name
5. Additional metadata that I did not use
Example: 
{
  "response": {
    "game_count": 1630,
    "games": [
      {
        "appid": 10,
        "name": "Counter-Strike",
        "playtime_forever": 0,
        "img_icon_url": "6b0312cda02f5f777efa2f3318c307ff9acafbb5",
        "content_descriptorids": [
          2,
          5
        ]
      },
      [more game entries go here...]
    ]
  }
}

# Data Access Techniques
## For Data Source 1:
Used the above URL with requests.get() to retrieve XML pages from the Steam group
Created functions which accomplish the following:
1. Loop through every page for a given group and save the group member IDs as an XML file
2. Extract Steam IDs from those XML files and save them to a single .txt file
3. Save the .txt file locally
See README.md for more information on fetcher.py, the file I used for API calls

## For Data Source 2:
Used the web API above along with an API key that I signed up for in conjunction with the Steam IDs from Data Source 1
Used the below format to query the API:
    url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"

    params = {
        "key": apiKey,
        "steamid": id,
        "format": "json",
        # optional args for the relevant info
        "include_appinfo": 1,
        "include_played_free_games": 1
    }
Saved each json in a unique file named [steamid].json in a folder named gamesCache

# Data Summary
Total users processed: 38024
Relevant fields:
Data Source 1:
1. Steam ID

Data Source 2:
1. appid (game ID)
2. name (game title)
3. playtime_forever (user's total playtime for that title in minutes)
4. img_icon_url (unused)
5. content_descriptorids (unused)
json titles are the Steam IDs from Data Source 1

# Additional notes:
Some users' data couldn't be retrieved due to privacy settings, so they were skipped.

I chose -MHW- as my group for two reasons: one, it is a fairly large group, and two, because it's centered around a specific game (Monster Hunter: World), it made it easier for me to see whether the insights I was getting from the data made sense, or if my algorithms or code needed tweaking. For example, expecting Monster Hunter: World to have a lot of, if not the highest number of neighbors.
