import glob
import os

from osmond import (
    create_domain,
    process_meteo_files,
    process_ocean_files,
    process_wave_files,
)

script_filename = os.path.basename(__file__)

box = [18.16, 19.26, 38.09, 39.18]

output_dir = f"output/{script_filename}"

create_domain(
    "GEBCO_2024_sub_ice_topo.nc", box[0], box[1], box[2], box[3], f"{output_dir}/glbl"
)

atmos_files = glob.glob("test_data/input/atmos/2025012112/*.nc")
process_meteo_files(atmos_files, box[0], box[1], box[2], box[3], f"{output_dir}/atmos/")

ocean_files = glob.glob("test_data/input/ocean/2025012112/*.nc")
process_ocean_files(ocean_files, box[0], box[1], box[2], box[3], f"{output_dir}/ocean/")

wave_files = glob.glob("test_data/input/waves/2025012112/*.nc")
process_wave_files(wave_files, box[0], box[1], box[2], box[3], f"{output_dir}/wave/")
