import pandas as pd
import numpy as np
import fastf1 as ff1
from fastf1.core import Session, Telemetry, Laps, Lap
from fastf1.logger import logging
from pathlib import Path
import typer
from loguru import logger
from tqdm import tqdm
from f1_pit_predictor.config import RAW_DATA_DIR
from datetime import datetime


app = typer.Typer()

class NoTelemetryException(Exception):
    pass
class NoLapException(Exception):
    pass


# Set up FastF1 cache on script startup
cache_path: Path = RAW_DATA_DIR / "cache"
cache_path.mkdir(parents=True, exist_ok=True)  # Ensure cache directory exists
ff1.Cache.enable_cache(cache_path)
logger.success("FastF1 cache enabled.")


def extract_number(s):
    """
    Extracts the number of laps from the GapToLeader column. (e.g. '1 L' -> 1)
    """
    if isinstance(s, str) and s.endswith('L'):
        return int(s.split()[0])
    else:
        return 0

def load_api_data(session: Session) -> pd.DataFrame:
    """
    Loads the data from a session with FastF1 API and returns it as a pandas DataFrame with per lap data.
    """
    logger.info("Loading data from the FastF1 API...")
    laps_data, stream_data = ff1.core.api.timing_data(session.api_path)

    # Drop rows with missing time data
    laps_data.dropna(subset=['Time'], inplace=True)
    
    # Merge the two dataframes for each driver based on the time of the sample
    api_data = pd.merge_asof(laps_data.sort_values('Time'), stream_data.sort_values('Time'), on='Time', by='Driver')

    # Discretize the time data for one sample per lap
    merged_laps = pd.merge(session.laps, api_data[['Driver', 'Time', 'NumberOfLaps', 'NumberOfPitStops', 'GapToLeader', 'IntervalToPositionAhead']], left_on=['LapNumber', 'DriverNumber'], right_on=['NumberOfLaps', 'Driver'])

    # Fix the data types
    merged_laps['LapsToLeader'] = merged_laps['GapToLeader'].map(extract_number)
    merged_laps.replace(regex=r'^LAP', value=0, inplace=True)
    merged_laps["GapToLeader"] = pd.to_numeric(merged_laps["GapToLeader"], errors="coerce")
    merged_laps["IntervalToPositionAhead"] = pd.to_numeric(merged_laps["IntervalToPositionAhead"], errors="coerce")
    merged_laps = merged_laps.infer_objects(copy=False)
    merged_laps.replace(regex=r'^\+', value='', inplace=True)
    merged_laps.replace(regex=r'^(\d+)\sL$', value=np.nan, inplace=True)

    merged_laps.rename(columns={'Time_x': 'Time', 'Driver_x':'Driver'}, inplace=True)
    merged_laps = merged_laps.astype({'GapToLeader': 'float64', 'IntervalToPositionAhead': 'float64'})
    merged_laps.session = session.laps.session
    return merged_laps[['Time', 'Driver', 'DriverNumber', 'LapTime', 'LapNumber', 'PitOutTime',
       'PitInTime','Compound', 'TyreLife', 'Stint', 'LapStartTime', 'Team',
        'TrackStatus', 'IsAccurate', 'LapStartDate', 'NumberOfPitStops', 'Position', 'GapToLeader',
       'IntervalToPositionAhead', 'LapsToLeader']]

def get_empty_dataframe() -> pd.DataFrame:
    """
    Returns an empty DataFrame with the columns that will be used to store the data.
    """
    return pd.DataFrame(
            columns=[
                'LapStartTime',
                'LapNumber',
                'LapTime',
                'DriverNumber',
                'Team',
                'Compound',
                'TyreLife',
                'TrackStatus',
                'Stint',
                'DistanceToDriverAhead',
                'DriverAhead',
                'PitStatus',
                'IsAccurate',
                'NumberOfPitStops',
                'Position',
                'GapToLeader',
                'IntervalToPositionAhead',
                'LapsToLeader',
                ])

def get_telemetry_at_start_of_lap(lap: Lap, telemetry: Telemetry) -> pd.DataFrame:
    """
    Find the telemetry data (Driver Ahead, Distance to Driver Ahead) for the start of a lap and merge it with the lap data.
    """
    # Find the telemetry data for the start of the lap by creating a 1 second window around the lap start time.
    mask = (telemetry['Date'] > lap['LapStartDate']) & (
        telemetry['Date'] <= lap['LapStartDate'] + pd.Timedelta(seconds=1))
    rows = telemetry.loc[mask]
    # If there is no telemetry data for the lap, raise an exception.
    if rows.empty:
        raise NoTelemetryException("No telemetry data found for lap " + str(
            lap['LapNumber']) + " of " + str(lap['Driver']) + " at " + str(lap['LapStartDate']))
    # There can be multiple telemetry samples in the 1 second window, so take the first one.
    row = rows.iloc[0]
    # Get the telemetry data we are interested in.
    telemetryInfo = row[['DriverAhead', 'DistanceToDriverAhead']]
    lapInfo = lap[['LapStartTime', 'LapNumber', 'LapTime',
                   'DriverNumber', 'Team', 'Compound', 
                   'TyreLife', 'Stint', 'TrackStatus',
                   'IsAccurate', 'NumberOfPitStops', 'Position',
                   'GapToLeader', 'IntervalToPositionAhead', 'LapsToLeader',]]  # Get the lap data we are interested in.
    # Convert the pit out time to seconds.
    lap['PitOutTime'] = lap['PitOutTime'].total_seconds() if lap['PitOutTime'] is not None else 0
    # Convert the pit in time to seconds.
    lap['PitInTime'] = lap['PitInTime'].total_seconds() if lap['PitInTime'] is not None else 0
    # Get the pit status.
    lapInfo['PitStatus'] = 'OutLap' if lap['PitOutTime'] > 0 else 'InLap' if lap['PitInTime'] > 0 else 'NoPit'
    telemetryInfo.rename("Telemetry", inplace=True)
    lapInfo.rename("Lap", inplace=True)
    # Merge the telemetry and lap data.
    merge = pd.concat([telemetryInfo, lapInfo])
    return merge

def get_laps_of_driver(driver_number: str, laps: Laps) -> pd.DataFrame:
    """
    Get the laps of a driver from the FastF1 API.
    """
    driver_laps = laps.loc[laps['DriverNumber'] == driver_number]
    if len(driver_laps['DriverNumber']) == 0:
        raise NoLapException("No laps for driver " + driver_number)
    driver_laps_telemetry = driver_laps.get_car_data()
    if len(driver_laps_telemetry) == 0:
        raise NoLapException("No telemetry for driver " + driver_number)
    try:
        driver_laps_telemetry = driver_laps_telemetry.add_driver_ahead()
        transformed_laps = []
        for _, row in driver_laps.iterrows():
            try:
                transformed_laps.append(get_telemetry_at_start_of_lap(row, driver_laps_telemetry))
            except NoTelemetryException as e:
                logger.error(e)
    except ValueError as e:
        logger.error(e)
        return get_empty_dataframe()
    return pd.DataFrame(transformed_laps)

def add_weather_to_laps(laps: Laps, weather) -> pd.DataFrame:
    """
     Add weather data that would have been available at the start of each lap.
    - AirTemp (float): Air temperature [°C]
    - Humidity (float): Relative humidity [%]
    - Pressure (float): Air pressure [mbar]
    - Rainfall (bool): Shows if there is rainfall
    - TrackTemp (float): Track temperature [°C]
    - WindDirection (int): Wind direction [°] (0°-359°)
    - WindSpeed (float): Wind speed [m/s]
    """
    if laps.empty:
        raise NoLapException("Laps dataframe is empty")
    # Effectuer une jointure basée sur une plage de temps
    lapsWithWeather = pd.merge_asof(laps.sort_values('LapStartTime'), 
                                    weather.sort_values('Time'), 
                                    left_on='LapStartTime', 
                                    right_on='Time', 
                                    by=None, 
                                    direction='backward')

    return lapsWithWeather

@app.command()
def get_season_data(year: int, save_all_races: bool=True, verbose: bool=False) -> pd.DataFrame:
    """
    Get the data for a whole season. The data is saved in a folder named after the year.
    """
    if not verbose:
        ff1.set_log_level(logging.CRITICAL)
    schedule = ff1.get_event_schedule(year, include_testing=False)

    path: Path = RAW_DATA_DIR / str(year)
    # Create a directory for the year if it doesn't exist
    if not path.exists():
        logger.info(f"Creating directory for year {year}")
        path.mkdir()

    df_season = get_empty_dataframe()
    for _, event in tqdm(schedule.iterrows(), total=len(schedule), desc=f"Processing {year} season"):
        if year == 2018 and event['RoundNumber'] < 3: # The 2 first races of 2018 do not have telemetry data
            continue
        if datetime.now() < event['Session5DateUtc']:
            logger.info("Skipping future event")
            break
        race = event.get_race()
        race.load()
        df_event = get_empty_dataframe()
        api_laps = load_api_data(race)

        for driver in tqdm(race.drivers, desc=f"Processing {event['EventName']} drivers"):
            try:
                df_driver_laps = get_laps_of_driver(driver, api_laps)
                if not df_driver_laps.empty:
                    df_event = pd.concat([df_event, df_driver_laps], ignore_index=True)
            except NoLapException as e:
                logger.error(e)
    
        df_event['RoundNumber'] = event['RoundNumber']
        df_event['Track'] = event['Location']
        df_event['TotalLaps'] = api_laps['LapNumber'].max()
        df_event['Year'] = year
        try:
            df_event = add_weather_to_laps(df_event, race.weather_data)
            df_event = df_event.drop(columns=['Time'])
            # Convert the laptime column to total seconds if it's not a NAN value
            df_event['LapTime'] = df_event['LapTime'].apply(lambda x: x.total_seconds() if not pd.isna(x) else x)
            df_event['LapStartTime'] = df_event['LapStartTime'].apply(lambda x: x.total_seconds() if not pd.isna(x) else x)
        except NoLapException as e:
            logger.error(e)
        if save_all_races:
            # Save it to a csv file
            df_event.to_csv(path / f"{event.EventName.replace(' ', '_').lower()}.csv", index=False)
        if df_season.empty:
            df_season = df_event
        else:
            df_season = pd.concat([df_season, df_event], axis=0)
    # Save the data for the whole season
    df_season.to_csv(path / f"{year}.csv", index=False)
    return df_season

if __name__ == "__main__":
    app()
