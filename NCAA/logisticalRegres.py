from cfdApi import createFullSeasonData
from cfdApi import safeDiv
from cfdApi import getAllTeams

import pickle
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

def createDataSet(gamesFeatures: list[dict]):
    df = pd.DataFrame(gamesFeatures)

    X = df.drop(columns=["winner"])
    y = df["winner"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    return X_train, y_train, X_test, y_test


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


def trainModel(X_train: object, y_train: object, scaler: object) -> object:
    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)

    with open("log_reg_model.pkl", "wb") as f:
        pickle.dump({"model": model, "scaler": scaler}, f)

    return model


def loadModel(modelFileName: str = "log_reg_model") -> object:
    with open(modelFileName, "rb") as f:
        data = pickle.load(f)

    return data["model"], data["scaler"]


def evalulateModel(model: object, X_test, y_test):
    y_pred = model.predict(X_test)
    print(f"Accuracy: {accuracy_score(y_test, y_pred)}")


def printFeatureImportance(model, featuresNames):
    feature_importance = pd.DataFrame({
        "feature": featuresNames,
        "coefficient": model.coef_[0]
    }).sort_values("coefficient", ascending=False)

    print(feature_importance)


if __name__ == "__main__":
    teamsList = getAllTeams(2024)
    gamesRecord = createFullSeasonData(teamsList, 2024)
    gamesFeatures = createFeatures(gamesRecord)

    X_train, y_train, X_test, y_test = createDataSet(gamesFeatures)

    featuresNames = X_train.columns

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    model = trainModel(X_train, y_train, scaler)
    evalulateModel(model, X_test, y_test)
    printFeatureImportance(model, featuresNames)

    X_train, y_train, X_test, y_test = createDataSet(gamesFeatures)
    model = RandomForestClassifier(n_estimators=500, random_state=42)
    model.fit(X_train, y_train)
    print("randomForest accuracy: " + str(model.score(X_test, y_test)))

    model = XGBClassifier(n_estimators=500, learning_rate=0.05, max_depth=4, random_state=42)
    model.fit(X_train, y_train)
    print("xgb accuracy: " + str(model.score(X_test, y_test)))
