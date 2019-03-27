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

def debug_config():
    logging.debug("---START CONFIG---")
    logging.debug("conf_file: " + conf_file)
    logging.debug("cache_file: " + cache_file)
    logging.debug("zipcode: " + zipcode)
    logging.debug("cache_ageout: " + cache_ageout)
    logging.debug("forecat_type: " + forecast_type)
    if use_geoloc:
        logging.debug("use_geoloc: true")
    else:
        logging.debug("use_geoloc: false")
    logging.debug("---END CONFIG---")

def conf_parser(config_file):
    cp.read(config_file)
    config = cp._sections["weather"]
    return config

def forecast_location(use_geoloc, zipcode):
    if use_geoloc:
        location = requests.get('https://ipinfo.io/json')
        json = location.json()
        location = json['loc']
    else:
        from uszipcode import SearchEngine
        search = SearchEngine()
        zipcode = search.by_zipcode(zipcode)
        zipcode = zipcode.to_dict()
        latlong = zipcode['lat'],zipcode['lng']
        location = ("{0[0]},{0[1]}").format(latlong)
    return forecast_get_url(location)

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

def forecast_url_reponse(forecast_url):
    response = requests.get(forecast_url)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.debug(e)
        return(False)
    else:
        return(True)

def forecast_type_toggle(forecast_type):
    if forecast_type == "short":
        cp.set('weather', 'forecast_type', 'long')
    elif forecast_type == "long":
        cp.set('weather', 'forecast_type', 'short')
    with open(conf_file, 'w') as conf:
        cp.write(conf)

def forecast_refresh(cache_ageout):
    import time
    current_time = int(time.time())
    cache_mod = int(os.stat(cache_file).st_mtime)
    conf_mod = int(os.stat(conf_file).st_mtime)
    logging.debug("CURRENT TIME: " + str(current_time))
    logging.debug("CONF AGE: " + str(current_time - conf_mod))
    logging.debug("CACHE AGE: " + str(current_time - cache_mod))
    if (current_time - conf_mod) == "0":
        logging.debug("Confile file is NEW! REFRESHING")
        logging.debug(conf + "is 0")
    elif (current_time - conf_mod) < (current_time - cache_mod):
        logging.debug("Conf file is newer than Cache file!! REFRESHING ")
    elif (current_time - cache_mod) > int(cache_ageout):
        logging.debug("Cache file is older than " + cache_ageout + "!! REFRESHING ")
    elif (current_time - cache_mod) < int(cache_ageout):
        logging.debug("Cache file is newer than " + cache_ageout + " EXITING")
        return(False)
    return(True)

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

## get conf_age and cache_age

while True:
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        debug_config()
    if not os.path.exists(conf_path):
        conf_creator()
    if args.toggle_forecast_type:
        forecast_type_toggle(forecast_type)
    if forecast_refresh(cache_ageout):
        break
        forecast_url = forecast_location(zipcode, use_geoloc)
    else:
        break
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
