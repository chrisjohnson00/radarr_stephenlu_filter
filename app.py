from flask import Flask, jsonify
import json
import requests
import redis
from pushover import Client
import consul
import os

application = Flask(__name__)
c = consul.Consul()
consul_path = "radarr_stephenlu_filter/"
keys = c.kv.get(consul_path, keys=True)
config_keys = keys[1]
for key in config_keys:
    if key != consul_path:
        config_key = key.replace(consul_path, '')
        if os.environ.get(config_key):
            application.config[config_key] = os.environ.get(config_key)
        else:
            index, data = c.kv.get(key)
            application.config[config_key] = data['Value'].decode("utf-8")
required_configs = ['OMDB_API_KEY', 'TMDB_API_KEY', 'PUSHOVER_APP_ID', 'PUSHOVER_API_TOKEN', 'REDIS_HOST', 'REDIS_PORT']


@application.route('/')
def hello():
    return "Welcome to the Radarr StepenLu Filter"


@application.route('/health')
def health_check():
    # can i connect to redis
    r = get_redis_connection()
    r.client_list()  # throws an execption if not connected
    for config in required_configs:
        value = application.config.get(config)
        if value is None:
            raise Exception("{} missing from config".format(config))
    return "Success"


@application.route('/config')
def config():
    response_text = ""
    for config in required_configs:
        value = application.config.get(config)
        if any(secret in config for secret in ['KEY', 'TOKEN', 'PASSWORD']):
            response_text += "{}: [REDACTED]<br/>".format(config)
        else:
            response_text += "{}: {}<br/>".format(config, value)
    return response_text


@application.route('/filter')
def filter_stephenlu():
    r = requests.get("https://s3.amazonaws.com/popular-movies/movies.json")
    response_json = json.loads(r.text)
    filtered_results = []
    for movie in response_json:
        result = tmdb_api_call(movie['imdb_id'])
        if 27 in result['genre_ids']:
            print("Skipping '{}' due to Genre".format(result['title']), flush=True)
        elif float(result['vote_average']) < 6:
            print("Skipping '{}' due to rating {}".format(result['title'], result['vote_average']), flush=True)
        else:
            print("Adding '{}'".format(result['title']), flush=True)
            filtered_results.append(transform_tmdb_to_radarr_list(result, movie['imdb_id'], movie['poster_url']))
    return jsonify(filtered_results)


def omdb_api_call(imdb_id):
    api_key = application.config.get('OMDB_API_KEY')
    url = "http://www.omdbapi.com/?i={}&apikey={}".format(imdb_id, api_key)
    r = requests.get(url)
    response_json = json.loads(r.text)
    return response_json


def transform_omdb_to_radarr_list(omdb):
    return {'title': omdb['Title'], 'imdb_id': omdb['imdbID'], 'poster_url': omdb['Poster']}


def transform_tmdb_to_radarr_list(tmdb, imdb_id, poster_url):
    return {'title': tmdb['title'], 'imdb_id': imdb_id, 'poster_url': poster_url}


def tmdb_api_call(imdb_id):
    api_key = application.config.get('TMDB_API_KEY')
    url = "https://api.themoviedb.org/3/find/{}?api_key={}&language=en-US&external_source=imdb_id".format(imdb_id,
                                                                                                          api_key)
    cached = get_from_cache(url)
    if cached:
        print("Cache hit for {}".format(imdb_id), flush=True)
        return json.loads(cached)
    print("Cache miss for {}".format(imdb_id), flush=True)
    r = requests.get(url)
    response_json = json.loads(r.text)
    save_to_cache(url, response_json['movie_results'][0], 28800)
    process_notification(imdb_id, response_json)
    return response_json['movie_results'][0]


def get_from_cache(key):
    r = get_redis_connection()
    return r.get(key)


def get_redis_connection():
    redis_host = application.config.get('REDIS_HOST')
    redis_port = application.config.get('REDIS_PORT')
    r = redis.Redis(host=redis_host, port=redis_port, db=0)
    return r


def save_to_cache(key, data, ttl):
    r = get_redis_connection()
    if ttl > 0:
        return r.set(key, json.dumps(data), ex=ttl)
    else:
        return r.set(key, json.dumps(data))


def process_notification(imdb_id, response_json):
    notification_sent = get_from_cache(imdb_id)
    if notification_sent:
        print("notification sent already for this movie", flush=True)
    else:
        send_pushover_notification(response_json['movie_results'][0])
        save_to_cache(imdb_id, imdb_id, -1)


def send_pushover_notification(movie_results):
    pushover_app_id = application.config.get('PUSHOVER_APP_ID')
    pushover_api_token = application.config.get('PUSHOVER_API_TOKEN')
    client = Client(pushover_app_id, api_token=pushover_api_token)
    client.send_message("{} added to Radarr watch list".format(movie_results['title']), title="New Watched Movie")


if __name__ == "__main__":
    application.run(host="0.0.0.0", port=80)
