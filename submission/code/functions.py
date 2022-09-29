# Drafted by Vitoria Moreno-Costa
# September 2022

# Imports
import pandas as pd
import numpy as np
import spotipy as sp
import spotipy
import sys
from spotipy.oauth2 import SpotifyClientCredentials
import pprint
import sqlite3
import math
import matplotlib.pyplot as plt
import matplotlib as mpl

### Artists

def build_artist_table(artists: list, spotify: spotipy.client.Spotify):
    """Returns a dataframe of artist information for each artist in the list of artists"""
    artist_tables = []
    for artist in artists:
        artist_tables.append(return_artist_info(artist, spotify))
    return pd.DataFrame(artist_tables)


def return_artist_info(artist: str, spotify: spotipy.client.Spotify):
    """Returns a dictionary of artist information from Spotify API.
    If there are multiple genres or images, it chooses the first option."""
    name = artist.lower()
    results = spotify.search(q="artist:" + name, type="artist")
    items = results["artists"]["items"]
    try:
        artist = items[0]
    except:
        raise Exception("No artist found")
    artist_table = {
        "artist_id": artist["id"],
        "artist_name": artist["name"],
        "external_url": artist["external_urls"]["spotify"],
        "genre": artist["genres"][0],
        "image_url": artist["images"][0]["url"],
        "followers": artist["followers"]["total"],
        "popularity": artist["popularity"],
        "type": artist["type"],
        "artist_uri": artist["uri"],
    }
    return artist_table

### Album

def build_album_table(artists_table: pd.DataFrame, remove_albums_with_keyword: str, spotify: spotipy.client.Spotify):
    """Returns a dataframe of all albums for the artists in the given artists_table,
    which was generate using build_artist_table function."""
    for i in artists_table.index:
        artist_uri = artists_table.loc[i, "artist_uri"]
        artist_id = artists_table.loc[i, "artist_id"]
        artist_album_table = return_artist_album_table(artist_uri, artist_id, spotify)
        if i == 0:
            album_table = artist_album_table
        else:
            album_table = pd.concat([album_table, artist_album_table]).reset_index(
                drop=True
            )
    album_table = return_unique_albums(album_table, remove_albums_with_keyword)
    return album_table


def return_artist_album_table(artist_uri: str, artist_id: str, spotify: spotipy.client.Spotify):
    """Returns a dataframe of album(s) information for a given artist uri from Spotify API"""
    results = spotify.artist_albums(
        artist_id=artist_uri, album_type="album", country="US"
    )
    items = results["items"]
    if len(items) == 0:
        raise Exception("No albums found")
    albums_table = []
    for album in items:
        albums_table.append(return_album_info(album, artist_id))
    return pd.DataFrame(albums_table)


def return_album_info(album: dict, artist_id: str):
    """Returns a dictionary of album information from the provided artist item from the Spotify API file"""
    album_table = {
        "album_id": album["id"],
        "album_name": album["name"],
        "external_url": album["external_urls"]["spotify"],
        "image_url": album["images"][0]["url"],
        "release_date": album["release_date"],
        "total_tracks": album["total_tracks"],
        "type": album["type"],
        "album_uri": album["uri"],
        "artist_id": artist_id,
    }
    return album_table


def return_unique_albums(album_table: pd.DataFrame, keywords_to_remove_album: str):
    """Returns album_table dataframe that includes only the earliest available version of an album and excludes those with a keyword provided,
    for example it excludes tour or live concerts, or deluxe albums if an earlier album is available"""
    album_table.sort_values("release_date", ascending=True, inplace=True)
    album_table["temp_album_name"] = [
        x[0].rstrip().lower() for x in album_table["album_name"].str.split("(")
    ]
    for keyword in keywords_to_remove_album:
        album_indices = album_table.query(
            f"album_name.str.lower().str.find('{keyword.lower()}') != -1"
        ).index
        album_table = album_table.drop(album_indices)
    for i in album_table.index:
        if i not in album_table.index:
            continue
        album = album_table.loc[i, "temp_album_name"]
        artist = album_table.loc[i, "artist_id"]
        duplicate_albums = album_table.query(
            "(album_name.str.lower().str.find(@album) != -1) & (artist_id == @artist)"
        )
        if duplicate_albums.shape[0] > 1:
            first_album_index = duplicate_albums.index[0]
            duplicate_album_indices = duplicate_albums.index[1:]
            album_table.drop(duplicate_album_indices, inplace=True, errors="ignore")
    album_table = (
        album_table.drop_duplicates(subset="temp_album_name")
        .drop(columns=["temp_album_name"])
        .reset_index(drop=True)
    )
    return album_table

### Tracks

def build_track_table(album_table: pd.DataFrame, spotify: spotipy.client.Spotify):
    """Returns a dataframe of all tracks for the albums in the given album_table,
    which was generate using build_album_table."""
    for i in album_table.index:
        album_id = album_table.loc[i, "album_id"]
        album_tracks_table = return_album_tracks(album_id, spotify)
        if i == 0:
            tracks_table = album_tracks_table
        else:
            tracks_table = pd.concat([tracks_table, album_tracks_table])
    tracks_table["explicit"] = tracks_table["explicit"].astype(str)
    return tracks_table.reset_index(drop=True)


def return_album_tracks(album_id: str, spotify: spotipy.client.Spotify):
    """Returns a dataframe of album tracks for a given album_id using Spotify API"""
    results = spotify.album_tracks(album_id=album_id, limit=50, offset=0)
    items = results["items"]
    if len(items) == 0:
        raise Exception("No tracks found")
    tracks_table = []
    for track in items:
        tracks_table.append(return_track_info(track, album_id))
    return pd.DataFrame(tracks_table)


def return_track_info(track: dict, album_id: str):
    """Returns a dictionary of track information from the provided track item from the Spotify API results item"""
    track_table = {
        "track_id": track["id"],
        "song_name": track["name"],
        "external_url": track["external_urls"]["spotify"],
        "duration_ms": track["duration_ms"],
        "explicit": track["explicit"],
        "disc_number": track["disc_number"],
        "type": track["type"],
        "song_uri": track["uri"],
        "album_id": album_id,
    }
    return track_table

### Track Feature

def build_track_feature_table(track_table: pd.DataFrame, spotify: spotipy.client.Spotify):
    """Returns a dataframe of all tracks features for the track in the given track_table,
    which was generated using build_track_table."""
    # Can only call 100 ids at a time
    hundreds_of_tracks = math.ceil(track_table.shape[0] / 100)
    for i in range(0, hundreds_of_tracks):
        track_ids = track_table.loc[(i * 100) : ((i + 1) * 100) - 1, "track_id"]
        new_track_feature_table = return_track_feature_table(track_ids, spotify)
        if i == 0:
            track_feature_table = new_track_feature_table
        else:
            track_feature_table = pd.concat(
                [track_feature_table, new_track_feature_table]
            )
    return track_feature_table.reset_index(drop=True)


def return_track_feature_table(track_ids: list, spotify: spotipy.client.Spotify):
    """Returns a dataframe of track features from a given list of track_ids using Spotify API"""
    results = spotify.audio_features(track_ids)
    if len(results) == 0:
        raise Exception("No tracks found")
    tracks_table = []
    for track_id, track in zip(track_ids, results):
        tracks_table.append(return_track_feature_info(track, track_id))
    return pd.DataFrame(tracks_table)


def return_track_feature_info(track: dict, track_id: str):
    """Returns a dictionary of track feature information for a given track_id from results of a Spotipy API results item"""
    if track is None:
        keys = [
            "track_id",
            "danceability",
            "energy",
            "instrumentalness",
            "liveness",
            "loudness",
            "speechiness",
            "tempo",
            "type",
            "valence",
            "song_uri",
        ]
        track_feature_dict = dict(zip(keys, [np.nan] * 11))
        track_feature_dict["song_uri"] = track_id
    track_feature_dict = {
        "track_id": track["id"],
        "danceability": track["danceability"],
        "energy": track["energy"],
        "instrumentalness": track["instrumentalness"],
        "liveness": track["liveness"],
        "loudness": track["loudness"],
        "speechiness": track["speechiness"],
        "tempo": track["tempo"],
        "type": track["type"],
        "valence": track["valence"],
        "song_uri": track["uri"],
    }
    return track_feature_dict

# Load Tables or Views to SQLlite database

def store_tables_in_db(table_names: [str], tables: [pd.DataFrame], db: str):
    """Saves the tables as the provided table_names into the given db"""
    conn = sqlite3.connect(f"../{db}.db")
    c = conn.cursor()
    for table_name, table in zip(table_names, tables):
        insert_table(table_name, table, c, conn)

def insert_table(
    table_name: str, table: pd.DataFrame, c: sqlite3.Cursor, conn: sqlite3.Connection
):
    """Inserts table referred by table_Name into the databased in the sqlite3 connection"""
    col_dtypes = translate_columns_dtypes(table)
    c.execute(f"""CREATE TABLE IF NOT EXISTS {table_name} ({col_dtypes})""")
    table.to_sql(table_name, conn, if_exists="replace", index=False)
    print(f'{table_name} inserted into db')

def translate_columns_dtypes(table):
    """Returns a str version of a list of column names and their sqlite3 data types 
    based on the pandas datatype of each column in the table"""
    col_dtypes = []
    for col, col_dtype in table.dtypes.items():
        if col_dtype == "object" or col_dtype == "bool":
            col_dtypes.append(f"{col} TEXT")
        elif col_dtype == "int64":
            col_dtypes.append(f"{col} INT")
        elif col_dtype == "float64":
            col_dtypes.append(f"{col} REAL")
    return ", ".join(col_dtypes)

def add_view(query: str, view_name: str, db: str):
    """Adds a view based on the provided query to the db"""
    conn = sqlite3.connect(f"../{db}.db")
    c = conn.cursor()
    c.execute(f"DROP VIEW IF EXISTS {view_name}")
    c.execute(f"""CREATE VIEW {view_name} AS {query}""")
    print(f'{view_name} added to db')
    
def retrieve_query_pd(query: str, columns: list, db: str):
    """Returns a dataframe that contains the data from the query to the db"""
    conn = sqlite3.connect(f"../{db}.db")
    c = conn.cursor()
    data = c.execute(query)
    data = data.fetchall()
    return pd.DataFrame(data, columns=columns)
    
# Visualizations

def plot_spotify_bar(df: str, y: list, width: list, title: str, xlabel: str, filename_to_save: str):
    """Creates and saves a bar graph of the provided information"""
    fig, ax = plt.subplots(figsize = (10,9))
        
    rescale = lambda y: (y - np.min(y)) / (np.max(y) - np.min(y))
    color=plt.get_cmap("viridis")(rescale(width))
    
    plt.barh(y = y, width = width, color = color)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.grid(axis = 'x')
    plt.savefig(f'../visualizations/{filename_to_save}.png', bbox_inches='tight')
    print(f'{filename_to_save} saved in visualizations folder')

def plot_spotify_time(df, time_col, y_col, title, ylabel, filename_to_save):
    """Creates and saves a time-series plot of the provided information"""
    fig, ax = plt.subplots(figsize = (10,4))
    df[time_col] = pd.to_datetime(df[time_col])
    plt.plot(df[time_col], df[y_col], marker='.', markersize=10, )
    plt.title(title)
    plt.ylabel(ylabel)
    plt.savefig(f'../visualizations/{filename_to_save}.png', bbox_inches='tight')
    print(f'{filename_to_save} saved in visualizations folder')