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


def requestTeamRecord(team: str, year: int, isRefresh: bool = False):
    jsonFileName = f"teamData/{team}_{year}.json".replace(" ", "")
    if (isRefresh is False):
        if (os.path.exists(jsonFileName)):
            with open(jsonFileName, "r") as jsonFile:
                statsDict = json.load(jsonFile)
            return statsDict

    dataFrame = apiCall("https://api.collegefootballdata.com/games", team, year)
    print(dataFrame.loc[5])


def requestTeamData(team: str, year: int, isRefresh: bool = False) -> dict:

    jsonFileName = f"teamData/{team}_{year}.json".replace(" ", "")

    if (isRefresh is False):
        if (os.path.exists(jsonFileName)):
            with open(jsonFileName, "r") as jsonFile:
                statsDict = json.load(jsonFile)
            return statsDict

    dataFrame = apiCall("https://api.collegefootballdata.com/stats/season", team, year)
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

    teamOneStatsDict = requestTeamData("Oregon State", 2025)
    teamTwoStatsDict = requestTeamData("Oregon", 2025)
    teamOneRatesDict = rawStatsToRates(teamOneStatsDict)
    teamTwoRatesDict = rawStatsToRates(teamTwoStatsDict)

    print(f"Team 1:\n{teamOneRatesDict}")
    print(f"Team 2:\n{teamTwoRatesDict}")

    requestTeamRecord("Oregon State", 2024)
