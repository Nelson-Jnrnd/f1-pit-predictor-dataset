import numpy as np
from f1_pit_predictor.preprocessing.cleaning import clean_data
from f1_pit_predictor.preprocessing.features import preprocess_training_set, preprocess_test_set
## Train test split ------------------------------------------------------------

def _get_races_grouped(df):
    return df.groupby(['Year', 'RoundNumber', 'DriverNumber'])

def get_train_test_split(df, test_size, return_groups=False, random_state=None):
    if random_state is not None:
        np.random.seed(random_state)
    groups = _get_races_grouped(df).groups
    groups_keys = list(groups.keys())
    np.random.shuffle(groups_keys)
    test_groups = groups_keys[:int(len(groups_keys) * test_size)]
    train_groups = groups_keys[int(len(groups_keys) * test_size):]
    test = df[df.apply(lambda x: (x['Year'], x['RoundNumber'], x['DriverNumber']) in test_groups, axis=1)].reset_index(drop=True)
    train = df[df.apply(lambda x: (x['Year'], x['RoundNumber'], x['DriverNumber']) in train_groups, axis=1)].reset_index(drop=True)
    if return_groups:
        return train, test, train.groupby(['Year', 'RoundNumber', 'DriverNumber']).groups, test.groupby(['Year', 'RoundNumber', 'DriverNumber']).groups
    return train, test

def get_preprocessed_train_test_split(df, test_size, return_groups=False, random_state=None, target='pit', drop=True):
    df = clean_data(df, target, drop=drop)
    train, test, train_groups, test_groups = get_train_test_split(df, test_size, return_groups=True, random_state=random_state)
    train, encoder = preprocess_training_set(train)
    test = preprocess_test_set(test, encoder)
    train.dropna(inplace=True)
    test.dropna(inplace=True)
    if return_groups:
        return train, test, encoder, train_groups, test_groups
    return train, test, encoder

def get_x_y_pit(df):
    return df.drop(['is_pitting'], axis=1), df['is_pitting']

def get_x_y_tires(df):
    return df.drop(['is_pitting', 'NextCompound_SOFT', 'NextCompound_MEDIUM', 'NextCompound_HARD', 'NextCompound_nan'], axis=1), df[['NextCompound_SOFT', 'NextCompound_MEDIUM', 'NextCompound_HARD']]
