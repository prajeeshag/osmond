import glob
import os

import numpy as np

from osmond import (
    create_domain,
    process_meteo_files,
    process_ocean_files,
    process_wave_files,
)

script_filename = os.path.basename(__file__)

box = [-1.154541, 5.845458984, -0.693494, 5.306505684]

output_dir = f"output/{script_filename}"


create_domain(
    "GEBCO_2024_sub_ice_topo.nc", box[0], box[1], box[2], box[3], f"{output_dir}/glbl"
)
print("done domain")

atmos_files = glob.glob("test_data/input/atmos/2025012112/*.nc")
ds_list = process_meteo_files(
    atmos_files, box[0], box[1], box[2], box[3], f"{output_dir}/atmos/"
)

if np.any(ds_list[0]["longitude"].values > 180):  # type: ignore
    print(ds_list[0]["longitude"].values)  # type: ignore
    raise ValueError("longitude needs to be -180 to 180")

print("done meteo")

ocean_files = glob.glob("test_data/input/ocean/2025012112/*.nc")
process_ocean_files(ocean_files, box[0], box[1], box[2], box[3], f"{output_dir}/ocean/")
print("done ocean")

wave_files = glob.glob("test_data/input/waves/2025012112/*.nc")
process_wave_files(wave_files, box[0], box[1], box[2], box[3], f"{output_dir}/wave/")
print("done wave")
