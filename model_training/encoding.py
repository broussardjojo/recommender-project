from typing import Tuple

import pandas as pd
from sklearn.preprocessing import OneHotEncoder, MinMaxScaler

UNUSED_COLUMNS = ["genres", "artist_name", 'track_name']

def fit_scalers_and_encoders(df_in: pd.DataFrame) -> dict:
    scalers_and_encoders = {}
    # Creating onehotencoders for categorical features
    for column in ['key', 'mode', 'time_signature']:
        encoder = OneHotEncoder(sparse=False)
        encoder.fit(df_in[[column]])
        scalers_and_encoders[column] = encoder
    # Creating scalers for continuous features
    for column in ['duration_ms', 'danceability', 'energy', 'loudness', 'speechiness', 'acousticness',
                   'instrumentalness', 'liveness', 'valence', 'tempo', 'artist_popularity']:
        scaler = MinMaxScaler()
        scaler.fit(df_in[[column]])
        scalers_and_encoders[column] = scaler
    return scalers_and_encoders


# Scalers is a dictionary mapping of column names (as strings) to scalers or encoders.
def encode_dataframe_given_scalers(df_in: pd.DataFrame, scalers: dict) -> pd.DataFrame:
    # Encoding categorical variables and discarding their non-encoded versions
    for column in ['key', 'mode', 'time_signature']:
        df_in[scalers[column].get_feature_names_out()] = scalers[column].transform(df_in[[column]])
        df_in = df_in.drop(columns=column)

    # Normalizing continuous features
    for column in ['duration_ms', 'danceability', 'energy', 'loudness', 'speechiness', 'acousticness',
                   'instrumentalness', 'liveness', 'valence', 'tempo', 'artist_popularity']:
        df_in[[column]] = scalers[column].transform(df_in[[column]])
    return df_in

def encode_training_data(df_in: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    training_scalers_and_encoders = fit_scalers_and_encoders(df_in)
    cleaned_training_dataset = encode_dataframe_given_scalers(df_in, training_scalers_and_encoders)
    cleaned_training_dataset = cleaned_training_dataset.set_index("track_id")
    return cleaned_training_dataset, training_scalers_and_encoders
