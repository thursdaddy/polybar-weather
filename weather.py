#!/usr/local/bin/python3.6

import argparse
from configparser import ConfigParser
import logging
import json
import requests
import os

conf_path = os.environ.get("HOME") + "/.config/polybar/scripts/"
conf_file = conf_path + "py_scripts.conf"
cache_file = conf_path + "py_weather.cache"

def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="enable verbose logging", action="store_true")
    args = parser.parse_args()
    return args

def conf_creator():
    os.makedirs(conf_path)
    if not os.path.exists(conf_file):
        cp.add_section('weather')
        cp.set('weather', 'use_geoloc', '1')
        cp.set('weather', 'zipcode', '10001')
        cp.set('weather', 'cache_ageout', '900')
        cp.set('weather', 'forecast_type', 'short')
        with open(conf_file, 'w') as configfile:
            cp.write(configfile)
        logging.debug("WRITING: " + conf_file)

def cache_new(cache_file, cache_ageout):
    import time
    if os.path.exists(cache_file):
        mod_time = int(os.stat(cache_file).st_mtime)
        current_time = int(time.time())
        cache_age = current_time - mod_time
        logging.debug("Mod Time: " + str(mod_time))
        logging.debug("Current Time: " + str(current_time))
        logging.debug("Cache Age: " + str(cache_age))
        if cache_age > int(cache_ageout):
            logging.debug("Cache is old")
            return(False)
        else:
            logging.debug("Cache is new")
            return(False)

def conf_parser(config_file):
    cp.read(config_file)
    config = cp._sections["weather"]
    return config

def get_geolocation():
    logging.debug("---GEOLOC ENABLED---")    
    location = requests.get('https://ipinfo.io/json')
    json = location.json()
    location = json['loc']
    return get_forecast_url(location)

def get_location(zcode):
    from uszipcode import SearchEngine
    search = SearchEngine()
    zipcode = search.by_zipcode(zcode)
    zipcode = zipcode.to_dict()
    lat = zipcode['lat']
    lng = zipcode['lng']
    t = lat,lng
    location = ("{0[0]},{0[1]}").format(t)
    return get_forecast_url(location)

def get_forecast_url(location):
    logging.debug("WEATHER.GOV ENTRY URL: https://api.weather.gov/points/%s" % location)    
    weather_api = ("https://api.weather.gov/points/%s" % location)
    response = requests.get(weather_api)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.debug(e)
        return False
    get_forecast = requests.get(weather_api)
    json = get_forecast.json()
    forecast_url = json["properties"]["forecast"]
    state = json["properties"]["relativeLocation"]["properties"]["state"]
    city = json["properties"]["relativeLocation"]["properties"]["city"]
    logging.debug("WEATHER.GOV FORECAST URL: " + forecast_url)    
    logging.debug("WEATHER.GOV FORECAST LOCATION: " + city + "," + state)    
    return forecast_url

cp = ConfigParser()
args = arg_parser()
if args.verbose:
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("---VERBOSE LOGGING ENABLED---")
if not os.path.exists(conf_path):
        conf_creator()
config = conf_parser(conf_file)

while True:
    use_geoloc = config['use_geoloc']
    zcode = config['zipcode']
    if cache_new(cache_file, config['cache_ageout']) == False:
        if use_geoloc  == '1':
            forecast_url = get_geolocation()
            print(forecast_url)
            break
        else: 
            forecast_url = get_location(zcode)
            print(forecast_url)
            break
