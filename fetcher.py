# Key (for reference): 2B81229B06DF76305388DA3288651800
# Domain (for reference): UMich Student Proj

import requests
import json
import os
import time
import xml.etree.ElementTree as ET

apiKey = "2B81229B06DF76305388DA3288651800"
maxCallsPerDiem = 100000
cachingdir = "gamesCache"

# grabs xml for members of a given steam community group
# examples: -MHW-, SteamDB
def fetch_group_members(group_name, page=1):
    # url to fetch group members in an xml
    url = f"https://steamcommunity.com/groups/{group_name}/memberslistxml/?xml=1&p={page}"

    # make request
    response = requests.get(url)

    # check for errors
    if response.status_code != 200:
        print("Error fetching page:", response.status_code)
        return None

    # return xml as text
    return response.text

# grab relevant info from one page of the xml and return list of ids
def extract_steamids(xml_text):
    # holds ids
    steamids = []

    # used to parse xml
    root = ET.fromstring(xml_text)

    # Every member is inside <members><steamID64>...</steamID64></members>
    for elem in root.iter("steamID64"):
        steamids.append(elem.text)

    # return as list
    return steamids

# grab every member if group has multiple pages
def get_all_group_members(group_name):
    # holds ids
    all_steamids = []
    # start from 1
    page = 1

    # loop until complete
    while True:
        # fetch xml for current page
        xml_text = fetch_group_members(group_name, page)

        # check if done
        if xml_text is None:
            break

        # extract ids from xml
        steamids = extract_steamids(xml_text)

        # check if done
        if not steamids:
            break

        # not necesssary but helps
        print("Finished Fetching" + str(len(steamids)) + " IDs from page " + str(page))
        all_steamids.extend(steamids)
        time.sleep(1)
        page += 1

    print("Finished Fetching All IDs. Total IDs fetched: " + str(len(all_steamids)))
    return all_steamids

# save ids to file
def saveToFile(ids):
    with open("steam_ids.txt", "w") as f:
        for sid in ids:
            f.write(sid + "\n")

# load ids from file
def loadFile(filename="steam_ids.txt"):
    with open(filename, "r") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

os.makedirs(cachingdir, exist_ok=True)

# fetching games helper, dumps to json in the gamesCache folder
def fetch_games(id):
    # make cache path for this id
    cache_path = os.path.join(cachingdir, f"{id}.json")

    # if this id is cached, load and return
    if os.path.exists(cache_path):
        with open(cache_path, "r") as f:
            return json.load(f)
        
    # beginning of steam api call url from:
    # https://developer.valvesoftware.com/wiki/Steam_Web_API#GetUserStatsForGame_(v0002)
    url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"

    params = {
        "key": apiKey,
        "steamid": id,
        "format": "json",
        # optional args for the relevant info
        "include_appinfo": 1,
        "include_played_free_games": 1
    }

    # attempt the call
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
    except Exception as e:
        print(f"Error fetching {id}: {e}")
        return None

    # cache result
    with open(cache_path, "w") as f:
        json.dump(data, f, indent=2)

    # just do 1 call per second just in case
    time.sleep(1)

    return data

# loop through using helper
def get_all_games(ids):
    for sid in ids:
        print("Fetching games for Steam ID:", sid)
        fetch_games(sid)

def main():
    # define a group name, steamdb is a large one to use. more can be used for more data
    # just to check for now, using -MHW- since it's much smaller
    # group_name = "-MHW-"

    # get all member ids
    # ids = get_all_group_members(group_name)

    # save it to a text file
    # saveToFile(ids)

    # load from file
    # ids = loadFile("steam_ids.txt")

    # get all games and save to a cache
    # get_all_games(ids)

    # basic command line interface
    print("SteamAPI fetcher")

    # loop to select options with basic command interface
    while True:
        print("\nOptions:")
        print("1. Fetch group member IDs")
        print("2. Fetch games for member IDs in cache (steam_ids.txt)")
        print("3. Exit")
        print("(Note: Make sure to rename any existing steam_ids.txt files or any gamesCache folders prior to running any options to avoid overwriting them.)")

        choice = input("Enter a number (1-3):")

        match choice:
            case "1":
                group_name = input("Enter a Steam group name (example: -MHW-): ")
                ids = get_all_group_members(group_name)
                saveToFile(ids)
                print("Finished! IDs saved to steam_ids.txt")
            case "2":
                if not os.path.exists("steam_ids.txt"):
                    print("No steam_ids.txt file found. Please run option 1 first.")
                    continue
                ids = loadFile("steam_ids.txt")
                get_all_games(ids)
                print("Finished fetching games for all IDs.")
            case "3":
                print("Bye bye!")
                break
            case _:
                print("Invalid choice. Please enter a number between 1 and 3.")

if __name__ == '__main__':
    main()