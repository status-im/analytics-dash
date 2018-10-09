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


def plotData(filename, ylabel, timespan, x, y):
    # TODO: factor out as common routine
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

    plt.ylabel(ylabel)

    plt.title("Status.im %s %s (Prometheus)" % (timespan, ylabel))

    plt.plot(x, y)
    plt.gcf().autofmt_xdate()
    plt.savefig(filename, dpi=150)


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

    plotData(
        getPath("whisper_distinct_users_daily.png"),
        "Whisper Users (Public Channels)",
        "Daily",
        *distinct_users()
    )

    plotData(
        getPath("whisper_messages_hourly.png"),
        "Whisper Messages (Public Channels)",
        "Hourly",
        *getData(
            parse_data(
                openPrometheusURL("sum(rate(shh_messages_total[1h]))*3600", "1h")
            )
        )
    )

    plotData(
        getPath("whisper_messages_daily.png"),
        "Whisper Messages (Public Channels)",
        "Daily",
        *getData(
            parse_data(
                openPrometheusURL("sum(rate(shh_messages_total[1d]))*3600*24", "1d")
            )
        )
    )

    plotData(
        getPath("whisper_messages_weekly.png"),
        "Whisper Messages (Public Channels)",
        "Weekly",
        *getData(
            parse_data(
                openPrometheusURL("sum(rate(shh_messages_total[1w]))*3600*24*7", "1w")
            )
        )
    )


main()
