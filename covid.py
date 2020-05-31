
import requests
import os
import pandas

from datetime import datetime


def retrieve_data(data_url, data_path):
    req = requests.get(data_url)
    print(req)
    with open(data_path, "w") as fd:
        fd.write(req.content.decode())


def get_stats(data_url, data_path):
    if not os.path.exists(data_path):
        retrieve_data(data_url, data_path)
    else:
        mtime = datetime.fromtimestamp(os.path.getmtime(data_path))
        today = datetime.today()
        if mtime.date() != today.date():
            retrieve_data(data_url, data_path)

    with open(data_path, "r") as fd:
        df = pandas.read_csv(fd)

    yesterday, today = list(df[df["Province_State"] == "Indiana"].sum())[-2:]
    return today, today - yesterday


def format_stats(stats):
    modifier = "▼" if stats[1] <= 0 else "▲"
    return f"{stats[0]} ({stats[1]} {modifier})"


def covid_report():
    confirmed_url = "https://github.com/CSSEGISandData/COVID-19/raw/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv"
    confirmed_path = "/tmp/covid_confirmed.csv"
    deaths_url = "https://github.com/CSSEGISandData/COVID-19/raw/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv"
    deaths_path = "/tmp/covid_deaths.csv"

    confirmed = get_stats(confirmed_url, confirmed_path)
    deaths = get_stats(deaths_url, deaths_path)
    return f"{format_stats(confirmed)} | {format_stats(deaths)}"


if __name__ == "__main__":
    print(covid_report())
