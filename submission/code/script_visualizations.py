# Drafted by Vitoria Moreno-Costa
# September 2022

from functions import *

db = 'spotify'

# Create and save visualizations
## 1
longest_songs_by_artist = retrieve_query_pd("""SELECT artist_name,
                            song_name,
                            MAX(duration_ms) as duration_ms
                      FROM top_10_songs_by_artist_by_duration GROUP BY 1
                      ORDER BY 3;""",
                  ['artist_name','song_name','duration_ms'], db)

plot_spotify_bar(longest_songs_by_artist, 
                 y = [', '.join(longest_songs_by_artist.loc[i,['song_name','artist_name']]) 
                      for i in longest_songs_by_artist[['artist_name','song_name']].index],
                 width = longest_songs_by_artist['duration_ms']/(1000*60), 
                 title = 'Longest Songs by Artist',
                 xlabel = 'Duration [minutes]',
                 filename_to_save = 'top_songs_by_artist_by_duration')

## 2
highest_energy_by_artist = retrieve_query_pd("""SELECT artist_name,
                            album_name,
                            mean_energy
                      FROM top_1_album_by_artist_by_mean_song_energy
                      ORDER BY 3;""",
                  ['artist_name','album_name','mean_energy'], db)

plot_spotify_bar(longest_songs_by_artist, 
                 y = [', '.join(highest_energy_by_artist.loc[i,['album_name','artist_name']]) for i in longest_songs_by_artist[['artist_name','song_name']].index],
                 width = highest_energy_by_artist['mean_energy'], 
                 title = 'Highest Energy Albums by Artist',
                 xlabel = 'Mean Song Energy on Album',
                 filename_to_save = 'top_1_album_by_artist_by_mean_song_energy')

## 3 
lady_gaga_albums_by_mean_song_energy = retrieve_query_pd("""
    WITH mean_energy as (SELECT artist.artist_name,
                          album.album_name,
                          album.release_date,
                          AVG(track_feature.energy) as mean_energy
                    FROM artist JOIN album ON artist.artist_id = album.artist_id
                        JOIN track ON album.album_id = track.album_id
                        JOIN track_feature ON track.track_id = track_feature.track_id
                    GROUP BY 1, 2
                    ORDER BY 3 DESC)
    SELECT artist_name, album_name, release_date, mean_energy
    FROM mean_energy
    WHERE artist_name = "Lady Gaga"
    ORDER BY release_date;
    """,
                  ['artist_name','album_name','release_date','mean_energy'], db)

plot_spotify_time(lady_gaga_albums_by_mean_song_energy, 'release_date','mean_energy','Mean Energy of Lady Gaga Albums by Release Date','Mean Song Energy of Album','lady_gaga_albums_by_mean_song_energy_over_time')

df = lady_gaga_albums_by_mean_song_energy.sort_values('release_date',ascending=False)
plot_spotify_bar(df, df['album_name'], df['mean_energy'], 'Mean Energy of Lady Gaga Albums, sorted by ascending Release Date', 'Mean Song Energy of Album', 'lady_gaga_albums_by_mean_song_energy')
