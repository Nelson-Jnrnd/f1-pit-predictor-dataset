# f1-pit-predictor-dataset
This repository contains a Jupyter notebook for collecting telemetry data from F1 races using the FastF1 API and storing them in CSV files. 

The notebook collects data for a whole F1 season (from 2018 to 2022) and can be easily modified to include additional seasons. 

The data were intented to be used to train a machine learning model for predicting when a driver will make a pit stop during a race.

## Data
The data is organized into separate CSV files for each race, as well as a single CSV file containing all the data for the season.

This dataset contains lap-by-lap data for each drivers during races and contains the following columns:

* LapStartTime: The start time of the lap in HH:MM:SS format.
* LapNumber: The number of the lap.
* LapTime: The duration of the lap in HH:MM:SS format .
* Compound: The type of tire compound used for the lap.
* TyreLife: The number of laps made on this set of tire.
* TrackStatus: Single digit status codes (‘1’: Track clear, ‘2’: Yellow flag, ‘4’: Safety Car, ‘5’: Red Flag, ‘6’: Virtual Safety Car deployed, ‘7’: Virtual Safety Car ending).
* Stint: The stint number of the race for the driver (2 after the first stop, 3 after the second etc).
* DistanceToDriverAhead: The distance to the driver ahead in meters.
* DriverAhead: The name tag (HAM, ALO, etc) of the driver ahead.
* Track: The name of the track where the race took place.
* Time: The time of the lap in HH:MM:SS format.
* AirTemp: The temperature of the air in degrees Celsius.
* Humidity: The humidity in percentage.
* Pressure: The pressure in hPa.
* Rainfall: Whether it rained during the lap (True/False).
* TrackTemp: The temperature of the track in degrees Celsius.
* WindDirection: The direction of the wind.
* WindSpeed: The speed of the wind in meters per second.
