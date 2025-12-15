import pandas as pd

#utility function for loading and cleaning the MoneyPuck data.
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

def set_over_hit(row):
    if row['FINAL_SCORE'] == row['OVER']:
        return 'push'
    elif row['FINAL_SCORE'] > row['OVER']:
        return True
    else:
        return False
    
def set_under_hit(row):
    if row['FINAL_SCORE'] == row['UNDER']:
        return 'push'
    elif row['FINAL_SCORE'] < row['UNDER']:
        return True
    else:
        return False

#load and clean over under excel data from BigDataBall
def load_and_clean_over_under_data():
    games_all_data_df = pd.read_excel('./data/2024-2025_NHL_Box_Score_Team-Stats.xlsx', sheet_name="NHL-2024-25-TEAM", header=1)
    games_all_data_df.columns = (
    games_all_data_df.columns
        .str.replace('\n', '_', regex=True)
        .str.replace(' ', '_', regex=True)
        .str.replace('O/U', 'OVER_UNDER', regex=True)
    )
    #data about game date for analysis
    games_all_data_df["DATE"] = pd.to_datetime(games_all_data_df["DATE"], format="%m/%d/%y")
    games_all_data_df["YEAR"] = games_all_data_df["DATE"].dt.year
    games_all_data_df["MONTH"] = games_all_data_df["DATE"].dt.month
    games_all_data_df["DAY"] = games_all_data_df["DATE"].dt.day
    games_all_data_df["DAY_OF_WEEK"] = games_all_data_df["DATE"].dt.day_name()
    #parse O/U columns into seperate columns for Over and Under and odds columns
    pattern = r'(?P<number>[\d\.]+)(?P<ou>[ou])\s*(?P<odds>[+-]?\d+)'
    parsed = games_all_data_df['CLOSING_OVER_UNDER'].str.extract(pattern)
    games_all_data_df['OVER'] = parsed.apply(lambda row: row['number'] if row['ou'] == 'o' else '', axis=1)
    games_all_data_df['UNDER'] = parsed.apply(lambda row: row['number'] if row['ou'] == 'u' else '', axis=1)
    games_all_data_df['UNDER_ODDS'] = parsed.apply(lambda row: row['odds'] if row['ou'] == 'u' else '', axis=1)
    games_all_data_df['OVER_ODDS'] = parsed.apply(lambda row: row['odds'] if row['ou'] == 'o' else '', axis=1)
    #only include columns we are intersted in
    games_data_df = games_all_data_df[['GAME-ID',"TEAMS", "FINAL_SCORE", "VENUE", "YEAR", "MONTH", "DAY", "DAY_OF_WEEK", "DATE", "OVER", "UNDER", "OVER_ODDS", "UNDER_ODDS"]]
    #the home and away teams have a row for every game.
    #combine those into one row with a final score
    combined_games_df = (
        games_data_df
        .groupby('GAME-ID', as_index=False)
        .agg({
            'TEAMS': ' & '.join,           # join team names with ' & '
            'FINAL_SCORE': 'sum',          # sum the scores
            'VENUE': 'first',              # keep first (or use another aggregation if needed)
            'YEAR': 'first',
            'MONTH': 'first',
            'DAY': 'first',
            'DAY_OF_WEEK': 'first',
            'DATE': 'first',
            'OVER': 'max',                 # get the non-empty value
            'UNDER': 'max',                # get the non-empty value
            'OVER_ODDS': 'max',            # get the non-empty value
            'UNDER_ODDS': 'max'   
        })
    )
    #set over/under columns as numberic
    cols_to_float = ['OVER', 'UNDER', 'FINAL_SCORE', 'OVER_ODDS', 'UNDER_ODDS']
    for col in cols_to_float:
        combined_games_df[col] = pd.to_numeric(combined_games_df[col], errors='coerce')
    #calculate over hits
    combined_games_df['OVER_HIT'] = combined_games_df.apply(set_over_hit, axis=1)
    combined_games_df['UNDER_HIT'] = combined_games_df.apply(set_under_hit, axis=1)
    #return cleaned data
    return combined_games_df