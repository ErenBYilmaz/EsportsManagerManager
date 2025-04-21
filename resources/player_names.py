import os
import urllib.request

import pandas


def load_player_names():
    if not os.path.isfile('resources/names.csv'):
        url = 'https://raw.githubusercontent.com/hadley/data-baby-names/master/baby-names.csv'
        urllib.request.urlretrieve(url, 'resources/names.csv')
    df = pandas.read_csv('resources/names.csv')
    return df['name'].unique().tolist()


PLAYER_NAME_EXAMPLES = load_player_names()
