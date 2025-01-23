from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from xarray.coding.times import decode_cf_datetime  # type: ignore

from .config import (
    DataSetMap,
    DataSetType,
    MeteoMap,
    OceanMap,
    WaveMap,
    data_maper,
    meteo_dataset,
    ocean_dataset,
    waves_dataset,
)


def process(
    input: Path,
    lonlatbox: list[float],
    output: Path,
    dset_map: DataSetMap,
    dset_type: DataSetType,
):
    ds = xr.open_dataset(input, chunks={}, decode_times=False)  # type: ignore
    lonmin, lonmax, latmin, latmax = lonlatbox
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

        if dset_map.depth_mapping:
            da = subset_vars[vname]
            subset_vars[vname] = xr.concat(  # type: ignore
                [
                    da.assign_coords(depth=[depth])  # type: ignore
                    for depth in dset_map.depth_mapping.output_levels
                ],
                dim="depth",
            )

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


def subset_forcings(
    infiles: list[str],
    lonmin: float,
    lonmax: float,
    latmin: float,
    latmax: float,
    output_dir: str,
):
    for infile in infiles:
        fname = Path(infile).name
        output = Path(output_dir) / fname
        subset_forcing(infile, lonmin, lonmax, latmin, latmax, output.as_posix())


def subset_forcing(
    infile: str,
    lonmin: float,
    lonmax: float,
    latmin: float,
    latmax: float,
    output: str,
):
    ds = xr.open_dataset(infile, chunks={}, decode_times=False)  # type: ignore
    subset_vars: dict[str, xr.DataArray] = {}
    for var in ds.data_vars:
        if len(ds[var].shape) == 3:  # type: ignore
            subset_vars[var] = ds[var].loc[:, latmin:latmax, lonmin:lonmax]  # type: ignore
        elif len(ds[var].shape) == 4:  # type: ignore
            subset_vars[var] = ds[var].loc[:, :, latmin:latmax, lonmin:lonmax]  # type: ignore
        else:
            raise ValueError(
                f"Unexpected shape {ds[var].shape} for variable '{var}' in file '{infile}'"  # type: ignore
            )

    ds = xr.Dataset(subset_vars)
    ds.load()  # type: ignore
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    ds.to_netcdf(output)  # type: ignore


def process_meteo_file(
    infile: str,
    lonmin: float,
    lonmax: float,
    latmin: float,
    latmax: float,
    output_dir: str,
):
    """Create Meteorology inputs"""
    data_maps = data_maper.meteo[MeteoMap.gfsnc_wgrib2.value]  # type: ignore
    output = Path(output_dir) / Path(infile).name
    process(
        Path(infile),
        [lonmin, lonmax, latmin, latmax],
        output,
        data_maps,
        meteo_dataset,
    )


def process_ocean_file(
    infile: str,
    lonmin: float,
    lonmax: float,
    latmin: float,
    latmax: float,
    output_dir: str,
):
    """Create Ocean inputs"""
    data_maps = data_maper.ocean[OceanMap.cmems.value]  # type: ignore
    output = Path(output_dir) / Path(infile).name
    process(
        Path(infile),
        [lonmin, lonmax, latmin, latmax],
        output,
        data_maps,
        ocean_dataset,
    )


def process_wave_file(
    infile: str,
    lonmin: float,
    lonmax: float,
    latmin: float,
    latmax: float,
    output_dir: str,
):
    """Create Ocean inputs"""
    data_maps = data_maper.waves[WaveMap.cmems.value]  # type: ignore
    output = Path(output_dir) / Path(infile).name
    process(
        Path(infile),
        [lonmin, lonmax, latmin, latmax],
        output,
        data_maps,
        waves_dataset,
    )


def process_meteo_files(
    infiles: list[str],
    lonmin: float,
    lonmax: float,
    latmin: float,
    latmax: float,
    output_dir: str,
):
    """
    Processes multiple meteorology input files and generates outputs for a specified geographic bounding box.

    Args:
        infiles (list[str]):
            A list of input file paths to process.
        lonmin (float):
            The minimum longitude for the geographic bounding box.
        lonmax (float):
            The maximum longitude for the geographic bounding box.
        latmin (float):
            The minimum latitude for the geographic bounding box.
        latmax (float):
            The maximum latitude for the geographic bounding box.
        output_dir (str):
            The directory where processed files will be saved.

    Returns:
        None:
            This function does not return a value. Processed files are saved in the specified `output_dir`.

    Example:\n
        >>> infiles = ["/path/to/input1.nc", "/path/to/input2.nc"]
        >>> lonmin = -10.0
        >>> lonmax = 10.0
        >>> latmin = -5.0
        >>> latmax = 5.0
        >>> output_dir = "/path/to/output"
        >>> process_meteo_files(infiles, lonmin, lonmax, latmin, latmax, output_dir)
    """
    for infile in infiles:
        process_meteo_file(infile, lonmin, lonmax, latmin, latmax, output_dir)


def process_ocean_files(
    infiles: list[str],
    lonmin: float,
    lonmax: float,
    latmin: float,
    latmax: float,
    output_dir: str,
):
    """
    Processes multiple ocean input files and generates outputs for a specified geographic bounding box.

    Args:
        infiles (list[str]):
            A list of input file paths to process.
        lonmin (float):
            The minimum longitude for the geographic bounding box.
        lonmax (float):
            The maximum longitude for the geographic bounding box.
        latmin (float):
            The minimum latitude for the geographic bounding box.
        latmax (float):
            The maximum latitude for the geographic bounding box.
        output_dir (str):
            The directory where processed files will be saved.

    Returns:
        None:
            This function does not return a value. Processed files are saved in the specified `output_dir`.

    Example:\n
        >>> infiles = ["/path/to/input1.nc", "/path/to/input2.nc"]
        >>> lonmin = -10.0
        >>> lonmax = 10.0
        >>> latmin = -5.0
        >>> latmax = 5.0
        >>> output_dir = "/path/to/output"
        >>> process_meteo_files(infiles, lonmin, lonmax, latmin, latmax, output_dir)
    """
    for infile in infiles:
        process_ocean_file(infile, lonmin, lonmax, latmin, latmax, output_dir)


def process_wave_files(
    infiles: list[str],
    lonmin: float,
    lonmax: float,
    latmin: float,
    latmax: float,
    output_dir: str,
):
    """
    Processes multiple wave input files and generates outputs for a specified geographic bounding box.

    Args:
        infiles (list[str]):
            A list of input file paths to process.
        lonmin (float):
            The minimum longitude for the geographic bounding box.
        lonmax (float):
            The maximum longitude for the geographic bounding box.
        latmin (float):
            The minimum latitude for the geographic bounding box.
        latmax (float):
            The maximum latitude for the geographic bounding box.
        output_dir (str):
            The directory where processed files will be saved.

    Returns:
        None:
            This function does not return a value. Processed files are saved in the specified `output_dir`.

    Example:\n
        >>> infiles = ["/path/to/input1.nc", "/path/to/input2.nc"]
        >>> lonmin = -10.0
        >>> lonmax = 10.0
        >>> latmin = -5.0
        >>> latmax = 5.0
        >>> output_dir = "/path/to/output"
        >>> process_meteo_files(infiles, lonmin, lonmax, latmin, latmax, output_dir)
    """
    for infile in infiles:
        process_wave_file(infile, lonmin, lonmax, latmin, latmax, output_dir)
