# pip install pandas plotly matplotlib kaleido

# %%
import logging
import pickle
import re
import subprocess as sbp
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import ipywidgets as w
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from plotly import express as px
from plotly import graph_objects as go

# %%
logging.basicConfig(force=True)
log = logging.getLogger("parmacmouse")

# %%
cols = "DPI Dinch Vinch".split()
regex = r"MACCEL: DPI: +(\d+) +Dinch:  +(-?\d+\.\d+) +Vinch:  +(-?\d+\.\d+)"
parsers = [int, float, float]


def parsing_console(f, regex=regex, parsers=parsers):
    for line in f:
        m = re.search(regex, line)
        if not m:
            continue
        yield [f(d) for f, d in zip(parsers, m.groups())]


# %%
fname = Path("parsemouse-qmkconsole-dv_inch_per_dpi.log")

try:
    with open(fname.with_suffix(".pickle"), "rb") as f:
        data = pickle.load(f)
except FileNotFoundError as ex:
    log.warning(f"{ex}!  Start collecting anew.")
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

    return df


def to_series(data, fields):
    df = to_df(data)
    return [df.loc[:, c].dropna().astype(np.int32) for c in fields]


df = to_df(data)


# %%

plot_interval_sec = 1.2
t_last = time.time()
size_scale = 2e0

fig = go.FigureWidget(
    data=[
        go.Scatter(
            x=[0],
            y=[0],
            marker_size=[0],
            mode="markers",
            name=f"{c} inches x 10,000",
        )
        for c in cols
    ],
    layout=go.Layout(xaxis_title=cols[0]),
)
display(fig)


def update_fig(fig, dpi="?"):
    if df.empty:
        return

    col = cols[1]
    counts = df.dropna(subset=col).loc[df[col] > 0]
    fig.data[0].x = counts[cols[0]] - 20
    fig.data[0].y = counts["value"].abs()
    fig.data[0].marker.size = size_scale * np.log(np.abs(counts[col]))

    col = cols[2]
    counts = df.dropna(subset=col).loc[df[col] > 0]
    fig.data[1].x = counts[cols[0]] + 20
    fig.data[1].y = counts["value"].abs()
    fig.data[1].marker.size = size_scale * np.log(np.abs(counts[col]))

    fig.layout.title = f"Current dpi: {dpi}"


update_fig(fig)

# f = sys.stdin
proc = sbp.Popen(["qmk", "console"], stdout=sbp.PIPE, universal_newlines=True)
f = proc.stdout
try:
    for dpi, *values in parsing_console(f, regex, parsers):
        data.update([(dpi, col, v) for col, v in zip(cols[1:], values, strict=True)])

        t = time.time()
        elapsed = t - t_last
        if elapsed < plot_interval_sec:
            continue
        t_last = t

        # print(dpi, values)

        df = to_df(data)
        with fig.batch_update():
            update_fig(fig, dpi)

except KeyboardInterrupt:
    pass
finally:
    proc.terminate()


# %%
with open(fname.with_suffix(".pickle"), "wb") as f:
    pickle.dump(data, f)
# %%
# Generate static diagrag for GitHub: https://plotly.com/python/static-image-export/
fig.show("png", width=1200)

# %%
data.total()
# %%
