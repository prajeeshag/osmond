import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt


def plot_bounding_box(
    lon_min: float, lon_max: float, lat_min: float, lat_max: float
) -> None:
    """
    Plot a bounding box on a map using Matplotlib and Cartopy.

    Parameters:
    lon_min (float): Minimum longitude of the bounding box.
    lat_min (float): Minimum latitude of the bounding box.
    lon_max (float): Maximum longitude of the bounding box.
    lat_max (float): Maximum latitude of the bounding box.
    """
    # Create the figure and the map with PlateCarree projection
    fig, ax = plt.subplots(
        figsize=(10, 8), subplot_kw={"projection": ccrs.PlateCarree()}
    )

    # Add features to the map
    ax.coastlines(resolution="50m", linewidth=1)
    ax.add_feature(cfeature.BORDERS, linestyle=":")
    ax.add_feature(cfeature.LAND, facecolor="lightgray")
    ax.add_feature(cfeature.OCEAN, facecolor="lightblue")

    # Plot the bounding box
    lons = [lon_min, lon_max, lon_max, lon_min, lon_min]
    lats = [lat_min, lat_min, lat_max, lat_max, lat_min]
    ax.plot(
        lons,
        lats,
        color="red",
        linewidth=2,
        transform=ccrs.PlateCarree(),
        label="Bounding Box",
    )

    # Set the extent of the map
    ax.set_extent(
        [lon_min - 5, lon_max + 5, lat_min - 5, lat_max + 5], crs=ccrs.PlateCarree()
    )

    # Add gridlines and labels
    gl = ax.gridlines(draw_labels=True, linestyle="--", color="gray", alpha=0.7)
    gl.top_labels = False
    gl.right_labels = False

    # Add a title and legend
    ax.set_title("Bounding Box Visualization", fontsize=16)
    ax.legend(loc="upper right")

    # Show the plot
    plt.savefig("bounding_box.png")


def to_360(lon):
    return (lon + 360.0) % 360.0


# Example usage
plot_bounding_box(-16.3806, -10.9753, 33.6564, 37.4798)
