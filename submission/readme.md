# Submission Readme

Use this file to explain what files are doing what.  Consider that the people grading this project might not be familiar with the way you chose to structure everything.  This should be a high level overview which can quickly get someone else up to speed and able to understand your code / submissions.

## Summary

The python scripts and functions in the code folder ingest, transform, store, and analyse Spotify data for 20 of my favorite artists. The data is stored in the spotify.db SQLite file and contains 4 tables and 5 views. The visualizations folder contains png files for visualizations created in the script, and the visualization.pdf file displays and explains each of these visualizations.

## Source
The project collects 20 artists, 132 albums, and approximately 2000 songs and their features using [Spotipy API](https://spotipy.readthedocs.io/en/master/#). 

Artists:
    "Taylor Swift",
    "Shakira",
    "Phil Collins",
    "Billie Eilish",
    "Camilo",
    "Bad Bunny",
    "Harry Styles",
    "Sublime",
    "Eric Clapton",
    "Lizzo",
    "Adele",
    "Maroon 5",
    "Ed Sheeran",
    "Enrique Iglesias",
    "Coldplay",
    "Lady Gaga",
    "Beyonce",
    "Britney Spears",
    "Queen",
    "Eagles"

---
## Overview of Code
Code Structure:
- **functions.py**
    - Contains all functions used in the two scripts below
- **script_data_ETL.py**
    1. Extract and transform tables using the following functions:
        - artist:
            - build_artist_table - Aggregates information for each artist in pandas dataframe
            - _return_artist_info - API call and JSON extraction
        - album:
            - build_album_table - Aggregates albums in pandas dataframe for each artist 
            - _return_artist_album_table - API call to obtain albums of an artist and aggregates albums in pandas dataframe
            - _return_album_info - JSON extraction
            - _return_unique_albums - Returns album_table dataframe that includes only the earliest available version of an album and excludes those whose name contains a keyword provided
        - track:
            - build_track_table - Aggregates tracks in pandas dataframe for each album
            - _return_album_tracks - API call to obtain tracks of an album and aggregates tracks in pandas dataframe
            - _return_track_info - JSON extraction
        - track_feature:
            - build_track_feature_table: Aggregates track_feature in pandas dataframe for each track
            - _return_track_feature_table - API call to obtain track_feature of a track and aggregates track_features in pandas dataframe
            - _return_track_feature_info - JSON extraction
    2. Load tables into spotify.db using the following functions:
        - store_tables_in_db: iterates through tables to store in db
        - _insert_table: contains query to create and insert table in db
        - _translate_columns_dtypes: returns the table names and data types for inserting table
    3. Add 5 views to spotify.db using the following function:
        - add_view: adds a view based on the provided query to the db
- **script_visualizations.py**
    1. Load data from spotify.py using the following function:
        - retrieve_query_pd
    2. Create and save visualizations using the following functions:
        - plot_spotify_bar - creates and saves a bar graph of the provided information
        - plot_spotify_time - creates and saves a time-series plot of the provided information
---
## How to recreate output
Ensure that dependencies from requirements.txt are installed/compatible.
Run the code below to recreate the output (assuming your working directory is submission).
```
cd code
python script_data_ETL.py
python script_visualizations.py
```
---
    
## Directory Structure
```
submission
|__code
|   |__functions.py
|   |__script_data_ETL.py
|   |__script_visualizations.py
|__notebooks **IGNORE** (internal use of jupyter notebooks to craft code)
|__visualizations
|   |__lady_gaga_albums_by_mean_song_energy_over_time.png
|   |__lady_gaga_albums_by_mean_song_energy.png
|   |__top_1_album_by_artist_by_mean_song_energy.png
|   |__top_songs_by_artist_by_duration.png
|__readme.md
|__requirements.txt
|__spotify.db
|__visualizations.pdf
```