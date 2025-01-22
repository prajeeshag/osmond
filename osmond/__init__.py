import typer

from .domain import app as domain_app
from .domain import create_domain
from .forcing import app as forcing_app
from .forcing import subset_forcing, subset_forcings

__all__ = [
    "subset_forcing",
    "subset_forcings",
    "create_domain",
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
