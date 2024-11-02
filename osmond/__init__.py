import typer

from .domain import app as domain_app
from .forcing import app as forcing_app

app = typer.Typer()

app.add_typer(domain_app, name="domain")
app.add_typer(forcing_app, name="forcing")

click_app = typer.main.get_command(app)
