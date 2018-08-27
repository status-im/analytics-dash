#!/usr/bin/env python3


def openURL(urlFragment):
    from os import environ
    from urllib.request import Request, urlopen

    CLIENT_KEY = environ["CLIENT_KEY"]
    BASE = "https://api.appfigures.com/v2/"
    AUTH_HEADER = environ["AUTH_HEADER"]

    return urlopen(
        Request(
            BASE + urlFragment,
            headers={"X-Client-Key": CLIENT_KEY, "Authorization": AUTH_HEADER},
        )
    )


def getData(pj):
    # https://stackoverflow.com/questions/9627686/plotting-dates-on-the-x-axis-with-pythons-matplotlib#9627970
    from datetime import datetime

    # Remove last couple days, since they're 0
    return list(
        zip(
            *[
                (datetime.strptime(z["date"], "%Y-%m-%d"), z["downloads"], z["updates"])
                for z in sorted(pj.values(), key=lambda _: _["date"])
            ][:-4]
        )
    )


def combineDailyToWeekly(pj, func):
    chunkSize = 7
    return [func(pj[i : i + chunkSize]) for i in range(0, len(pj), chunkSize)]


def getLastElem(arr):
    return arr[-1]


def getDownloadsWeekly(t):
    return combineDailyToWeekly(t[0], getLastElem), combineDailyToWeekly(t[1], sum)


def getUpdatesWeekly(t):
    return combineDailyToWeekly(t[0], getLastElem), combineDailyToWeekly(t[2], sum)


def getDownloadsDaily(t):
    return t[0], t[1]


def getUpdatesDaily(t):
    return t[0], t[2]


def plotData(filename, ylabel, timespan, x, y):
    # allow this to run on a headless server
    import matplotlib
    matplotlib.use("Agg")

    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    assert len(x) == len(y)

    plt.clf()
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xlabel("Date")

    assert ylabel in ("Downloads", "Updates")
    plt.ylabel(ylabel)

    assert timespan in ("Daily", "Weekly")
    plt.title("Status.im %s %s (Appfigures)" % (timespan, ylabel))

    plt.plot(x, y)
    plt.gcf().autofmt_xdate()
    plt.savefig(filename, dpi=150)


def main():
    from json import loads
    from os.path import join
    from sys import argv

    getPath = lambda n: join(argv[1], n)

    data = getData(loads(openURL("sales/dates/-120/0").read()))
    plotData(getPath("downloads_daily.png"), "Downloads", "Daily", *getDownloadsDaily(data))
    plotData(getPath("updates_daily.png"), "Updates", "Daily", *getUpdatesDaily(data))
    plotData(getPath("downloads_weekly.png"), "Downloads", "Weekly", *getDownloadsWeekly(data))
    plotData(getPath("updates_weekly.png"), "Updates", "Weekly", *getUpdatesWeekly(data))


main()
