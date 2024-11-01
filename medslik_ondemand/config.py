from enum import Enum
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict


class ModelBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Field(ModelBase):
    name: str
    standard_name: str
    units: str
    long_name: str


input_fields = {
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
        if k not in input_fields:
            raise ValueError(f"fields.key should be one of ({input_fields.keys()})")
        for vk, _ in v.items():
            if vk not in input_fields[k]:
                raise ValueError(
                    f"field.{k}.key should be one of ({input_fields[k].keys()})"
                )


class FieldMap(ModelBase):
    fields: Annotated[
        dict[str, dict[str, DataField]],
        AfterValidator(validate_fields),
    ]


meteo_data_maps = {
    "gfsnc_wgrib2": {
        "pmsl": DataField(name="PRES_surface", mulc=0.01),
        "tair2m": DataField(name="TMP_2maboveground", addc=-273.15),
        "x_wind10": DataField(name="UGRD_10maboveground"),
        "y_wind10": DataField(name="VGRD_10maboveground"),
    },
}


# MeteoMap: Enum = Enum("MeteoMap", list(meteo_data_maps.keys()))
class MeteoMap(str, Enum):
    gfsnc_wgrib2 = "gfsnc_wgrib2"
