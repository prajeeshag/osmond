import glob

from osmond import (
    create_domain,
    process_meteo_files,
    process_ocean_files,
    process_wave_files,
)

box = [-20.0, -10.0, 10.0, 30.0]

create_domain("GEBCO_2024_sub_ice_topo.nc", box[0], box[1], box[2], box[3], "test")
