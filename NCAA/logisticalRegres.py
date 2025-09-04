from cfdApi import createFullSeasonData
from cfdApi import safeDiv
from cfdApi import getAllTeams


def createFeatures(gamesRecord: list[dict]) -> list[dict]:
    gamesFeatures = []
    for game in gamesRecord:
        gameFeatures = {}

        gameFeatures["winner"] = game["winner"]

        # Elo difference and home field advantage are always available
        gameFeatures["eloDifference"] = safeDiv(game["team1Elo"], game["team2Elo"])
        gameFeatures["isHome"] = game["isHome"]

        if game["week"] <= 1:
            # No stats yet → set all stat features to neutral (1)
            stat_names = [
                "passEfficiencyDifference",
                "completionPercentDifference",
                "yardsPerRushDifference",
                "thirdDownConversionRateDifference",
                "fourthDownConversionRateDifference",
                "turnoverMarginDifference",
                "penaltiesDifference",
                "yardsPerPenaltyDifference",
                "yardsPerPlayDifference",
                "possessionRatioDifference",
                "sacksDifference",
                "sacksOpponentDifference",
                # opponent-related
                "passingEfficiencyOpponentDifference",
                "completionPercentOpponentDifference",
                "yardsPerRushOpponentDifference",
                "thirdDownConversionRateOpponentDifference",
                "fourthDownConversionRateOpponentDifference"
            ]
            for name in stat_names:
                gameFeatures[name] = 1

        else:
            # Offensive stat differences
            gameFeatures["passEfficiencyDifference"] = safeDiv(game["team1"]["passingEfficiency"], game["team2"]["passingEfficiency"])
            gameFeatures["completionPercentDifference"] = safeDiv(game["team1"]["completionPercent"], game["team2"]["completionPercent"])
            gameFeatures["yardsPerRushDifference"] = safeDiv(game["team1"]["yardsPerRush"], game["team2"]["yardsPerRush"])
            gameFeatures["thirdDownConversionRateDifference"] = safeDiv(game["team1"]["thirdDownConversionRate"], game["team2"]["thirdDownConversionRate"])
            gameFeatures["fourthDownConversionRateDifference"] = safeDiv(game["team1"]["fourthDownConversionRate"], game["team2"]["fourthDownConversionRate"])
            gameFeatures["turnoverMarginDifference"] = safeDiv(game["team1"]["turnoverMargin"], game["team2"]["turnoverMargin"])
            gameFeatures["penaltiesDifference"] = safeDiv(game["team1"]["penalties"], game["team2"]["penalties"])
            gameFeatures["yardsPerPenaltyDifference"] = safeDiv(game["team1"]["yardsPerPenalty"], game["team2"]["yardsPerPenalty"])
            gameFeatures["yardsPerPlayDifference"] = safeDiv(game["team1"]["yardsPerPlay"], game["team2"]["yardsPerPlay"])
            gameFeatures["possessionRatioDifference"] = safeDiv(game["team1"]["possessionRatio"], game["team2"]["possessionRatio"])
            gameFeatures["sacksDifference"] = safeDiv(game["team1"]["sacks"], game["team2"]["sacks"])
            gameFeatures["sacksOpponentDifference"] = safeDiv(game["team1"]["sacksOpponent"], game["team2"]["sacksOpponent"])

            # Defensive (opponent) stat differences
            gameFeatures["passingEfficiencyOpponentDifference"] = safeDiv(game["team1"]["passingefficiencyOpponent"], game["team2"]["passingefficiencyOpponent"])
            gameFeatures["completionPercentOpponentDifference"] = safeDiv(game["team1"]["completionPercentOpponent"], game["team2"]["completionPercentOpponent"])
            gameFeatures["yardsPerRushOpponentDifference"] = safeDiv(game["team1"]["yardsPerRushOpponent"], game["team2"]["yardsPerRushOpponent"])
            gameFeatures["thirdDownConversionRateOpponentDifference"] = safeDiv(game["team1"]["thirdDownConversionRateOpponent"], game["team2"]["thirdDownConversionRateOpponent"])
            gameFeatures["fourthDownConversionRateOpponentDifference"] = safeDiv(game["team1"]["fourthDownConversionRateOpponent"], game["team2"]["fourthDownConversionRateOpponent"])

        gamesFeatures.append(gameFeatures)

    return gamesFeatures


if __name__ == "__main__":
    teamsList = getAllTeams(2024)
    gamesRecord = createFullSeasonData(teamsList, 2024)
    gamesFeatures = createFeatures(gamesRecord)
    print(gamesFeatures[1])
