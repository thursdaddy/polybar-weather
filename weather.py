#!/usr/local/bin/python3.6

import argparse
from configparser import ConfigParser
import logging
import json
import requests
import os

cp = ConfigParser()
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

def cache_check(cache_file):
    if os.path.exists(cache_file):
        print("cache exists")
    else:
        print("cache does not exist")

def conf_parser(config):
    cp.read(config)
    config = cp._sections["weather"]
    return config

def get_location():
    location = requests.get('https://ipinfo.io/json')
    json = location.json()
    location = json['loc']
    return get_forecast_url(location)

def get_forecast_url(location):
    logging.debug("WEATHER.GOV ENTRY URL: https://api.weather.gov/points/%s" % location)    
    weather_api = ("https://api.weather.gov/points/%s" % location)
    response = requests.get(weather_api)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.debug(e)
        return print("API DOWN")
    get_forecast = requests.get(weather_api)
    json = get_forecast.json()
    forecast_url = json["properties"]["forecast"]
    logging.debug("WEATHER.GOV FORECAST URL: " + forecast_url)    
    return forecast_url

args = arg_parser()
if args.verbose:
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("---VERBOSE LOGGING ENABLED---")
if not os.path.exists(conf_path):
        conf_creator()
cache_check(cache_file)

# if cache exists..
    # check age
# parse config
# else check geolocation
# get weather URL
