from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import NamedTuple, Self, TypeAlias

import yaml
from pydantic import BaseModel, ConfigDict, model_validator


class ModelBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FieldAttr(NamedTuple):
    standard_name: str
    long_name: str
    units: str


DataSetType: TypeAlias = MappingProxyType[str, MappingProxyType[str, FieldAttr]]

coords_common = {
    "latitude": FieldAttr(
        standard_name="latitude",
        long_name="Latitude",
        units="degrees north",
    ),
    "longitude": FieldAttr(
        standard_name="longitude",
        long_name="Longitude",
        units="degrees east",
    ),
    "time": FieldAttr(
        standard_name="time",
        long_name="Time",
        units="hours since",
    ),
}

meteo_dataset = MappingProxyType(
    {
        "coords": MappingProxyType(coords_common),
        "data_vars": MappingProxyType(
            {
                "pmsl": FieldAttr(
                    standard_name="air_pressure_at_sea_level",
                    long_name="Air Pressure at Sea Level",
                    units="hPa",
                ),
                "tair2m": FieldAttr(
                    standard_name="air_temperature",
                    long_name="Air Temperature at 2 meters height above Sea Level",
                    units="degrees C",
                ),
                "x_wind10": FieldAttr(
                    standard_name="x_wind",
                    long_name="Wind Speed along East-West Direction at 10 meters above Sea Level",
                    units="m s-1",
                ),
                "y_wind10": FieldAttr(
                    standard_name="y_wind",
                    long_name="Wind Speed along North-South Direction at 10 meters above Sea Level",
                    units="m s-1",
                ),
            }
        ),
    }
)

ocean_dataset = MappingProxyType(
    {
        "coords": MappingProxyType(
            {**coords_common, "depth": FieldAttr("depth", "Depth", "m")}
        ),
        "data_vars": MappingProxyType(
            {
                "uvel": FieldAttr(
                    standard_name="sea_water_x_velocity",
                    long_name="Velocity Zonal Component",
                    units="m s-1",
                ),
                "vvel": FieldAttr(
                    standard_name="sea_water_y_velocity",
                    long_name="Velocity Meridional Component",
                    units="m s-1",
                ),
                "potemp": FieldAttr(
                    standard_name="sea_water_potential_temperature",
                    long_name="Potential Temperature",
                    units="degrees C",
                ),
            }
        ),
    }
)


class DataVarMap(ModelBase):
    name: str
    addc: float = 0.0
    mulc: float = 1.0


class DepthMapping(Enum):
    copy = "copy"
    select = "select"


class DepthMaping(ModelBase):
    mapping: DepthMapping = DepthMapping.copy
    input_indices: list[int] = [1]
    input_levels: list[float]
    output_levels: list[float] = [1, 2, 4, 6]


class DataSetMap(BaseModel):
    data_vars: dict[str, DataVarMap]
    coords: dict[str, DataVarMap]
    depth_mapping: DepthMaping | None = None


class DataSetMaper(BaseModel):
    meteo: dict[str, DataSetMap] = {}
    ocean: dict[str, DataSetMap] = {}

    @model_validator(mode="after")
    def check_coords_and_data_vars(self) -> Self:
        for dsname, dsmap in self.meteo.items():
            if dsmap.coords.keys() != meteo_dataset["coords"].keys():
                raise ValueError(f"Coordinates does not match for dataset {dsname}")
            if dsmap.data_vars.keys() != meteo_dataset["data_vars"].keys():
                raise ValueError(f"Data variables does not match for dataset {dsname}")
        for dsname, dsmap in self.ocean.items():
            if dsmap.coords.keys() != ocean_dataset["coords"].keys():
                raise ValueError(f"Coordinates does not match for dataset {dsname}")
            if dsmap.data_vars.keys() != ocean_dataset["data_vars"].keys():
                raise ValueError(f"Data variables does not match for dataset {dsname}")
        return self


def load_dataset_maper() -> DataSetMaper:
    default_config_yml = Path(__file__).parent / "config.yml"  # type: ignore
    with default_config_yml.open("r") as f:
        config = yaml.safe_load(f)
    data_set_map = DataSetMaper(**config)
    return data_set_map


data_maper = load_dataset_maper()

MeteoMap = Enum("MeteoMap", {key: key for key in data_maper.meteo.keys()})
OceanMap = Enum("OceanMap", {key: key for key in data_maper.ocean.keys()})
