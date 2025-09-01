import requests
import pandas as pd
import json
import os


with open("CFDkey", "r") as apiFile:
    API_KEY = apiFile.read().replace("\n", "")


def apiCall(url: str, team: str, year: str):
    headers = {"Authorization": f"Bearer {API_KEY}"}

    params = {
        "year": year,
        "team": team
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    return pd.DataFrame(data)


def createFullSeasonData(teams: list[str], year: int, isRefresh: bool = False):
    jsonFileName = f"teamData/{year}_season_data.json"
    if (isRefresh is False):
        if (os.path.exists(jsonFileName)):
            with open(jsonFileName, "r") as jsonFile:
                fullSeasonRecord = json.load(jsonFile)
            return fullSeasonRecord
    
    fullSeasonRecord = []
    for team in teams:
        fullSeasonRecord = fullSeasonRecord + (createSeasonData(team, year, isRefresh))

    fullSeasonRecordJson = json.dumps(fullSeasonRecord)
    with open(jsonFileName, "w") as jsonFile:
        jsonFile.write(fullSeasonRecordJson)

    return fullSeasonRecord 


def createSeasonData(team: str, year: int, isRefresh: bool = False):
    gamesRecord = requestTeamRecord(team, year, isRefresh)
    indexToRemove = []
    for i in range(len(gamesRecord)):
        teamData = requestTeamData(gamesRecord[i]["team1"], year)
        if (teamData == -1):
            indexToRemove.append(i)
            continue
        gamesRecord[i]["team1"] = teamData 
        teamData = requestTeamData(gamesRecord[i]["team2"], year)
        if (teamData == -1):
            indexToRemove.append(i)
            continue
        gamesRecord[i]["team2"] = teamData

    for i in indexToRemove:
        del gamesRecord[i]

    return gamesRecord

def requestTeamRecord(team: str, year: int, isRefresh: bool = False):
    jsonFileName = f"teamData/{team}_{year}_record.json".replace(" ", "")
    if (isRefresh is False):
        if (os.path.exists(jsonFileName)):
            with open(jsonFileName, "r") as jsonFile:
                gamesRecord = json.load(jsonFile)
            return gamesRecord

    dataFrame = apiCall("https://api.collegefootballdata.com/games", team, year)
    gamesRecord = []
    for idx, game in dataFrame.iterrows():
        locationStr = ""
        opponentLocationStr = ""
        if (game["homeTeam"] == team):
            locationStr = "home"
            opponentLocationStr = "away"
        else:
            locationStr = "away"
            opponentLocationStr = "home"
        
        gameRecord = {}
        gameRecord["team1"] = game[f"{locationStr}Team"]
        gameRecord["team2"] = game[f"{opponentLocationStr}Team"]
        gameRecord["isHome"] = 1 if (locationStr == "home") else 0 
        gameRecord["winner"] = 1 if (game[f"{locationStr}Points"] > game[f"{opponentLocationStr}Points"]) else 0
        
        gamesRecord.append(gameRecord)

    gamesRecordJson = json.dumps(gamesRecord)

    with open(jsonFileName, "w") as jsonFile:
        jsonFile.write(gamesRecordJson)

    return gamesRecord

def requestTeamData(team: str, year: int, isRefresh: bool = False) -> dict:

    jsonFileName = f"teamData/{team}_{year}.json".replace(" ", "")

    if (isRefresh is False):
        if (os.path.exists(jsonFileName)):
            with open(jsonFileName, "r") as jsonFile:
                statsDict = json.load(jsonFile)
            return statsDict

    dataFrame = apiCall("https://api.collegefootballdata.com/stats/season", team, year)

    if (dataFrame.empty):
        print(f"{team} does not have any data for year {year}")
        return -1

    statsDict = dataFrame.set_index("statName")["statValue"].to_dict()

    dataFrame = apiCall("https://api.collegefootballdata.com/ratings/elo", team, year)

    statsDict["elo"] = int(dataFrame.loc[0, "elo"])

    statsDictJson = json.dumps(statsDict)

    with open(jsonFileName, "w") as jsonFile:
        jsonFile.write(statsDictJson)

    return statsDict


def rawStatsToRates(statsDict: dict) -> dict:
    ratesDict = {}

    ratesDict["passingEfficiency"] = statsDict["netPassingYards"] / statsDict["passAttempts"]
    ratesDict["completionPercent"] = statsDict["passCompletions"] / statsDict["passAttempts"]
    ratesDict["yardsPerRush"] = statsDict["rushingYards"] / statsDict["rushingAttempts"]
    ratesDict["thirdDownConversionRate"] = statsDict["thirdDownConversions"] / statsDict["thirdDowns"]
    ratesDict["fourthDownConversionRate"] = statsDict["fourthDownConversions"] / statsDict["fourthDowns"]

    ratesDict["turnoverMargin"] = statsDict["turnoversOpponent"] - statsDict["turnovers"]
    ratesDict["penalties"] = statsDict["penalties"]
    ratesDict["yardsPerPenalty"] = statsDict["penaltyYards"] / statsDict["penalties"]
    ratesDict["yardsPerPlay"] = statsDict["totalYards"] / (statsDict["rushingAttempts"] + statsDict["passAttempts"])
    ratesDict["possessionRatio"] = statsDict["possessionTime"] / statsDict["possessionTimeOpponent"]
    ratesDict["sacks"] = statsDict["sacks"]
    ratesDict["sacksOpponent"] = statsDict["sacksOpponent"]
    ratesDict["elo"] = statsDict["elo"]

    ratesDict["passingefficiencyOpponent"] = statsDict["netPassingYardsOpponent"] / statsDict["passAttemptsOpponent"]
    ratesDict["completionPercentOpponent"] = statsDict["passCompletionsOpponent"] / statsDict["passAttemptsOpponent"]
    ratesDict["yardsPerRushOpponent"] = statsDict["rushingYardsOpponent"] / statsDict["rushingAttemptsOpponent"]
    ratesDict["thirdDownConversionRateOpponent"] = statsDict["thirdDownConversionsOpponent"] / statsDict["thirdDownsOpponent"]
    ratesDict["fourthDownConversionRateOpponent"] = statsDict["fourthDownConversionsOpponent"] / statsDict["fourthDownsOpponent"]

    return ratesDict


if __name__ == "__main__":
    gamesRecord = createFullSeasonData({"Oregon State", "Oregon", "California"}, 2024)
    print(gamesRecord[0])
