from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class ModelBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Field(ModelBase):
    name: str
    standard_name: str
    units: str
    long_name: str


input_fields_param = {
    "meteo": {
        "pmsl": Field(
            name="pmsl",
            standard_name="air_pressure_at_sea_level",
            long_name="Air Pressure at Sea Level",
            units="hPa",
        ),
        "tair2m": Field(
            name="tair2m",
            standard_name="air_temperature",
            long_name="Air Temperature at 2 meters height above Sea Level",
            units="degrees C",
        ),
        "x_wind10": Field(
            name="x_wind10",
            standard_name="x_wind",
            long_name="Wind Speed along East-West Direction at 10 meters above Sea Level",
            units="m s-1",
        ),
        "y_wind10": Field(
            name="y_wind10",
            standard_name="y_wind",
            long_name="Wind Speed along North-South Direction at 10 meters above Sea Level",
            units="m s-1",
        ),
    },
    "ocean": {
        "uvel": Field(
            name="uvel",
            standard_name="sea_water_x_velocity",
            long_name="Velocity Zonal Component",
            units="m s-1",
        ),
        "vvel": Field(
            name="vvel",
            standard_name="sea_water_y_velocity",
            long_name="Velocity Meridional Component",
            units="m s-1",
        ),
        "wvel": Field(
            name="wvel",
            standard_name="sea_water_z_velocity",
            long_name="Velocity Vertical Component",
            units="m s-1",
        ),
        "potemp": Field(
            name="potemp",
            standard_name="sea_water_potential_temperature",
            long_name="Potential Temperature",
            units="degrees C",
        ),
        "psal": Field(
            name="psal",
            standard_name="sea_water_salinity",
            long_name="Practical Salinity",
            units="psu",
        ),
    },
    "wave": {
        "wsh": Field(
            name="wsh",
            standard_name="sea_surface_wave_significant_height",
            long_name="Sea Surface Wave Significant Height",
            units="m",
        ),
        "wdir": Field(
            name="wdir",
            standard_name="sea_surface_wave_to_direction",
            long_name="Sea Surface Wave Direction",
            units="degrees",
        ),
        "wper": Field(
            name="wper",
            standard_name="sea_surface_wave_zero_upcrossing_period",
            long_name="Mean Wave Period",
            units="s",
        ),
    },
}


class DataField(ModelBase):
    name: str
    addc: float = 0.0
    mulc: float = 1.0


def validate_fields(fields: dict[str, dict[str, DataField]]):
    """
    validate if fields key in input_fields
    """
    for k, v in fields.items():
        if k not in input_fields_param:
            raise ValueError(
                f"fields.key should be one of ({input_fields_param.keys()})"
            )
        for vk, _ in v.items():
            if vk not in input_fields_param[k]:
                raise ValueError(
                    f"field.{k}.key should be one of ({input_fields_param[k].keys()})"
                )


class DataSetMaper(BaseModel):
    meteo: dict[str, dict[str, DataField]] = {}
    ocean: dict[str, dict[str, DataField]] = {}
    waves: dict[str, dict[str, DataField]] = {}


def load_dataset_maper() -> DataSetMaper:
    import yaml

    default_config_yml = Path(__file__).parent / "config.yml"  # type: ignore
    with default_config_yml.open("r") as f:
        config = yaml.safe_load(f)
    data_set_map = DataSetMaper(**config)
    return data_set_map


data_maper = load_dataset_maper()


MeteoMap = Enum("MeteoMap", {key: key for key in data_maper.meteo.keys()})
OceanMap = Enum("OceanMap", {key: key for key in data_maper.ocean.keys()})
