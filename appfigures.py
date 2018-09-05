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
    from datetime import datetime

    # Remove last couple days, since they're 0
    return list(
        zip(
            *[
                (
                    datetime.strptime(z["date"], "%Y-%m-%d"),
                    z["downloads"],
                    z["updates"],
                    z["downloads"] - z["uninstalls"],
                )
                for z in sorted(pj.values(), key=lambda _: _["date"])
            ][:-4]
        )
    )


def combineDaily(pj, func, numDays):
    assert numDays in (1, 7)
    return tuple([func(pj[i : i + numDays]) for i in range(0, len(pj), numDays)])


def getLastElem(arr):
    return arr[-1]


def getAxes(t, y_axis_choice, numDays):
    assert len(t[0]) == len(t[y_axis_choice])
    assert y_axis_choice in (1, 2, 3)
    assert numDays in (1, 7)
    assert t[0] == combineDaily(t[0], getLastElem, 1)
    assert t[y_axis_choice] == combineDaily(t[y_axis_choice], sum, 1)

    return (
        combineDaily(t[0], getLastElem, numDays),
        combineDaily(t[y_axis_choice], sum, numDays),
    )


def plotData(filename, ylabel, timespan, x, y):
    # allow this to run on a headless server
    import matplotlib

    matplotlib.use("Agg")

    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    assert len(x) == len(y)

    # https://stackoverflow.com/questions/9627686/plotting-dates-on-the-x-axis-with-pythons-matplotlib#9627970
    plt.clf()
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xlabel("Date")

    assert ylabel in ("Downloads", "Updates", "Net New Installs")
    plt.ylabel(ylabel)

    assert timespan in ("Daily", "Weekly")
    plt.title("Status.im %s %s (Appfigures)" % (timespan, ylabel))

    plt.plot(x, y)
    plt.gcf().autofmt_xdate()
    plt.savefig(filename, dpi=150)


def checkOutputPath(path):
    from os import access, F_OK

    return access(path, F_OK)


def main():
    from json import loads
    from os.path import join
    from sys import argv

    outputPath = argv[1]

    # TOCTOU, but doesn't much matter. Just helpful to detect
    # failures early if possible.
    assert checkOutputPath(outputPath)

    getPath = lambda n: join(outputPath, n)

    data = getData(loads(openURL("sales/dates/-120/0").read()))

    # data has, in order: date, downloads, updates, and net new installs
    for interval, numDays in (("Daily", 1), ("Weekly", 7)):
        fi = interval.lower()
        plotData(
            getPath("downloads_%s.png" % fi),
            "Downloads",
            interval,
            *getAxes(data, 1, numDays)
        )
        plotData(
            getPath("updates_%s.png" % fi),
            "Updates",
            interval,
            *getAxes(data, 2, numDays)
        )
        plotData(
            getPath("netnewinstalls_%s.png" % fi),
            "Net New Installs",
            interval,
            *getAxes(data, 3, numDays)
        )


main()
