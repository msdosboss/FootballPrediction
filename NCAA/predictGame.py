from cfdApi import requestTeamGame
from cfdApi import requestTeamData
from cfdApi import rawStatsToRates
from logisticalRegres import createFeatures
from logisticalRegres import loadModel

import pandas as pd

import argparse


def predictGame(team1: str, team2: str, year: int = 2025, week: int = 2):
    game = requestTeamGame(team1, year, week)
    game["team1"] = rawStatsToRates(requestTeamData(team1, year))
    game["team2"] = rawStatsToRates(requestTeamData(team2, year))

    gameFeature = createFeatures([game])[0]

    df = pd.DataFrame(gameFeature, index=[0])

    X = df.drop(columns=["winner"])

    model, scaler = loadModel()

    X = scaler.transform(X)
    y = model.predict(X)

    if (y[0] == 1):
        print(f"{team1} is predicted to beat {team2}")
    else:
        print(f"{team2} is predicted to beat {team1}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get teams from command line")
    parser.add_argument('team1', type=str, help='team1')
    parser.add_argument('team2', type=str, help='team2')

    args = parser.parse_args()

    team1 = args.team1
    team2 = args.team2

    predictGame(team1, team2)
