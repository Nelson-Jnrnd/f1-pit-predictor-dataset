from sklearn.preprocessing import OneHotEncoder
import pandas as pd

## Remove features -------------------------------------------------------------
def _get_features_to_remove():
    return ['LapStartTime', 'DriverNumber', 'Team', 'DriverAhead', 
    'AirTemp', 'Humidity', 'Pressure', 'Rainfall', 'TrackTemp', 'WindDirection', 'WindSpeed',
    'PitStatus', 'PitStatusShift', 'IsAccurate', 'Year', 'RoundNumber', 'NumberOfPitStops'] #'LapNumber', 'TotalLaps']

def _process_remove_features(df):
    df.drop(_get_features_to_remove(), axis=1, inplace=True)
    return df

## Feature encoding ------------------------------------------------------------

def _process_feature_encoding(df: pd.DataFrame) -> tuple[pd.DataFrame, OneHotEncoder]:
    if 'NextCompound' in df.columns:
        categorical_features = ['Compound', 'Track', 'NextCompound']
    else:
        categorical_features = ['Compound', 'Track']
    one_hot_encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
    one_hot_encoder.fit(df[categorical_features])
    one_hot_encoded = one_hot_encoder.transform(df[categorical_features])
    one_hot_encoded = pd.DataFrame(one_hot_encoded, columns=one_hot_encoder.get_feature_names_out(categorical_features))
    df = df.join(one_hot_encoded)
    df.drop(categorical_features, axis=1, inplace=True)
    return df, one_hot_encoder

def _process_feature_encoding_new(df: pd.DataFrame, encoder: OneHotEncoder) -> pd.DataFrame:
    if 'NextCompound' in df.columns:
        categorical_features = ['Compound', 'Track', 'NextCompound']
    else:
        categorical_features = ['Compound', 'Track']
    one_hot_encoded = encoder.transform(df[categorical_features])
    one_hot_encoded = pd.DataFrame(one_hot_encoded, columns=encoder.get_feature_names_out(categorical_features))
    df = df.join(one_hot_encoded)
    df.drop(categorical_features, axis=1, inplace=True)
    return df

def preprocess_training_set(df: pd.DataFrame) -> tuple[pd.DataFrame, OneHotEncoder]:
    df = df.copy()
    df, encoder = _process_feature_encoding(df)
    df = _process_remove_features(df)
    return df, encoder

def preprocess_test_set(df: pd.DataFrame, encoder: OneHotEncoder) -> pd.DataFrame:
    df = df.copy()
    df = _process_feature_encoding_new(df, encoder)
    df = _process_remove_features(df)
    return df