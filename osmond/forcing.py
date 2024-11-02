from pathlib import Path
from typing import Annotated

import numpy as np
import pandas as pd
import typer
import xarray as xr
from xarray.coding.times import decode_cf_datetime  # type: ignore

from .config import (
    DataSetMap,
    DataSetType,
    MeteoMap,
    OceanMap,
    data_maper,
    meteo_dataset,
    ocean_dataset,
)

app = typer.Typer(add_completion=False)


@app.command()
def meteo(
    input: Annotated[Path, typer.Option(help="Input path")],
    lonlatbox: Annotated[str, typer.Option(help="<lonmin>,<lonmax>,<latmin>,<latmax>")],
    output: Annotated[Path, typer.Option(help="Output path")],
    dstype: Annotated[  # type: ignore
        MeteoMap, typer.Option(help="Input dataset type")  # type: ignore
    ] = MeteoMap.gfsnc_wgrib2.value,  # type: ignore
):
    """Create Meteorology inputs"""
    data_maps = data_maper.meteo[dstype.value]  # type: ignore
    process(input, lonlatbox, output, data_maps, meteo_dataset)


@app.command()
def ocean(
    input: Annotated[Path, typer.Option(help="Input path")],
    lonlatbox: Annotated[str, typer.Option(help="<lonmin>,<lonmax>,<latmin>,<latmax>")],
    output: Annotated[Path, typer.Option(help="Output path")],
    dstype: Annotated[  # type: ignore
        OceanMap, typer.Option(help="Input dataset type")  # type: ignore
    ] = OceanMap.cmems.value,  # type: ignore
):
    """Create Ocean inputs"""
    data_maps = data_maper.ocean[dstype.value]  # type: ignore
    process(input, lonlatbox, output, data_maps, ocean_dataset)


def process(
    input: Path,
    lonlatbox: str,
    output: Path,
    dset_map: DataSetMap,
    dset_type: DataSetType,
):
    ds = xr.open_dataset(input, chunks={}, decode_times=False)  # type: ignore
    lonmin, lonmax, latmin, latmax = map(float, lonlatbox.split(","))
    fieldname_map = {dfield.name: fname for fname, dfield in dset_map.data_vars.items()}
    ds = ds.rename_vars(fieldname_map)[list(fieldname_map.values())]
    coordname_map = {dfield.name: fname for fname, dfield in dset_map.coords.items()}
    ds = ds.rename_vars(coordname_map)
    subset_vars: dict[str, xr.DataArray] = {}
    for vname in fieldname_map.values():
        if len(ds[vname].shape) == 3:
            subset_vars[vname] = ds[vname].loc[:, latmin:latmax, lonmin:lonmax]  # type: ignore
        elif len(ds[vname].shape) == 4:
            subset_vars[vname] = ds[vname].loc[:, :, latmin:latmax, lonmin:lonmax]  # type: ignore
        else:
            raise ValueError(f"Unexpected shape {ds[vname].shape}")

    ds = xr.Dataset(subset_vars)
    ds.load()  # type: ignore
    for vname, dfield in dset_map.data_vars.items():
        if dfield.addc != 0.0:
            ds[vname] += dfield.addc
        if dfield.mulc != 1.0:
            ds[vname] *= dfield.mulc
        valid_min, valid_max = (  # type: ignore
            ds[vname].min().values,  # type: ignore
            ds[vname].max().values,  # type: ignore
        )  # type: ignore
        scale_fac, add_off, missing_val = compute_scale_and_offset(valid_min, valid_max)  # type: ignore
        scaled_data = ((ds[vname] - add_off) / scale_fac).astype(np.int16)  # type: ignore
        scaled_data = scaled_data.where(~np.isnan(ds[vname]), missing_val)
        ds[vname] = scaled_data
        ds[vname].attrs["scale_factor"] = scale_fac
        ds[vname].attrs["add_offset"] = add_off
        ds[vname].attrs["missing_value"] = missing_val
        ds[vname].attrs["valid_min"] = valid_min
        ds[vname].attrs["valid_max"] = valid_max
        data_vars_type = dset_type["data_vars"][vname]
        ds[vname].attrs["units"] = data_vars_type.units
        ds[vname].attrs["standard_name"] = data_vars_type.standard_name
        ds[vname].attrs["long_name"] = data_vars_type.long_name
    ds["time"] = process_time(ds["time"])
    ds["longitude"] = ds["longitude"].astype(np.float32)  # type: ignore
    ds["latitude"] = ds["latitude"].astype(np.float32)  # type: ignore
    ds.to_netcdf(output, unlimited_dims=["time"])  # type: ignore


def process_time(time: xr.DataArray) -> xr.DataArray:
    units = time.attrs["units"].lower()
    start_date = pd.to_datetime(  # type: ignore
        decode_cf_datetime(time[0], units)
    ).strftime("%Y-%m-%d %H:%M:%S")
    units_interval = units.split()[0].strip()
    time = time - time[0]
    if units_interval == "seconds":
        time = time / 3600
        units_interval = "hours"
    elif units_interval == "minutes":
        time = time / 60
        units_interval = "hours"
    time.attrs["units"] = f"{units_interval} since {start_date}"
    time.attrs["calendar"] = "julian"
    return time.astype(np.float32)  # type: ignore


def compute_scale_and_offset(
    data_min: float,
    data_max: float,
) -> tuple[float, float, np.int16]:
    """
    Computes the scale_factor and add_offset for converting float data to a specified integer type.

    Parameters:
    - data_min (float): The minimum value of the data.
    - data_max (float): The maximum value of the data.
    - dtype (np.dtype): The target integer data type (default is np.int16).

    Returns:
    - tuple: A tuple containing (scale_factor, add_offset, missing_value).
    """
    # Get the min and max range of the target integer type
    dtype: type = np.int16
    int_range_max = np.iinfo(dtype).max
    missing_value = np.iinfo(dtype).min
    int_range_min = missing_value + 1
    int_range = int_range_max - int_range_min
    # Compute scale_factor
    scale_factor = (data_max - data_min) / int_range
    # Compute add_offset
    add_offset = data_min + (data_max - data_min) / 2
    return scale_factor, add_offset, np.int16(missing_value)


click_app = typer.main.get_command(app)
