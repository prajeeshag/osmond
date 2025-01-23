import glob

from osmond import (
    create_domain,
    process_meteo_files,
    process_ocean_files,
    process_wave_files,
)

box = [-20.0, -10.0, 10.0, 30.0]

create_domain(
    "GEBCO_2024_sub_ice_topo.nc", box[0], box[1], box[2], box[3], "output/glbl"
)

atmos_files = glob.glob("test_data/input/atmos/2025012112/*.nc")
process_meteo_files(atmos_files, box[0], box[1], box[2], box[3], "output/atmos/")

ocean_files = glob.glob("test_data/input/ocean/2025012112/*.nc")
process_ocean_files(ocean_files, box[0], box[1], box[2], box[3], "output/ocean/")

wave_files = glob.glob("test_data/input/waves/2025012112/*.nc")
process_wave_files(wave_files, box[0], box[1], box[2], box[3], "output/wave/")
