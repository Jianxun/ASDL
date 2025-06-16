import wave_view as wv
import numpy as np


spice_file = "/foss/designs/simulations/tb_ota_5t/test_tran_square/results.raw"

data = wv.load_spice(spice_file)

# print(f"Total signals: {len(data.signals)}")
# for signal in data.signals:
#     print(f"  - {signal}")


# Now proceed with plotting using YAML configuration
custom_config = wv.config_from_yaml("""
title: "Transient Analysis"

X:
  signal_key: "time"
  label: "Time (s)"

Y:
  - label: "Voltages (V)"
    signals:
      Input: "v(in)"
      Output: "v(out)"
      VDDA: "v(vdda)"
      VSSA: "v(vssa)"
      
plot_height: 600
show_zoom_buttons: true
show_rangeslider: true
""")

fig1 = wv.plot(spice_file, custom_config, show=True)
