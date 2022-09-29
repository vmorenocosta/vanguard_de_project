# Drafted by Vitoria Moreno-Costa
# September 2022

from functions import *

# Load environment variables from .env files which is named in the .gitignore file to prevent accidental upload to Github
import os
from dotenv import load_dotenv
load_dotenv()
spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials())

# Enter parameters to build tables
db = 'spotify'

artists = [
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
    "Eagles",
]

keywords_to_remove_album = [
    "live",
    "tour",
    "mtv",
    "one more car, one more rider",
    "...but seriously",
    "bohemian rhapsody (the original soundtrack)",
    "queen rock montreal",
    "queen on air",
    "a night at the odeon",
]

# Build & Transform Tables
artist_table = build_artist_table(artists, spotify)
album_table = build_album_table(artist_table, keywords_to_remove_album, spotify)
track_table = build_track_table(album_table, spotify)
track_feature_table = build_track_feature_table(track_table, spotify)

# Load tables to SQL
table_names = ["artist", "album", "track", "track_feature"]
tables = [artist_table, album_table, track_table, track_feature_table]
store_tables_in_db(table_names, tables, db)

# Add views
## 1
query_top_10_songs_by_artist_by_duration = f"""
    WITH TOPTEN AS (SELECT artist.artist_name,
                          track.song_name,
                          track.duration_ms,
                          ROW_NUMBER() over (
                                PARTITION BY artist.artist_name
                                order by track.duration_ms DESC
                            ) AS RowNo 
                    FROM artist JOIN album ON artist.artist_id = album.artist_id
                        JOIN track ON album.album_id = track.album_id
                    )
    SELECT artist_name, song_name, duration_ms
    FROM TOPTEN WHERE RowNo <= 10;
    """
add_view(query_top_10_songs_by_artist_by_duration, 'top_10_songs_by_artist_by_duration', db)

## 2
query_top_20_artists_by_followers = """SELECT artist_name, followers
                                        FROM artist
                                        ORDER BY 2 DESC"""
add_view(query_top_20_artists_by_followers, 'top_20_artists_by_followers', db)

## 3
query_top_10_songs_by_artist_by_tempo = """
    WITH TOPTEN AS (SELECT artist.artist_name,
                          track.song_name,
                          track_feature.tempo,
                          ROW_NUMBER() over (
                                PARTITION BY artist.artist_name
                                order by track_feature.tempo DESC
                            ) AS RowNo 
                    FROM artist JOIN album ON artist.artist_id = album.artist_id
                        JOIN track ON album.album_id = track.album_id
                        JOIN track_feature ON track.track_id = track_feature.track_id
                    )
    SELECT artist_name, song_name, tempo
    FROM TOPTEN WHERE RowNo <= 10;
    """
add_view(query_top_10_songs_by_artist_by_tempo, 'top_10_songs_by_artist_by_tempo', db)

## 4
query_top_1_album_by_artist_by_mean_song_energy = """
    WITH mean_energy as (SELECT artist.artist_name,
                          album.album_name,
                          AVG(track_feature.energy) as mean_energy
                    FROM artist JOIN album ON artist.artist_id = album.artist_id
                        JOIN track ON album.album_id = track.album_id
                        JOIN track_feature ON track.track_id = track_feature.track_id
                    GROUP BY 1, 2
                    ORDER BY 3 DESC),
    mean_energy_row_no AS (SELECT *, ROW_NUMBER() over (PARTITION BY artist_name
                                                        order by mean_energy DESC
                                                        ) AS RowNo
                            FROM mean_energy)
    SELECT artist_name, album_name, mean_energy
    FROM mean_energy_row_no WHERE RowNo <= 1;
    """
add_view(query_top_1_album_by_artist_by_mean_song_energy, 'top_1_album_by_artist_by_mean_song_energy', db)

## 5
query_albums_without_explicit_songs = """
    WITH explicit_ind AS (SELECT track_id,
                                album_id,
                                (CASE WHEN upper(track.explicit) = "FALSE" THEN 0 ELSE 1 END) as explicit
                            FROM track)

    SELECT artist.artist_name, 
            album.album_name
    FROM artist JOIN album ON artist.artist_id = album.artist_id
        JOIN explicit_ind ON album.album_id = explicit_ind.album_id
        JOIN track_feature ON explicit_ind.track_id = track_feature.track_id
    GROUP BY 1, 2
    HAVING SUM(explicit_ind.explicit) = 0
    """
add_view(query_albums_without_explicit_songs, 'albums_without_explicit_songs', db)