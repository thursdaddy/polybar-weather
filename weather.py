#!/usr/local/bin/python3.6

import argparse
from configparser import ConfigParser
import logging
import os

def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="enable verbose logging", action="store_true")
    args = parser.parse_args()
    return args

def conf_checker():
    conf_path = os.environ.get("HOME") + "/.config/polybar/scripts/"
    conf_file = conf_path + "py_weather.conf"
    cache_file = conf_path + "py_weather.cache"
    if not os.path.exists(conf_path):
        os.makedirs(conf_path)
    if not os.path.exists(conf_file):
        cp.add_section('weather')
        cp.set('weather', 'use_geoloc', '0')
        cp.set('weather', 'zipcode', '10001')
        cp.set('weather', 'cache_ageout', '900')
        cp.set('weather', 'forecast_type', 'short')
        with open(conf_file, 'w') as configfile:
            cp.write(configfile)
        logging.debug("writing: " + conf_file)
    else:
        logging.debug("exists: " + conf_path)
        pass


def cache_age(cache_file):
    pass



if __name__ == '__main__':
    args = arg_parser()
    cp = ConfigParser()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("---VERBOSE LOGGING ENABLED---")
    conf_checker()
