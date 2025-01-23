import glob
import os

from osmond import (
    create_domain,
    process_meteo_files,
    process_ocean_files,
    process_wave_files,
)

script_filename = os.path.basename(__file__)

box = [-16.3806, -10.9753, 33.6564, 37.4798]

output_dir = f"output/{script_filename}"


create_domain(
    "GEBCO_2024_sub_ice_topo.nc", box[0], box[1], box[2], box[3], f"{output_dir}/glbl"
)
print("done domain")

atmos_files = glob.glob("test_data/input/atmos/2025012112/*.nc")
process_meteo_files(atmos_files, box[0], box[1], box[2], box[3], f"{output_dir}/atmos/")
print("done meteo")

ocean_files = glob.glob("test_data/input/ocean/2025012112/*.nc")
process_ocean_files(ocean_files, box[0], box[1], box[2], box[3], f"{output_dir}/ocean/")
print("done ocean")

wave_files = glob.glob("test_data/input/waves/2025012112/*.nc")
process_wave_files(wave_files, box[0], box[1], box[2], box[3], f"{output_dir}/wave/")
print("done wave")
