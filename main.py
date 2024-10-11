import os

from dotenv import load_dotenv
from flask import Flask, session, url_for, redirect, request, render_template

from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_url = 'http://127.0.0.1:5000/callback'
scope = 'playlist-modify-public playlist-modify-private user-library-read playlist-read-private user-read-private user-read-email user-top-read'

cache_handler = FlaskSessionCacheHandler(session)
sp_oauth = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_url,
        scope=scope,
        cache_handler=cache_handler,
        show_dialog=True
)

sp = Spotify(auth_manager=sp_oauth, requests_timeout=15)

@app.route('/')
def home():
    return render_template('index.html');  

@app.route('/login')
def login():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    return redirect(url_for('home')) 

@app.route('/callback')
def callback():
    token_info = sp_oauth.get_access_token(request.args['code'])
    session['token_info'] = token_info
    session['logged_in'] = True
    return redirect(url_for('home'))

# @app.route('/get_playlist')
# def get_playlist():
#     if not sp_oauth.validate_token(cache_handler.get_cached_token()):
#         auth_url = sp_oauth.get_authorize_url()
#         return redirect(auth_url)
    
#     playlist = sp.current_user_playlists()
#     playlist_info = [(pl['name'], pl['external_urls']['spotify']) for pl in playlist['items']]
#     playlist_html = '<br>'.join([f'{name}: {url}' for name, url in playlist_info])

#     return playlist_html

@app.route('/get_toptracks')
def get_toptracks():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    
    top_tracks = sp.current_user_top_tracks(limit=50)
    top_info = [(track['name'], track['artists'][0]['name'], track['album']['images'][0]['url'], track['popularity']) for track in top_tracks['items']]
    
    return render_template('top_tracks.html', top_info = top_info)

@app.route('/go_to_reco_play')
def go_to_reco_play():
    return render_template('reco.html')

@app.route('/make_reco_playlist', methods = ['POST'])
def make_reco_playlist():
    # get energy, dancibility and genre from html
    play_name =request.form.get('play_name')
    privacy = request.form.get('privacy') == 'True'
    play_num = request.form.get('play_num')


    # get top tracks to recommend 
    top_tracks = sp.current_user_top_tracks(limit=50)
    seed_tracks = [track['id'] for track in top_tracks['items']]

    # get recommended
    # Spotify can only take in 5 seed tracks in one request
    print(f"Play name: {play_name} Play NUm: {play_num} privacy: {privacy}")

    recommendations = sp.recommendations(
        seed_tracks=seed_tracks[:5],  # Seed tracks
        limit=play_num
    )

    # # Create new playlist
    user_id = sp.current_user()['id']
    playlist = sp.user_playlist_create(user_id, play_name) #add name and state
    
    # # Add recommended to playlist
    track_ids = [track['id'] for track in recommendations['tracks']]
    sp.playlist_add_items(playlist['id'], track_ids)

    return "Playlist created"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
