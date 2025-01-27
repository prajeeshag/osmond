# type: ignore
from pathlib import Path
from typing import Annotated

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import typer

app = typer.Typer()


@app.command("plot")
def plot_domain(
    inpfile: Annotated[
        Path, typer.Option(help="Path to domain file without extension")
    ],
    output: Annotated[Path, typer.Option(help="Output path for plot")],
):
    """Plot Medslik domain"""
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
        # ax.set_xlim(32, 50.5)
        # ax.set_ylim(10, 30)
        plt.axis("off")
        plt.savefig(output, dpi=300)  # type: ignore


app()
