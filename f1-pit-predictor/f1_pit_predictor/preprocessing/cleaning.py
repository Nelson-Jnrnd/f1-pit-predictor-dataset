import pandas as pd
import numpy as np

## Rainfall -------------------------------------------------------------------
# Remove races with rain
def _process_rainfall(df: pd.DataFrame) -> pd.DataFrame:
    rain = df.groupby(['Year', 'RoundNumber', 'DriverNumber'])['Compound'].transform(lambda x: x[x.str.contains('INTERMEDIATE|WET')].count())
    return df[rain == 0].reset_index(drop=True)

## Pitstops -------------------------------------------------------------------
# Creates the target variable for the pitstop prediction
def _process_pitstops(df: pd.DataFrame) -> pd.DataFrame:
    df['PitStatusShift'] = df.groupby(['Year', 'RoundNumber', 'DriverNumber'])['PitStatus'].shift(-1, fill_value='NoPit')
    return df

## Tires ----------------------------------------------------------------------
# Creates the target variable for the tire prediction
def _process_tires(df: pd.DataFrame) -> pd.DataFrame:
    df['NextCompound'] = df.groupby(['Year', 'RoundNumber', 'DriverNumber'])['Compound'].shift(-2)
    return df

## Incomplete races -----------------------------------------------------------
# Remove races where the driver did not finish
def _incomplete_races(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby(['Year', 'RoundNumber', 'DriverNumber']).filter(lambda x: x['LapNumber'].max() + 3 >= x['TotalLaps'].max()).reset_index(drop=True)

## Remove unusual races
# Remove races with more than 4 pit stops
def _remove_unusual_races(df: pd.DataFrame) -> pd.DataFrame:
    nb_pitstops = df.groupby(['Year', 'RoundNumber', 'DriverNumber'])['NumberOfPitStops'].transform(lambda x: x.max())
    return df[nb_pitstops <= 4].reset_index(drop=True)

## TrackName ------------------------------------------------------------------
# Replace spaces with underscores
def _process_track_name(df):
    df['Track'] = df['Track'].str.replace(' ', '_')
    return df

## TrackStatus ----------------------------------------------------------------
# Convert the track status code to binary columns
def _trackStatus_to_binary(df):
    trackStatus = df['TrackStatus']
    status = pd.Series(
        np.zeros(6, dtype=np.bool_),
        index=['Green', 'Yellow', 'SC', 'Red', 'VSC', 'SC_ending']
    )
    if trackStatus == 1:
        status['Green'] = True
    if trackStatus == 2:
        status['Yellow'] = True
    if trackStatus == 4:
        status['SC'] = True
    if trackStatus == 5:
        status['Red'] = True
    if trackStatus == 6:
        status['VSC'] = True
    if trackStatus == 7:
        status['SC_ending'] = True
    return status

def _process_trackStatus(df):
    trackStatuses = df.apply(_trackStatus_to_binary, axis=1)
    return pd.concat([df.drop('TrackStatus', axis=1), trackStatuses], axis=1)

## Missing Data ----------------------------------------------------------------
def _process_missing_values(df):
    df['DriverAhead'] = df['DriverAhead'].astype('str')
    # TODO fill the missing values better
    df.fillna({
        'DistanceToDriverAhead': -1,
        'GapToLeader': -1,
        'IntervalToPositionAhead': -1,
        'DriverAhead': -1
    }, inplace=True)

    # drop all rows with missing laptime
    df.dropna(subset=['LapTime'], inplace=True)
    return df[df['LapNumber'] > 1].reset_index(drop=True)

## Add target ------------------------------------------------------------------
def _process_target(df):
    df['is_pitting'] = df['PitStatusShift'] == 'InLap'
    df['is_pitting'] = df['is_pitting'].astype('bool')
    df = df.loc[df['PitStatusShift'] != 'OutLap']
    df = df.loc[df['PitStatus'] != 'OutLap']
    return df

def clean_data(df, target, drop=True):   
    """
    Clean the dataset for the target variable.
    """
    df = df.copy()
    df = _process_rainfall(df)
    df = _incomplete_races(df)
    df = _remove_unusual_races(df)
    if target == 'pit':
        df = _process_pitstops(df)
    elif target == 'tire':
        df = _process_pitstops(df)
        df = _process_tires(df)
        if drop:
            df = df.loc[df['PitStatusShift'] == 'InLap'].reset_index(drop=True)
    df = _process_track_name(df)
    df = _process_missing_values(df)
    df = _process_target(df)
    df = _process_trackStatus(df)
    return df