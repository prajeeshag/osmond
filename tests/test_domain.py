import glob

from osmond import (
    create_domain,
    process_meteo_files,
    process_ocean_files,
    process_wave_files,
)

# box = [-20.0, -10.0, 10.0, 30.0]
# box = [17.39, 19.289, 32.47, 34.27]
box = [50.86, 53.81, 25.45, 27.25]

create_domain("GEBCO_2024_sub_ice_topo.nc", box[0], box[1], box[2], box[3], "test")
