#!/usr/local/bin/python3.6

import argparse
from configparser import ConfigParser
import logging
import json
import requests
import os


def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="enable verbose logging", action="store_true")
    parser.add_argument("-t", "--toggle-forecast-type", help="toggle between short and long forecast", action="store_true")
    parser.add_argument("-n", "--notify-5day-forecast", help="send 5 day forecast to send-notfiy", action="store_true")
    args = parser.parse_args()
    return args

def conf_creator():
    os.makedirs(conf_path)
    if not os.path.exists(conf_file):
        cp.add_section('weather')
        cp.set('weather', 'use_geoloc', 'True')
        cp.set('weather', 'zipcode', '10001')
        cp.set('weather', 'cache_ageout', '900')
        cp.set('weather', 'forecast_type', 'short')
        with open(conf_file, 'w') as configfile:
            cp.write(configfile)
        logging.debug("WRITING: " + conf_file)

# checks if cache is older than cache_ageout value
# if conf file is newer than cache it will get weather
def cache_new(cache_file, cache_ageout):
    import time
    if not os.path.exists(cache_file):
        with open(cache_file, 'a'):
            os.utime(cache_file, None)
    if os.path.exists(cache_file):
        conf_mod_time = int(os.stat(conf_file).st_mtime)
        cache_mod_time = int(os.stat(cache_file).st_mtime)
        current_time = int(time.time())
        cache_age = current_time - cache_mod_time
        conf_age = current_time -  conf_mod_time
        logging.debug("Mod Time: " + str(cache_mod_time))
        logging.debug("Current Time: " + str(current_time))
        logging.debug("Ageout value: " + str(cache_ageout))
        logging.debug("Cache Age: " + str(cache_age))
        logging.debug("Conf Age: " + str(conf_age))
        if (conf_age < cache_age) or str(conf_age) == "0":
            logging.debug("Cache is new OR Conf has been updated!")
            return(False)
        if cache_age > int(cache_ageout):
            logging.debug("Cache is old")
            return(False)
        else:
            logging.debug("Cache is new")
            return(True)

def conf_parser(config_file):
    cp.read(config_file)
    config = cp._sections["weather"]
    return config

def get_geolocation():
    logging.debug("---GEOLOC ENABLED---")    
    location = requests.get('https://ipinfo.io/json')
    json = location.json()
    location = json['loc']
    return forecast_get_url(location)

def get_location(zipcode):
    from uszipcode import SearchEngine
    search = SearchEngine()
    zipcode = search.by_zipcode(zipcode)
    zipcode = zipcode.to_dict()
    latlong = zipcode['lat'],zipcode['lng']
    location = ("{0[0]},{0[1]}").format(latlong)
    return forecast_get_url(location)

def forecast_url_reponse(forecast_url):
    response = requests.get(forecast_url)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.debug(e)
        return(False)
    else:
        return forecast_url

def forecast_get_url(location):
    logging.debug("WEATHER.GOV ENTRY URL: https://api.weather.gov/points/%s" % location)    
    forecast_url = ("https://api.weather.gov/points/%s" % location)
    if forecast_url_reponse(forecast_url):
        get_forecast = requests.get(forecast_url)
        json = get_forecast.json()
        forecast_url = json["properties"]["forecast"]
        logging.debug("WEATHER.GOV FORECAST URL: " + forecast_url)    
        logging.debug("WEATHER.GOV FORECAST LOCATION: " + json["properties"]["relativeLocation"]["properties"]["city"] + ", " + json["properties"]["relativeLocation"]["properties"]["state"])    
        if forecast_url_reponse(forecast_url):
            return forecast_url
        else: 
            return(False)

def forecast_type_toggle(forecast_type):
    if forecast_type == "short":
        cp.set('weather', 'forecast_type', 'long')
    elif forecast_type == "long":
        cp.set('weather', 'forecast_type', 'short')
    with open(conf_file, 'w') as conf:
        cp.write(conf)

def forecast_get_json(forecast_url):
    forecast = requests.get(forecast_url)
    json = forecast.json()
    return json

def forecast_long(forecast_json):
    message = "long_forecast_message"
    forecast_write_cache(message)

def forecast_5day(forecast_json):
    message = "5_forecast_message"
    forecast_send_notify(message)

def forecast_short(forecast_json):
    message = "short_forecast_message"
    forecast_write_cache(message)

def forecast_write_cache(message):
    print(message)

def forecast_send_notify(message):
    import subprocess
    subprocess.Popen(['notify-send', "-t", "100000", message])

cp = ConfigParser()
args = arg_parser()

## config and cache files
conf_path = os.environ.get("HOME") + "/.config/polybar/scripts/"
conf_file = conf_path + "py_scripts.conf"
cache_file = conf_path + "py_weather.cache"

## set varibles from config
config = conf_parser(conf_file)
use_geoloc = cp.getboolean('weather', 'use_geoloc')
forecast_type = config['forecast_type']
cache_ageout = config['cache_ageout']
zipcode = config['zipcode']

## pre-checks
if args.verbose:
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("---VERBOSE LOGGING ENABLED---")
if not os.path.exists(conf_path):
        conf_creator()

while True:
    if args.toggle_forecast_type:
        forecast_type_toggle(forecast_type)
    if cache_new(cache_file, cache_ageout):
        break
    if use_geoloc:
        forecast_url = get_geolocation()
    else: 
        forecast_url = get_location(zipcode) 
    if args.notify_5day_forecast or forecast_type == "long":
        forecast_json = forecast_get_json(forecast_url)
        if args.notify_5day_forecast:
            forecast_5day(forecast_json)
            break
        else:
            forecast_long(forecast_json)
            break 
    elif forecast_type == "short":
        forecast_json = forecast_get_json(forecast_url + "/hourly")
        forecast_short(forecast_json)
    break

## TODO
# create throttle for geolocation requests.. 
# - cp.set zipcode
# - check if conf age is older than 900
# create icon selector
# format message
# write message
