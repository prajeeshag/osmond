import glob

from osmond import (
    create_domain,
    process_meteo_files,
    process_ocean_files,
    process_wave_files,
)

create_domain("GEBCO_2024_sub_ice_topo.nc", 20.0, 60.0, 10.0, 35.0, "output/glbl")

atmos_files = glob.glob("test_data/input/atmos/2025012112/*.nc")
process_meteo_files(atmos_files, 20.0, 60.0, 10.0, 35.0, "output/atmos/")

ocean_files = glob.glob("test_data/input/ocean/2025012112/*.nc")
process_ocean_files(ocean_files, 20.0, 60.0, 10.0, 35.0, "output/ocean/")

wave_files = glob.glob("test_data/input/waves/2025012112/*.nc")
process_wave_files(wave_files, 20.0, 60.0, 10.0, 35.0, "output/wave/")
