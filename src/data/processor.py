from copy import deepcopy

import numpy as np
import pandas as pd
import tensorflow as tf

import config as config
from utils.csv_utils import read_csv


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
        dataset.append({'x': df.iloc[i - N:i - 1], 'y': df.iloc[i]})
    return dataset

def process_dataset(df, features, sequence_length, batch_size=32, fill_value=0):

    # Uncomment if you want to normalize the data
    # df = (df-df.mean())/df.std()

    # Remove unwanted features
    selected_features = [clean_string(i) for i in features]
    df = df.loc[:, selected_features]

    # Split into datapoints (x) and labels (y)
    x = df.loc[:, :]
    y = df.loc[:, 'downfall']

    # Offset to create timeseries_dataset
    x = x.iloc[:-sequence_length]
    y = y.iloc[sequence_length:]

    timeseries_dataset = tf.keras.preprocessing.timeseries_dataset_from_array(
        x,
        y,
        sequence_length=sequence_length,
        batch_size=batch_size,
    )

    # Test each batch to see if
    for i, batch in enumerate(timeseries_dataset):
        inputs, targets = batch
        for j in range(len(inputs)):
            assert np.array_equal(inputs[j], x[i * batch_size + j:i * batch_size + j + sequence_length])
            assert np.array_equal(targets[j], y[i * batch_size + j])

    return timeseries_dataset


def load_data(features, sequence_length):
    train_dataset = read_csv('../data/train_data.csv')
    train_data = process_dataset(
        train_dataset,
        features=features,
        sequence_length=sequence_length,
        batch_size=config.batch_size
    )

    val_dataset = read_csv('../data/validation_data.csv')
    val_data = process_dataset(
        val_dataset,
        features=features,
        sequence_length=sequence_length,
        batch_size=config.batch_size
    )

    test_dataset = read_csv('../data/test_data.csv')
    test_data = process_dataset(
        test_dataset,
        features=features,
        sequence_length=sequence_length,
        batch_size=config.batch_size
    )

    return train_data, train_dataset, val_data, val_dataset, test_data, test_dataset
