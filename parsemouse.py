# pip install pandas plotly matplotlib kaleido

# %%
import itertools as itt
import logging
import pickle
import re
import subprocess as sbp
import sys
import threading
import time
from collections import Counter, defaultdict
from pathlib import Path

import ipywidgets as w
import numpy as np
import pandas as pd
import plotly.io as pio
from matplotlib import pyplot as plt
from plotly import express as px
from plotly import graph_objects as go
from plotly.subplots import make_subplots

# %%
logging.basicConfig(level=logging.INFO, force=True)
log = logging.getLogger("parsemouse")

# %%
cols = "DPI Dinch Vinch".split()
regex = r"MACCEL: DPI: +(\d+) +Dinch: +(-?\d+\.\d+) +Vinch: +(-?\d+\.\d+)"
parsers = [int, float, float]
maxing_afterglow_ts = 1.7


show_logs_btn = w.ToggleButton(
    description="Show logs (or max)? (click before launching cell)"
)
logs_text = w.Text()  # Sdisabled=True)
logs_text.layout.width = "100%"
max_values = ()


def parsing_console(f, regex=regex, parsers=parsers):
    global max_values

    last_maxing_ts = 0
    for line_no, line in enumerate(f):
        m = re.search(regex, line)
        if not m:
            continue
        values = [f(d) for f, d in zip(parsers, m.groups())]

        if show_logs_btn.value:
            msg = line
        else:
            t = time.time()
            if (t - last_maxing_ts) > maxing_afterglow_ts:
                max_values = ()
            last_maxing_ts = t
            max_values = [
                max(abs(v), m)
                for v, m in itt.zip_longest(values, max_values, fillvalue=0)
            ]
            msg = ", ".join([f"{c}: {v}" for c, v in zip(cols, max_values)])
        logs_text.value = f"{line_no}: MAX: {msg}"

        yield values


# %%
fname = Path("parsemouse-qmkconsole-dv_inch_per_dpi")

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
# pio.renderers.default = "notebook_connected"


# %%

plot_interval_sec = 1.2
size_scale = 2e0

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.update_layout(go.Layout(xaxis_title=cols[0]))
fig.add_trace(
    go.Scatter(
        x=[0],
        y=[0],
        marker_size=[0],
        mode="markers",
        name=f"{cols[1]}",
    ),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(
        x=[0],
        y=[0],
        marker_size=[0],
        mode="markers",
        name=f"{cols[2]}",
    ),
    secondary_y=True,
)
px_colors = px.colors.qualitative.Plotly
fig.update_yaxes(
    title_text=r"$\text{Distance} [\frac{\text{inches}}{1000}]$)",
    color=px_colors[0],
    rangemode="tozero",
    secondary_y=False,
)
fig.update_yaxes(
    title_text=r"$\text{Velocity} [\frac{\text{inches}}{1000 \times \text{duty_cycle}(\text{~1ms})})$]",
    color=px_colors[1],
    rangemode="tozero",
    secondary_y=True,
)


def update_fig(fig, df, dpi="?"):
    if df.empty:
        return

    df = df.abs()
    col = cols[1]
    counts = df.dropna(subset=col).loc[df["value"] > 0]
    fig.data[0].x = counts[cols[0]] - 5
    fig.data[0].y = counts["value"]
    fig.data[0].marker.size = size_scale * np.log(counts[col])

    col = cols[2]
    counts = df.dropna(subset=col).loc[df["value"] > 0]
    fig.data[1].x = counts[cols[0]] + 5
    fig.data[1].y = counts["value"]
    fig.data[1].marker.size = size_scale * np.log(counts[col])

    fig.layout.title = f"Current dpi: {dpi}, #samples: {df[col].sum()}"


fig = go.FigureWidget(fig)
update_fig(fig, df)
break_loop_btn = w.Button(description="STOP qmk console", icon="ban")


def break_loop(_btn):
    break_loop.var = True

break_loop_btn.on_click(break_loop)
# %%
display(fig, w.HBox((break_loop_btn, show_logs_btn)), logs_text)

# %%
break_loop.var = False
break_loop_btn.button_style = "success"

def pump_qmk_console(proc):
    # f = sys.stdin
    f = proc.stdout
    t_last = time.time()
    try:
        for dpi, *values in parsing_console(f, regex, parsers):
            if break_loop.var:
                break
            data.update(
                [(dpi, col, v) for col, v in zip(cols[1:], values, strict=True)]
            )

            t = time.time()
            elapsed = t - t_last
            if elapsed < plot_interval_sec:
                continue
            t_last = t

            # print(dpi, values)

            df = to_df(data)
            with fig.batch_update():
                update_fig(fig, df, dpi)

    except KeyboardInterrupt:
        pass
    finally:
        log.info("Loop ended.")
        proc.terminate()
        break_loop_btn.button_style = ""


proc = sbp.Popen(["qmk", "console"], stdout=sbp.PIPE, universal_newlines=True)
thread = threading.Thread(target=pump_qmk_console, args=[proc])

thread.start()

# %%
# View the above live in nbviewer:
#   https://nbviewer.org/github/ankostis/qmk_userspace_features/blob/qmk-log-stats/parsemouse.ipynb

# %%
# Generate static diagrag for GitHub: https://plotly.com/python/static-image-export/
fig.show("svg", width=1200)
# %%
# Test if it works
fig.show("notebook_connected", width=1200)
# %%
## Store collected logs, for the next time to run to appendp mose logs on top.
with open(fname.with_suffix(".pickle"), "wb") as f:
    pickle.dump(data, f)
