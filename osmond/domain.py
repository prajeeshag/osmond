from enum import Enum
from pathlib import Path
from typing import Annotated

import cartopy.io.shapereader as shpreader  # type: ignore
import geopandas as gpd  # type: ignore
import numpy as np
import typer
import xarray as xr
from shapely.geometry import Polygon

app = typer.Typer(add_completion=False)


class CoastLineScale(str, Enum):
    f = "fine"
    h = "high"
    i = "intermediate"
    l = "low"  # noqa: E741
    c = "coarse"


def write_bathy(bathy: xr.DataArray, path: Path, name: str = ""):
    with path.open("w") as f:
        title = "Bathymetry"
        if name:
            title = f"{title} of {name}"
        f.write(f"{title}\n")
        # lon1 lon2 lat1 lat2 in Fortran XX4(xF10.6)
        lon1 = bathy["lon"].values[0]  # type: ignore
        lon2 = bathy["lon"].values[-1]  # type: ignore
        lat1 = bathy["lat"].values[0]  # type: ignore
        lat2 = bathy["lat"].values[-1]  # type: ignore
        f.write(f"   {lon1:10.6f} {lon2:10.6f} {lat1:10.6f} {lat2:10.6f}\n")

        # nlon nlat in Fortran XX2(xF10.6)
        nlat = bathy.shape[0]
        nlon = bathy.shape[1]
        f.write(f"  {nlon} {nlat}\n")

        # invert bathy values and clip to 9000
        bathy_values = -1 * bathy.values  # type: ignore
        bathy_values[bathy_values > 9000] = 9000  # type: ignore
        bathy_values[bathy_values <= 0] = 9999.0  # type: ignore
        bathy_values = np.flip(bathy_values, axis=0)
        np.savetxt(f, bathy_values, fmt="%04.0f")  # type: ignore


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


@app.command("create")
def make_domain(
    bathymetry: Annotated[
        Path, typer.Option(help="Path to GEBCO netcdf bathymetry file")
    ],
    lonlatbox: Annotated[str, typer.Option(help="<lonmin>,<lonmax>,<latmin>,<latmax>")],
    coastline_scale: Annotated[
        CoastLineScale, typer.Option(help="GSHHS coastline resolution")
    ] = CoastLineScale.f,
    output: Annotated[Path, typer.Option(help="Output path")] = Path("./output"),
):
    """
    Creates a Medslik bathymetry `<output>.bath` file from a GEBCO netcdf file
    and coastline file `<output>.map` from a GSHHS shapefile.
    """
    lonmin, lonmax, latmin, latmax = map(float, lonlatbox.split(","))
    bathy = xr.open_dataset(bathymetry, chunks={})["elevation"]  # type: ignore
    bds = bathy.loc[latmin:latmax, lonmin:lonmax]  # type: ignore
    output_bathy = output.with_suffix(".bath")
    write_bathy(bds, output_bathy)  # type: ignore
    process_coastline(output, coastline_scale, lonmin, lonmax, latmin, latmax)


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
    path = output.with_suffix(".map")

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


@app.command("plot")
def plot_domain(
    inpfile: Annotated[
        Path, typer.Option(help="Path to domain file without extension")
    ],
    output: Annotated[Path, typer.Option(help="Output path for plot")],
):
    """Plot Medslik domain"""
    import matplotlib.patches as patches
    import matplotlib.pyplot as plt

    bathyfile = inpfile.with_suffix(".bath")
    mapfile = inpfile.with_suffix(".map")
    fig, ax = plt.subplots()  # type: ignore

    with bathyfile.open("r") as f:
        line = f.readline()
        line = f.readline()
        lonmin, lonmax, latmin, latmax = map(float, line.split())
        line = f.readline()
        nlon, nlat = map(int, line.split())
        lon = np.linspace(lonmin, lonmax, nlon)
        lat = np.linspace(latmin, latmax, nlat)
        bathy: list[list[int]] = []
        for _ in range(nlat):
            line = f.readline()
            bathy.append(list(map(int, line.split())))
        bathy_array = np.array(list(reversed(bathy)))
        bathy_array = np.where(bathy_array == 9999, np.nan, bathy_array)
        print(lon.shape, lat.shape, bathy_array.shape)
        cs = ax.pcolormesh(lon, lat, bathy_array)  # type: ignore
        fig.colorbar(cs, ax=ax)  # type: ignore

    with mapfile.open("r") as f:
        f.readline()
        line = f.readline()
        nfeatures = 0
        while line != "":
            npoints, _ = map(int, line.split())
            # if mask == 1:
            nfeatures += 1
            coords: list[tuple[float, float]] = []
            for _ in range(npoints):
                line = f.readline()
                coord = tuple(map(float, line.split()))  # type: ignore
                # print(coord, line)
                if coord:
                    coords.append(coord)  # type: ignore
                else:
                    break
            coords.append(coords[0])
            polygon = patches.Polygon(
                coords, closed=True, edgecolor="orange", facecolor="none"
            )
            ax.add_patch(polygon)
            line = f.readline()
        ax.set_xlim(32, 50.5)
        ax.set_ylim(10, 30)
        plt.savefig(output, dpi=300)  # type: ignore


click_app = typer.main.get_command(app)
