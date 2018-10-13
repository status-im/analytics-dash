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


def createPlotScript(filename, ylabel, timespan, x, y):
    # TODO: refactor
    # TODO: the div names need to be distinct; they'll be a param basically
    # cache https://cdn.plot.ly/plotly-latest.min.js locally
    from operator import methodcaller

    assert len(x) == len(y)

    series_template = 'var series1 = { type: "scatter", mode: "lines", name: "SERIES_NAME", x: ["X_DATA"], y: ["Y_DATA"], line: {color: "COLOR"}}'
    new_plot_template = 'Plotly.newPlot("DIV_NAME", [series1], {title: "TITLE"});'
    title = "Status.im %s %s" % (timespan, ylabel)
    series = (
        series_template.replace("SERIES_NAME", ylabel)
        .replace("COLOR", "#17BECF")
        .replace("X_DATA", '", "'.join(map(methodcaller("isoformat"), x)))
        .replace("Y_DATA", '", "'.join(map(str, y)))
    )
    new_plot = new_plot_template.replace("TITLE", title).replace("DIV_NAME", "myDiv")
    with open(filename, "w") as f:
        f.write("\n".join([series, new_plot]))


def checkOutputPath(path):
    from os import access, F_OK

    return access(path, F_OK)


def main():
    from json import loads
    from os.path import join
    from sys import argv

    outputPath = argv[1]
    assert checkOutputPath(outputPath)
    getPath = lambda n: join(outputPath, n)

    data = getData(loads(openURL("sales/dates/-120/0").read()))

    # data has, in order: date, downloads, updates, and net new installs
    for interval, numDays in (("Daily", 1), ("Weekly", 7)):
        fi = interval.lower()
        createPlotScript(
            getPath("downloads_%s.js" % fi),
            "Downloads",
            interval,
            *getAxes(data, 1, numDays)
        )
        createPlotScript(
            getPath("updates_%s.js" % fi),
            "Updates",
            interval,
            *getAxes(data, 2, numDays)
        )
        createPlotScript(
            getPath("netnewinstalls_%s.js" % fi),
            "Net New Installs",
            interval,
            *getAxes(data, 3, numDays)
        )


main()
