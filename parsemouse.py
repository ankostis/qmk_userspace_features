# pip install pandas plotly matplotlib kaleido

# %%
import pickle
import re
import sys
from collections import defaultdict, Counter
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from plotly import express as px
from plotly import graph_objects as go

import subprocess as sbp
import time

import ipywidgets as w

# %%
cols = "DPI Dinch Vinch".split()
fname = Path("parsemouse-qmkconsole-dv_inch_per_dpi.log")
regex = r"MACCEL: DPI: +(\d+) +Dinch:  +(-?\d+\.\d+) +Vinch:  +(-?\d+\.\d+)"
parsers = [int, float, float]


def parsing_console(f, regex=regex, parsers=parsers, cols=cols):
    for line in f:
        m = re.search(regex, line)
        if not m:
            continue
        yield [f(d) for f, d in zip(parsers, m.groups())]


# %%
try:
    with open(fname.with_suffix(".pickle"), "rb") as f:
        data = pickle.load(f)
except FileNotFoundError as ex:
    print(f"{ex}!  Starting collecting data anew.")
    data = Counter()


# %%
def to_df(data):
    df_data = [[*k_tuple, count] for k_tuple, count in data.items()]
    df = pd.DataFrame(df_data, columns="DPI field value count".split())

    df = (
        df.set_index("DPI field value".split())
        .unstack("field")
        .droplevel(0, axis=1)
        .reset_index()
    )

    df.
    return df


def to_series(data, fields):
    df = to_df(data)
    return [df.loc[:, c].dropna().astype(np.int32) for c in fields]


df = to_df(data)



# %%

plot_interval_sec = 1.2
t_last = time.time()
size_scale = 2e0

fig = go.FigureWidget(data=[
        go.Scatter(
            x=[0],
            y=[0],
            marker_size=[0],
            mode="markers",
            name=f"{cols[1]} inches x 10,000",
        ),
        go.Scatter(
            x=[0],
            y=[0],
            marker_size=[0],
            mode="markers",
            name=f"{cols[2]} inches x 10,000",
        )
    ]
    , layout=go.Layout(xaxis_title=cols[0])
                      )
display(fig)
# f = sys.stdin
proc = sbp.Popen(["qmk", "console"], stdout=sbp.PIPE, universal_newlines=True)
f = proc.stdout
try:
    for dpi, *values in parsing_console(f, regex, parsers, cols):
        data.update([(dpi, col, v) for col, v in zip(cols[1:], values, strict=True)])

        t = time.time()
        elapsed = t - t_last
        if elapsed < plot_interval_sec:
            continue
        t_last = t

        # print(dpi, values)

        df = to_df(data)
        with fig.batch_update():
            counts = df.dropna(subset=cols[1])
            fig.data[0].x = counts[cols[0]] - 20
            fig.data[0].y = counts["value"]
            fig.data[0].marker.size =  size_scale * np.log(counts[cols[1]])

            counts = df.dropna(subset=cols[2])
            fig.data[1].x = counts[cols[0]] + 20
            fig.data[1].y = counts["value"]
            fig.data[1].marker.size = size_scale * np.log(counts[cols[2]])

            fig.layout.title = f"Current dpi: {dpi}"

        # g = go.FigureWidget(data=[trace1])
except KeyboardInterrupt:
    pass
finally:
    proc.terminate()


# %%
with open(fname.with_suffix(".pickle"), "wb") as f:
    pickle.dump(data, f)
# %%
# Generate static diagrag for GitHub: https://plotly.com/python/static-image-export/
fig.show("png")
