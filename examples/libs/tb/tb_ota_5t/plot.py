import yaml2plot as y2p
import pandas as pd
import xarray as xr

csv_file = "./tb.spice.csv"
# Load the CSV file into a pandas DataFrame
df = pd.read_csv(csv_file)
# Use the swept input as the xarray coordinate when available.
sweep_col = "V(IN)" if "V(IN)" in df.columns else df.columns[0]
df_indexed = df.set_index(sweep_col)
ds = xr.Dataset.from_dataframe(df_indexed)

# Now proceed with plotting using YAML configuration
spec = y2p.PlotSpec.from_yaml("""
title: "AC Analysis - Frequency Response"

X:
  signal: V(IN)
  label: V(in) (V)

Y:
  - label: Voltage (V)
    signals:
      Vout: V(OUT)
      Vin: V(IN)
  - label: Voltage (V)
    signals:
      Vtail: V(XOTA:TAIL)

height: 600
width: 800
show_rangeslider: true
""")

fig2 = y2p.plot(ds, spec)
