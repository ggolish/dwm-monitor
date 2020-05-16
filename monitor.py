#!/usr/bin/env python3

import time
import json
import argparse
import sys
import logging

from os.path import expanduser, join, exists
from threading import Timer
from subprocess import getoutput as cmd

import stats
import weather

DEFAULT_CONFIG_PATH = join(expanduser("~"), ".dwmstatus")
DEFAULT_CONFIG = {
    "update_interval": 0.25,
    "weather_interval": 300.0,
    "weather_url": "https://weather.com/weather/today/l/f4486c561c03c078e900d35ff13390398a4d73bed67c8b78fbcd1e129491db92",
}
STATUS_GLOBALS = {
    "date": "",
    "weather": "",
    "volume": "",
    "mute": "",
    "ram": "",
    "cpu": "",
    "gpu": "",
}


def load_config(path):
    global DEFAULT_CONFIG
    if path is None:
        path = expanduser("~")
        path = join(path, ".dwmstatus")
    config = {}
    if exists(path):
        with open(path, "r") as fd:
            config = json.load(fd)
    for k in DEFAULT_CONFIG:
        if k not in config:
            config[k] = DEFAULT_CONFIG[k]
    return config


def update_status():
    global STATUS_GLOBALS
    topbar_status = " | ".join([STATUS_GLOBALS[k]
                                for k in ["weather", "date"]])
    cmd(f"xsetroot -name '{topbar_status}'")


def launch_update_method(method, interval, key, args=[]):
    global STATUS_GLOBALS
    logging.debug(f"Running {method}, setting {key}")
    STATUS_GLOBALS[key] = method(*args)
    t = Timer(interval, launch_update_method,
              args=[method, interval, key, args])
    t.start()


def main(args):
    global STATUS_GLOBALS
    config = load_config(path=args.config)
    launch_update_method(stats.get_date, 1.0, "date")
    launch_update_method(weather.retrieve_report, config["weather_interval"],
                         "weather", args=[config["weather_url"]])
    while True:
        update_status()
        time.sleep(config["update_interval"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default=DEFAULT_CONFIG_PATH,
                        help=f"Path to config file, default is {DEFAULT_CONFIG_PATH}")
    parser.add_argument("--log", type=str, default="WARNING",
                        help="Log level: DEBUG | INFO | WARNING")

    args = parser.parse_args(sys.argv[1:])

    log_level = getattr(logging, args.log.upper())
    logging.basicConfig(level=log_level, format='%(asctime)s %(message)s')

    main(args)
