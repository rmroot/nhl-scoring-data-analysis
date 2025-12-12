import pandas as pd

#utility function for loading and cleaning the data.
def load_and_clean_games_data(csv_path="./data/all_teams.csv"):
    games_all_data_df = pd.read_csv(csv_path)
    #regular season game stats
    games_df = games_all_data_df[
        (games_all_data_df["situation"] == "all") & 
        (games_all_data_df["playoffGame"] == 0)
    ].copy()
    #data about game date for analysis
    games_df["game_date"] = pd.to_datetime(games_df["gameDate"], format="%Y%m%d")
    games_df["year"] = games_df["game_date"].dt.year
    games_df["month"] = games_df["game_date"].dt.month
    games_df["day"] = games_df["game_date"].dt.day
    games_df["day_of_week"] = games_df["game_date"].dt.day_name()
    #filter out one regular season game played in May
    #It was a makeup game. No other games played in May
    #also there is a data entry for "HOME" and "AWAY" for each game
    #filter duplicates
    games_df = games_df[(games_df["month"] != 5) & (games_df['home_or_away'] == 'HOME')]
    #apply the season for filtering out lockout and covid shortened seasons
    def applySeason(data_row):
        year = data_row['year']
        if data_row['month'] < 8:
            return f"{year-1}-{year}"
        else:
            return f"{year}-{year+1}"
    games_df['season'] = games_df.apply(applySeason, axis=1)
    filter_seasons = ['2012-2013', '2019-2020', '2020-2021']
    games_df = games_df[~games_df['season'].isin(filter_seasons)]
    #calculate the total goals for a game
    games_df['totalGoals'] = games_df["goalsFor"] + games_df["goalsAgainst"]
    return games_df