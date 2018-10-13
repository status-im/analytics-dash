#!/usr/bin/env python3


# sum(shh_messages_total) by (chat)


def openPrometheusURL(query, timestep):
    from time import time
    from urllib.request import urlopen

    # TODO: could escape it, but could also just avoid queries which need escaping

    cur_time = time()
    return urlopen(
        "http://master-01.do-ams3.metrics.hq.tinc:9090/api/v1/query_range?query=%s&end=%d&start=%d&step=%s"
        % (query, time(), time() - 3600 * 24 * 60, timestep)
    ).read()


def parse_data(raw_json):
    from json import loads

    j = loads(raw_json)
    assert j["status"] == "success"
    assert j["data"]["resultType"] == "matrix"
    return j["data"]["result"][0]["values"]


def getData(pj):
    from datetime import datetime

    return list(
        zip(
            *[
                (datetime.fromtimestamp(z[0]), float(z[1]))
                for z in sorted(pj, key=lambda _: _[0])
            ]
        )
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


def distinct_users():
    from collections import Counter
    from datetime import datetime
    from json import loads

    j = loads(
        openPrometheusURL(
            "sum(rate(shh_messages_total[1d])*3600)%20by%20(source)", "1d"
        )
    )
    assert j["status"] == "success"
    assert j["data"]["resultType"] == "matrix"

    distinct_user_count = Counter()
    for metric_values in j["data"]["result"]:
        source = metric_values["metric"].get("source", "")
        values = metric_values["values"]
        for epoch_time, hourly_rate in values:
            if float(hourly_rate) > 0:
                distinct_user_count[datetime.fromtimestamp(epoch_time)] += 1

    # TODO: refactor, etc
    return list(zip(*sorted(distinct_user_count.items())))


def main():
    from os.path import join
    from sys import argv

    getPath = lambda n: join(argv[1], n)

    createPlotScript(
        getPath("whisper_distinct_users_daily.js"),
        "Whisper Users (Public Channels)",
        "Daily",
        *distinct_users()
    )

    createPlotScript(
        getPath("whisper_messages_hourly.js"),
        "Whisper Messages (Public Channels)",
        "Hourly",
        *getData(
            parse_data(
                openPrometheusURL("sum(rate(shh_messages_total[1h]))*3600", "1h")
            )
        )
    )

    createPlotScript(
        getPath("whisper_messages_daily.js"),
        "Whisper Messages (Public Channels)",
        "Daily",
        *getData(
            parse_data(
                openPrometheusURL("sum(rate(shh_messages_total[1d]))*3600*24", "1d")
            )
        )
    )

    createPlotScript(
        getPath("whisper_messages_weekly.js"),
        "Whisper Messages (Public Channels)",
        "Weekly",
        *getData(
            parse_data(
                openPrometheusURL("sum(rate(shh_messages_total[1w]))*3600*24*7", "1w")
            )
        )
    )


main()
