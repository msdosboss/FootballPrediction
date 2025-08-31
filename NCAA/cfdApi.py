import requests
import pandas as pd


def requestTeamData(team, year):
    apiFile = open("CFDkey", "r")
    API_KEY = apiFile.read().replace("\n", "")
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    url = "https://api.collegefootballdata.com/stats/season"
    params = {
        "year": year,
        "team": team
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()


    df = pd.DataFrame(data)
    # Save as CSV
    df.to_csv(f"{team}_{year}_stats.csv", index=False)
    
    return df.set_index("statName")["statValue"].to_dict()



statsDict = requestTeamData("Oregon", 2025)

print(statsDict)

