import typer

from .domain import app as domain_app
from .domain import create_domain
from .forcing import app as forcing_app
from .forcing import process_meteo_files, process_ocean_files, process_wave_files

__all__ = [
    "create_domain",
    "process_meteo_files",
    "process_ocean_files",
    "process_wave_files",
]

app = typer.Typer(add_completion=False)

app.add_typer(
    domain_app,
    name="domain",
    help="Medslik Domain utility",
    # add_help_option=False,
)
app.add_typer(forcing_app, name="forcing", help="Medslik Input Creation")

click_app = typer.main.get_command(app)
