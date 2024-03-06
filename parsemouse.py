# pip install pandas plotly matplotlib kaleido

# %%
import re

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly import express as px
import matplotlib.pyplot as plt

# %%
fname = "parsemouse-qmkconsole-v_inch_per_dpi.log"
cols = "DPI Vinch".split()
regex = r"MACCEL: DPI: +(\d+) +Vinch:  +(-?\d+\.\d+)"
parsers = [int, float]

def parse_console(fname, regex=regex, parsers=parsers, cols=cols):
    with open(fname, "rt") as f:
        logs = f.read()
        df = pd.DataFrame(
            [
                [
                    f(d)
                    for f, d in zip(parsers, m.groups())
                ]
                for m in re.finditer(regex, logs)
            ],
            columns=cols,
        )
        return df.drop_duplicates()

df = parse_console(fname, regex, parsers, cols)
df# %%

fig = px.scatter(df, x=cols[0], y=cols[1])
fig

# %%
# Generate static diagrag for GitHub: https://plotly.com/python/static-image-export/
fig.show("png")


# %%
plt.hexbin(x=df[cols[0]], y=df[cols[1]], gridsize=(df[cols[0]].nunique(), 12))
## Had to save it to a file because vscode crashes with such a big file.
# plt.savefig("parsemouse-dpihexbin.png")

# %%
