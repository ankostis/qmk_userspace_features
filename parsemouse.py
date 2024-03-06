# pip install pandas plotly matplotlib kaleido

# %%
import pickle
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from plotly import express as px
from plotly import graph_objects as go

# %%
cols = "DPI Dinch Vinch".split()
fname = Path("parsemouse-qmkconsole-v_inch_per_dpi.log")
regex = r"MACCEL: DPI: +(\d+) +Vinch:  +(-?\d+\.\d+)"
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
    data = defaultdict(set)
# %%


import subprocess as sbp
import time

import ipywidgets as w


def to_df(data):
    df_data = [[dpi, i] for dpi, inches in data.items() for i in inches]
    return pd.DataFrame(df_data, columns=cols)


plot_interval_sec = 1.2
t_last = time.time()

wout = w.Output()
fig = go.FigureWidget(data=[go.Scatter(mode="markers")])
display(fig, wout)
# f = sys.stdin
proc = sbp.Popen(["qmk", "console"], stdout=sbp.PIPE, universal_newlines=True)
f = proc.stdout
try:
    last_dpi = ""
    for dpi, inch in parsing_console(f, regex, parsers, cols):
        data[dpi].add(inch)

        last_dpi = dpi
        t = time.time()
        elapsed = t - t_last
        if elapsed < plot_interval_sec:
            continue

        t_last = t
        df = to_df(data)
        wout.clear_output(wait=True)
        wout.append_stdout(last_dpi)

        # trace1 = go.Scatter(df, x=cols[0], y=cols[1], name="inches x 10,000")
        with fig.batch_update():
            fig.data[0].x = df[cols[0]]
            fig.data[0].y = df[cols[1]]
            fig.layout.title = str(dpi)

        # g = go.FigureWidget(data=[trace1])
except KeyboardInterrupt:
    pass
finally:
    proc.terminate()


# %%
with open(fname.with_suffix(".pickle"), "wb") as f:
    pickle.dump(data, f)
# %%
