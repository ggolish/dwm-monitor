#!/usr/bin/env python3

import time
import json
import argparse
import sys
import logging
import psutil

from os.path import expanduser, join, exists
from os import getpid, makedirs
from threading import Timer
from subprocess import run

import stats
import weather

DEFAULT_CONFIG_PATH = join(expanduser("~"), ".dwmstatus")
DEFAULT_LOG_PATH = join(expanduser("~"), ".dwmlog")
DEFAULT_CONFIG = {
    "os": "arch",
    "update_interval": 0.5,
    "pacman_interval": 1,
    "hardware_interval": 1.0,
    "weather_interval": 300.0,
    "weather_url": "https://weather.com/weather/today/l/f4486c561c03c078e900d35ff13390398a4d73bed67c8b78fbcd1e129491db92",
    "cpu_sensor_dev": "k10temp",
    "cpu_sensor_label": "Tdie",
    "gpu_sensor_dev": "amdgpu",
    "gpu_sensor_label": "edge",
    "battery": False,
    "mpchost": "/home/ggolish/.config/mpd/socket",
    "mpcport": "6600",
    "phone_interval": 0,
}
STATUS_GLOBALS = {
    "date": "",
    "weather": "",
    "pacman": "",
    "volume": "",
    "ram": "",
    "cpu": "",
    "gpu": "",
    "track": "",
    "net": "",
    "battery": "",
    "pacman": "",
    "phone": "",
}


def reap_zombies():
    for p in psutil.process_iter():
        if "dwm-monitor" in p.name() and p.pid != getpid():
            p.kill()


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


def store_default_config():
    global DEFAULT_CONFIG, DEFAULT_CONFIG_PATH
    with open(DEFAULT_CONFIG_PATH, "w") as fd:
        json.dump(DEFAULT_CONFIG, fd, sort_keys=True,
                  indent=4, separators=(",", ": "))


def update_status():
    global STATUS_GLOBALS
    topbar_status = " | ".join([STATUS_GLOBALS[k] for k in ["weather",
        "pacman", "date", "phone", "battery"] if STATUS_GLOBALS[k] != ""])
    bottombar_status = " | ".join([STATUS_GLOBALS[k] for k in ["volume", "ram",
        "cpu", "gpu", "net", "track"] if STATUS_GLOBALS[k] != ""])
    x = run(["xsetroot", "-name", f"{topbar_status};{bottombar_status}"], capture_output=True)
    if x.returncode != 0:
        logging.warn(f"xsetroot failure: {x.stderr.decode()}")
        run(["xsetroot", "-name", "xsetroot failure!"])


def store_status(dest):
    global STATUS_GLOBALS
    for f in STATUS_GLOBALS.keys():
        with open(join(dest, f), "w") as fd:
            fd.write(STATUS_GLOBALS[f])


def launch_update_method(method, interval, key, args=[]):
    global STATUS_GLOBALS
    logging.debug(f"Running {method}, setting {key}")
    STATUS_GLOBALS[key] = method(*args)
    t = Timer(interval, launch_update_method,
              args=[method, interval, key, args])
    t.start()


def main(args):
    global STATUS_GLOBALS
    reap_zombies()
    config = load_config(path=args.config)

    if args.write_files:
        makedirs(args.write_files, exist_ok=True)

    launch_update_method(
        stats.get_date,
        config["update_interval"],
        "date"
    )

    launch_update_method(
        stats.get_volume,
        config["update_interval"],
        "volume"
    )

    launch_update_method(
        stats.get_ram,
        config["hardware_interval"],
        "ram"
    )

    launch_update_method(
        stats.get_net,
        config["hardware_interval"],
        "net"
    )

    launch_update_method(
        stats.get_current_track,
        config["update_interval"],
        "track",
        args=[
            config["mpchost"],
            config["mpcport"]
        ]
    )

    launch_update_method(
        stats.get_cpu,
        config["hardware_interval"],
        "cpu",
        args=[
            config["cpu_sensor_dev"],
            config["cpu_sensor_label"]
        ]
    )
    if config["gpu_sensor_dev"] != "":
        launch_update_method(
            stats.get_gpu,
            config["hardware_interval"],
            "gpu",
            args=[
                config["gpu_sensor_dev"],
                config["gpu_sensor_label"]
            ]
        )

    launch_update_method(
        weather.retrieve_report,
        config["weather_interval"],
        "weather",
        args=[
            config["weather_url"]
        ]
    )

    if config["battery"]:
        launch_update_method(
            stats.get_battery,
            config["hardware_interval"],
            "battery"
        )

    if config["os"] == "arch":
        launch_update_method(
            stats.get_pacman_updates,
            config["pacman_interval"],
            "pacman"
        )

    if config["phone_interval"] > 0:
        launch_update_method(
            stats.get_phone_connection,
            config["phone_interval"],
            "phone"
        )

    while True:
        if args.write_files:
            store_status(args.write_files)
        else:
            update_status()
        time.sleep(config["update_interval"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--store-config", action="store_true",
                        help=f"Store default config file at {DEFAULT_CONFIG_PATH}")
    parser.add_argument("--config", type=str, default=DEFAULT_CONFIG_PATH,
                        help=f"Path to config file, default is {DEFAULT_CONFIG_PATH}")
    parser.add_argument("--log", type=str, default="WARNING",
                        help="Log level: DEBUG | INFO | WARNING")
    parser.add_argument("--write-files", type=str,
            help="Store statuses in files at provided destination rather than writing xroot name")

    args = parser.parse_args(sys.argv[1:])

    if args.store_config:
        store_default_config()
        sys.exit()

    log_level = getattr(logging, args.log.upper())
    logging.basicConfig(filename=DEFAULT_LOG_PATH,
                        level=log_level, format='%(asctime)s %(message)s')

    main(args)
