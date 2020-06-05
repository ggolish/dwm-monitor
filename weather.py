import requests
import logging
import time
from bs4 import BeautifulSoup


def retrieve_report(url, tries=0, max_tries=10):
    try:
        req = requests.get(url)
        soup = BeautifulSoup(req.content, "html.parser")
        wstats = {}
        wstats["curr_temp"] = soup.find("span", {"data-testid": "TemperatureValue"}).text
        wstats["desc"] = soup.find("div", {"data-testid": "wxPhrase"}).text
        warning = soup.find("span", class_="warning-text")
        if warning:
            wstats["desc"] += f" ({warning.text.upper()})"
        wstats["low_temp"], wstats["high_temp"] = sorted(
                [e.text for e in soup.find_all("span", {"data-testid": "TemperatureValue"})[1:3]])
        if wstats["low_temp"] == "--":
            return f"{wstats['desc']} {wstats['curr_temp']} ({wstats['high_temp']}▼)"
        else:
            return f"{wstats['desc']} {wstats['curr_temp']} ({wstats['low_temp']}▼, {wstats['high_temp']}▲)"
    except Exception as e:
        logging.warning(f"Unable to retrieve weather data: {str(e)}")
        if tries < max_tries:
            time.sleep(5)
            return retrieve_report(url, tries=tries+1)
        return "Unable to retrieve weather data"


if __name__ == "__main__":

    url = "https://weather.com/weather/today/l/f4486c561c03c078e900d35ff13390398a4d73bed67c8b78fbcd1e129491db92"
    print(retrieve_report(url))
