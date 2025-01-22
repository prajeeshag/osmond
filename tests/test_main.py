import glob

from osmond import create_domain, subset_forcings

create_domain("GEBCO_2024_sub_ice_topo.nc", 20.0, 60.0, 10.0, 35.0, "output/glbl")

atmos_files = glob.glob("test_data/atmosphere/2025012012/*.nc")
subset_forcings(atmos_files, 20.0, 60.0, 10.0, 35.0, "output/atmos/")

ocean_files = glob.glob("test_data/ocean/2025011912/*.nc")
subset_forcings(ocean_files, 20.0, 60.0, 10.0, 35.0, "output/ocean/")
