from enum import Enum
from pathlib import Path

import cartopy.io.shapereader as shpreader  # type: ignore
import geopandas as gpd  # type: ignore
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from shapely.geometry import Polygon


class CoastLineScale(str, Enum):
    f = "fine"
    h = "high"
    i = "intermediate"
    l = "low"  # noqa: E741
    c = "coarse"


def write_bathy(bathy: xr.DataArray, path: Path, name: str = ""):
    with path.open("w") as f:
        title = " Bathymetry"
        if name:
            title = f"{title} of {name}"
        f.write(f"{title}\n")
        # lon1 lon2 lat1 lat2 in Fortran XX4(xF10.6)
        lon1 = bathy["lon"].values[0]  # type: ignore
        lon2 = bathy["lon"].values[-1]  # type: ignore
        lat1 = bathy["lat"].values[0]  # type: ignore
        lat2 = bathy["lat"].values[-1]  # type: ignore
        f.write(f"    {lon1:.6f}  {lon2:.6f}  {lat1:.6f}  {lat2:.6f}\n")

        # nlon nlat in Fortran XX2(xF10.6)
        nlat = bathy.shape[0]
        nlon = bathy.shape[1]
        f.write(f"    {nlon}  {nlat}\n")

        # invert bathy values and clip to 9000
        bathy_values = -1 * bathy.values  # type: ignore
        bathy_values[bathy_values > 9000] = 9000  # type: ignore
        bathy_values[bathy_values <= 0] = 9999.0  # type: ignore
        bathy_values = np.flip(bathy_values, axis=0)
        np.savetxt(f, bathy_values, fmt="%5.0f", delimiter="")  # type: ignore


def subset_shapefile(  # type: ignore
    shpfilename: str,
    lonmin: float,
    lonmax: float,
    latmin: float,
    latmax: float,
) -> gpd.GeoDataFrame:  # type: ignore
    shp = gpd.read_file(shpfilename)  # type: ignore
    selection_box = Polygon(
        [
            (lonmin, latmin),
            (lonmin, latmax),
            (lonmax, latmax),
            (lonmax, latmin),
            (lonmin, latmin),
        ]
    )
    clipped_shp = gpd.clip(shp, selection_box)  # type: ignore
    return clipped_shp  # type: ignore


def process_coastline_from_bathy(bathy: xr.DataArray, output: Path):
    lon, lat, val = bathy["lon"], bathy["lat"], bathy.values[:, :]  # type: ignore
    val[0, :] = 1.0
    val[-1, :] = 1.0
    val[:, 0] = 1.0
    val[:, -1] = 1.0

    contour = plt.contour(lon, lat, val, levels=[0])  # type: ignore
    plt.axis("off")  # type: ignore

    geometries = []
    for path in contour.get_paths():
        for coordinates in path.to_polygons():
            geometries.append(coordinates)  # type: ignore

    nfeatures = len(geometries)  # type: ignore
    flines = [f"{nfeatures}\n"]
    for geom in geometries:  # type: ignore
        feature_len = len(geom)  # type: ignore
        flines.append(f"{feature_len}  0\n")
        for g in geom:  # type: ignore
            flines.append(f"{g[0]:10.5f} {g[1]:10.5f}\n")

    with output.open("w") as f:
        for line in flines:
            f.write(line)


def process_coastline(
    output: Path,
    coastline_scale: CoastLineScale,
    lonmin: float,
    lonmax: float,
    latmin: float,
    latmax: float,
):
    shpfilename: str = shpreader.gshhs(scale=coastline_scale.name, level=1)  # type: ignore
    subset_shp = subset_shapefile(shpfilename, lonmin, lonmax, latmin, latmax)  # type: ignore
    nfeatures = subset_shp.shape[0]  # type: ignore
    path = output

    flines = [""]
    nfeatures = 0
    for _, row in subset_shp.iterrows():  # type: ignore
        if row.geometry.geom_type == "Polygon":  # type: ignore
            nfeatures += 1
            feature_len = len(row.geometry.exterior.coords)  # type: ignore
            flines.append(f"{feature_len}  0\n")
            for g in row.geometry.exterior.coords:  # type: ignore
                flines.append(f"{g[0]:10.5f} {g[1]:10.5f}\n")
        else:
            for geo in row.geometry.geoms:  # type: ignore
                nfeatures += 1
                feature_len = len(geo.exterior.coords)  # type: ignore
                flines.append(f"{feature_len}  0\n")
                for g in geo.exterior.coords:  # type: ignore
                    flines.append(f"{g[0]:10.5f} {g[1]:10.5f}\n")

    flines[0] = f"{nfeatures}\n"
    with path.open("w") as f:
        for line in flines:
            f.write(line)


def create_domain(
    bathymetry: str,
    lonmin: float,
    lonmax: float,
    latmin: float,
    latmax: float,
    output: str = "./output",
    coastline_scale: CoastLineScale = CoastLineScale.f,
) -> tuple[Path, Path]:
    """
    Creates a Medslik bathymetry and coastline file from a GEBCO netCDF file and GSHHS shapefile.

    Args:
        bathymetry (str):
            Path to the GEBCO netCDF bathymetry file.
        lonmin (float):
            Minimum longitude of the domain.
        lonmax (float):
            Maximum longitude of the domain.
        latmin (float):
            Minimum latitude of the domain.
        latmax (float):
            Maximum latitude of the domain.
        output (str, optional):
            Path for the output files
        coastline_scale (CoastLineScale, optional):
            GSHHS coastline resolution. Options are:\n\n
            - `f` (fine)
            - `h` (high)
            - `i` (intermediate)
            - `l` (low)
            - `c` (coarse)

    Returns:
            A tuple containing the path to the generated Medslik bathymetry file (`<output>.bath`) and coastline file (`<output>.map`).

    Example:\n
        >>> bathymetry = "/path/to/GEBCO_bathymetry.nc"
        >>> lonmin = -10.0
        >>> lonmax = 10.0
        >>> latmin = -5.0
        >>> latmax = 5.0
        >>> output = "./workdir/domain_output"
        >>> coastline_scale = CoastLineScale.h
        >>> create_domain(bathymetry, lonmin, lonmax, latmin, latmax, output, coastline_scale)

    """
    bathy = xr.open_dataset(bathymetry, chunks={})["elevation"]  # type: ignore
    bds = bathy.loc[latmin:latmax, lonmin:lonmax]  # type: ignore
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_bathy = output_path.with_suffix(".bath")
    output_map = output_path.with_suffix(".map")
    write_bathy(bds, output_bathy)  # type: ignore
    process_coastline_from_bathy(bds, output_map)  # type: ignore
    # process_coastline(output_map, coastline_scale, lonmin, lonmax, latmin, latmax)
    return output_bathy, output_map
