import requests
import pandas as pd
import json
import os
import hashlib


with open("CFDkey", "r") as apiFile:
    API_KEY = apiFile.read().replace("\n", "")


def apiCall(url: str, params: dict):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    print("api call being made")
    # If it's not a list, wrap it in one
    if isinstance(data, dict):
        if len(data) == 0:
            return pd.DataFrame()  # empty response
        if "message" in data:  # error response from API
            print(f"API error: {data}")
            return pd.DataFrame()
        data = [data]

    return pd.DataFrame(data)


def getAllTeams(year: int, isRefresh: bool = False) -> list[str]:
    jsonFileName = f"teamData/teamsList_{year}.json"
    if (isRefresh is False):
        if (os.path.exists(jsonFileName)):
            with open(jsonFileName, "r") as jsonFile:
                return json.load(jsonFile)

    url = "https://api.collegefootballdata.com/teams/fbs"
    params = {"year": year}
    dataFrame = apiCall(url, params)

    teamsInfoList = dataFrame.values.tolist()
    teamsList = []
    for teamInfoList in teamsInfoList:
        # extracting the name from the teams info
        teamsList.append(teamInfoList[1])

    with open(jsonFileName, "w") as jsonFile:
        json.dump(teamsList, jsonFile)

    return teamsList


def createFullSeasonData(teams: list[str], year: int, isRefresh: bool = False):
    # Sort teams so the hash is consistent regardless of input order
    teams_sorted = sorted(teams)
    teams_str = "_".join(teams_sorted)

    teams_hash = hashlib.sha256(teams_str.encode()).hexdigest()[:8]

    jsonFileName = f"teamData/{year}_{teams_hash}_season_data.json"

    if not isRefresh and os.path.exists(jsonFileName):
        with open(jsonFileName, "r") as jsonFile:
            return json.load(jsonFile)

    fullSeasonRecord = []
    for team in teams_sorted:
        fullSeasonRecord.extend(createSeasonData(team, year, isRefresh))

    with open(jsonFileName, "w") as jsonFile:
        json.dump(fullSeasonRecord, jsonFile)

    return fullSeasonRecord


def createSeasonData(team: str, year: int, isRefresh: bool = False):
    gamesRecord = requestTeamRecord(team, year, isRefresh)

    i = 0
    while (i < len(gamesRecord)):
        endWeek = gamesRecord[i]["week"] - 1

        teamData = requestTeamData(gamesRecord[i]["team1"], year, endWeek)
        if (teamData == -1):
            del gamesRecord[i]
            continue

        try:
            teamData = rawStatsToRates(teamData)
        except KeyError as e:
            print(f"Missing key {e} for team {gamesRecord[i]['team1']} in week {endWeek}, data={teamData}")
            raise

        gamesRecord[i]["team1"] = teamData
        teamData = requestTeamData(gamesRecord[i]["team2"], year, endWeek)
        if (teamData == -1):
            del gamesRecord[i]
            continue

        try:
            teamData = rawStatsToRates(teamData)
        except KeyError as e:
            print(f"Missing key {e} for team {gamesRecord[i]['team2']} in week {endWeek}, data={teamData}")
            raise

        gamesRecord[i]["team2"] = teamData
        i += 1

    return gamesRecord


def requestTeamGame(team: str, year: int, week: int, isRefresh: bool = False) -> dict:
    jsonFileName = f"teamData/{team}_{year}_{week}record.json".replace(" ", "")
    if (isRefresh is False):
        if (os.path.exists(jsonFileName)):
            with open(jsonFileName, "r") as jsonFile:
                gameRecord = json.load(jsonFile)
            return gameRecord

    params = {
        "team": team,
        "year": year,
        "week": week
    }

    dataFrame = apiCall("https://api.collegefootballdata.com/games", params)

    locationStr = ""
    opponentLocationStr = ""

    if (dataFrame.loc[0, "homeTeam"] == team):
        locationStr = "home"
        opponentLocationStr = "away"
    else:
        locationStr = "away"
        opponentLocationStr = "home"

    gameRecord = {}
    gameRecord["team1"] = str(dataFrame.loc[0, f"{locationStr}Team"])
    gameRecord["team2"] = str(dataFrame.loc[0, f"{opponentLocationStr}Team"])

    if (dataFrame.loc[0, f"{locationStr}PregameElo"] is None):
        gameRecord["team1Elo"] = 1000  # defaults at 1000
    else:
        gameRecord["team1Elo"] = int(dataFrame.loc[0, f"{locationStr}PregameElo"])

    if (dataFrame.loc[0, f"{opponentLocationStr}PregameElo"] is None):
        gameRecord["team2Elo"] = 1000
    else:
        gameRecord["team2Elo"] = int(dataFrame.loc[0, f"{opponentLocationStr}PregameElo"])

    gameRecord["isHome"] = 1 if (locationStr == "home") else 0

    if (dataFrame.loc[0, f"{locationStr}Points"] is None):
        gameRecord["winner"] = None
    else:
        gameRecord["winner"] = 1 if (dataFrame.loc[0, f"{locationStr}Points"] > dataFrame.loc[0, f"{opponentLocationStr}Points"]) else 0

    gameRecord["week"] = int(dataFrame.loc[0, "week"])

    with open(jsonFileName, "w") as jsonFile:
        json.dump(gameRecord, jsonFile)

    return gameRecord


def requestTeamRecord(team: str, year: int, isRefresh: bool = False) -> list[dict]:
    jsonFileName = f"teamData/{team}_{year}_record.json".replace(" ", "")
    # THIS SHOULD REMOVED AT SOME POINT
    isRefresh = False
    # THIS SHOULD REMOVED AT SOME POINT
    if (isRefresh is False):
        if (os.path.exists(jsonFileName)):
            with open(jsonFileName, "r") as jsonFile:
                gamesRecord = json.load(jsonFile)
            return gamesRecord

    params = {
        "team": team,
        "year": year
    }

    dataFrame = apiCall("https://api.collegefootballdata.com/games", params)
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
        gameRecord["team1Elo"] = game[f"{locationStr}PregameElo"]
        gameRecord["team2Elo"] = game[f"{opponentLocationStr}PregameElo"]
        gameRecord["isHome"] = 1 if (locationStr == "home") else 0
        gameRecord["winner"] = 1 if (game[f"{locationStr}Points"] > game[f"{opponentLocationStr}Points"]) else 0
        gameRecord["week"] = game["week"]
        gamesRecord.append(gameRecord)

    gamesRecordJson = json.dumps(gamesRecord)

    with open(jsonFileName, "w") as jsonFile:
        jsonFile.write(gamesRecordJson)

    return gamesRecord


def requestTeamData(team: str, year: int, endWeek: int = 20, isRefresh: bool = False) -> dict:
    jsonFileName = f"teamData/{team}_{year}_{endWeek}.json".replace(" ", "")
    # THIS SHOULD REMOVED AT SOME POINT
    isRefresh = False
    # THIS SHOULD REMOVED AT SOME POINT

    if (isRefresh is False):
        if (os.path.exists(jsonFileName)):
            with open(jsonFileName, "r") as jsonFile:
                statsDict = json.load(jsonFile)
                if "_no_data" in statsDict:
                    return -1
            return statsDict

    params = {
        "team": team,
        "year": year,
        "endWeek": endWeek  # default is 20 meaning all weeks
    }

    dataFrame = apiCall("https://api.collegefootballdata.com/stats/season", params)

    if dataFrame.empty:
        print(f"{team} does not have any data for year {year}")
        statsDict = {"_no_data": True}  # sentinel flag
        with open(jsonFileName, "w") as jsonFile:
            json.dump(statsDict, jsonFile)
        return -1

    statsDict = dataFrame.set_index("statName")["statValue"].to_dict()

    statsDictJson = json.dumps(statsDict)

    with open(jsonFileName, "w") as jsonFile:
        jsonFile.write(statsDictJson)

    return statsDict


def safeDiv(a, b):
    return a / b if b != 0 else 1


def rawStatsToRates(statsDict: dict) -> dict:
    def keyCheck(k):
        return statsDict.get(k, 0)  # default to 0 if missing

    ratesDict = {}
    ratesDict["passingEfficiency"] = safeDiv(keyCheck("netPassingYards"), keyCheck("passAttempts"))
    ratesDict["completionPercent"] = safeDiv(keyCheck("passCompletions"), keyCheck("passAttempts"))
    ratesDict["yardsPerRush"] = safeDiv(keyCheck("rushingYards"), keyCheck("rushingAttempts"))
    ratesDict["thirdDownConversionRate"] = safeDiv(keyCheck("thirdDownConversions"), keyCheck("thirdDowns"))
    ratesDict["fourthDownConversionRate"] = safeDiv(keyCheck("fourthDownConversions"), keyCheck("fourthDowns"))

    ratesDict["turnoverMargin"] = keyCheck("turnoversOpponent") - keyCheck("turnovers")
    ratesDict["penalties"] = keyCheck("penalties")
    ratesDict["yardsPerPenalty"] = safeDiv(keyCheck("penaltyYards"), keyCheck("penalties"))
    ratesDict["yardsPerPlay"] = safeDiv(
        keyCheck("totalYards"), keyCheck("rushingAttempts") + keyCheck("passAttempts")
    )
    ratesDict["possessionRatio"] = safeDiv(keyCheck("possessionTime"), keyCheck("possessionTimeOpponent"))
    ratesDict["sacks"] = keyCheck("sacks")
    ratesDict["sacksOpponent"] = keyCheck("sacksOpponent")

    ratesDict["passingefficiencyOpponent"] = safeDiv(
        keyCheck("netPassingYardsOpponent"), keyCheck("passAttemptsOpponent")
    )
    ratesDict["completionPercentOpponent"] = safeDiv(
        keyCheck("passCompletionsOpponent"), keyCheck("passAttemptsOpponent")
    )
    ratesDict["yardsPerRushOpponent"] = safeDiv(
        keyCheck("rushingYardsOpponent"), keyCheck("rushingAttemptsOpponent")
    )
    ratesDict["thirdDownConversionRateOpponent"] = safeDiv(
        keyCheck("thirdDownConversionsOpponent"), keyCheck("thirdDownsOpponent")
    )
    ratesDict["fourthDownConversionRateOpponent"] = safeDiv(
        keyCheck("fourthDownConversionsOpponent"), keyCheck("fourthDownsOpponent")
    )

    return ratesDict


if __name__ == "__main__":
    print(requestTeamData("Boston College", 2024, 1))
