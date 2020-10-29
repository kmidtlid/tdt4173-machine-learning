from copy import deepcopy

import numpy as np
import pandas as pd
import tensorflow as tf


def fetch_raw_data() -> pd.DataFrame:
    data_2002_1 = pd.read_csv('../data/raw/data_2002_1.csv')
    data_2002_2 = pd.read_csv('../data/raw/data_2002_2.csv')
    data_2010_1 = pd.read_csv('../data/raw/data_2010_1.csv')
    data_2010_2 = pd.read_csv('../data/raw/data_2010_2.csv')

    # Merge attributes
    merged_1 = data_2002_1.merge(data_2002_2,
                                 indicator=True,
                                 how='inner',
                                 on=['Tid(norsk normaltid)'],
                                 suffixes=('', '_y'))

    merged_1.drop('_merge', 1, inplace=True)

    merged_1 = merged_1[[
        c for c in merged_1.columns if not c.endswith('_y')]]

    merged_2 = data_2010_1.merge(data_2010_2,
                                 indicator=True,
                                 how='inner',
                                 on=['Tid(norsk normaltid)'],
                                 suffixes=('', '_y'))

    merged_2.drop('_merge', 1, inplace=True)

    merged_2 = merged_2[[
        c for c in merged_2.columns if not c.endswith('_y')]]

    # Append datasets
    df = merged_1.append(merged_2)

    return df


def process_data(df: pd.DataFrame) -> pd.DataFrame:

    df.rename(columns={'Tid(norsk normaltid)': 'date', 'Navn': 'name', 'Stasjon': 'station', 'Midlere lufttrykk i stasjonsnivaa (dogn)': 'air_pressure', 'Vanndamptrykk (dogn)': 'water_vapor_pressure', 'Midlere relativ luftfuktighet (dogn)':
                       'relative_air_humidity', 'Spesifikk luftfuktighet': 'specific_air_humidity', 'Gjennomsnittlig skydekke (dogn)': 'average_cloud_cover', 'Middeltemperatur (dogn)': 'temperature', 'Kraftigste middelvind (dogn)': 'wind_speed', 'Nedbor (dogn)': 'downfall', 'Overskya vaer (dogn)': 'cloudy_weather'}, inplace=True)

    df.drop('name', 1, inplace=True)
    df.drop('station', 1, inplace=True)

    # Convert date from str to datetime
    df['date'] = pd.to_datetime(
        df['date'], format='%d.%m.%Y')

    df.sort_values('date', inplace=True)

    df.set_index('date', inplace=True)

    # Convert data types to float64
    columns = list(df)
    for x in range(len(columns)):
        df[columns[x]] = pd.to_numeric(df[columns[x]], errors='coerce')

    return df


def clean_string(input):
    string = deepcopy(input)
    string = string.lower()
    string = string.replace(" ", "_")
    return string


def preprocess_data(df: pd.DataFrame, N: int):
    dataset = pd.DataFrame()
    for i in range(N, len(df)):
        print(i)
        dataset.append({'x': df.iloc[i - N:i - 1], 'y': df.iloc[i]})
    return dataset


def normalize(data, train_split):
    data_mean = data[:train_split].mean(axis=0)
    data_std = data[:train_split].std(axis=0)
    return (data - data_mean) / data_std


def load_data(df, selected, config, normalize_values=True):

    selected = [clean_string(i) for i in selected]
    train_split = int(config.train_split * int(df.shape[0]))
    features = df[selected]
    if normalize_values:
        features = normalize(features.values, train_split)

    train_data = features.iloc[0: train_split - 1]
    val_data = features.iloc[train_split:]

    x_train = train_data.loc[:, selected].values
    y_train = features[['downfall']][1:train_split]  # 7 is the index of downfall

    x_val = val_data.loc[:, selected].values
    y_val = features[['downfall']][train_split:]

    dataset_train = tf.keras.preprocessing.timeseries_dataset_from_array(
        x_train,
        y_train,
        sequence_length=config.sequence_length,
        batch_size=config.batch_size,
    )
    dataset_val = tf.keras.preprocessing.timeseries_dataset_from_array(
        x_val,
        y_val,
        sequence_length=config.sequence_length,
        batch_size=config.batch_size,
    )

    return dataset_train, dataset_val
