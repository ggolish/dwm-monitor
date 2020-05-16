import requests
from bs4 import BeautifulSoup


def retrieve_report(url):
    try:
        req = requests.get(url)
        soup = BeautifulSoup(req.content, "html.parser")
        wstats = {}
        wstats["curr_temp"] = soup.find(
            class_="today_nowcard-temp").find("span").text
        wstats["desc"] = soup.find(class_="today_nowcard-phrase").text
        warning = soup.find("span", class_="warning-text")
        if warning:
            wstats["desc"] += f" ({warning.text.upper()})"
        wstats["low_temp"], wstats["high_temp"] = sorted(
            [e.find("span").text for e in soup.find_all(class_="deg-hilo-nowcard")])
        if wstats["low_temp"] == "--":
            return f"{wstats['desc']} {wstats['curr_temp']} ({wstats['high_temp']}▼)"
        else:
            return f"{wstats['desc']} {wstats['curr_temp']} ({wstats['low_temp']}▼, {wstats['high_temp']}▲)"
    except:
        return "Unable to retrieve weather data"


if __name__ == "__main__":

    url = "https://weather.com/weather/today/l/f4486c561c03c078e900d35ff13390398a4d73bed67c8b78fbcd1e129491db92"
    print(retrieve_report(url))
