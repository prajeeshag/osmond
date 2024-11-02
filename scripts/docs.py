import logging
import re
from pathlib import Path

import typer

logging.basicConfig(level=logging.INFO)

app = typer.Typer()

en_docs_path = Path("")
mkdocs_name = "mkdocs.yml"


def generate_readme_content() -> str:
    en_index = en_docs_path / "docs" / "index.md"
    content = en_index.read_text("utf-8")
    match_pre = re.search(r"</style>\n\n", content)
    if not match_pre:
        raise RuntimeError("Couldn't find pre section (<style>) in index.md")
    frontmatter_end = match_pre.end()
    new_content = content[frontmatter_end:]
    # Remove content between <!-- only-mkdocs --> and <!-- /only-mkdocs -->
    new_content = re.sub(
        r"<!--only-mkdocs-->.*?<!--/only-mkdocs-->",
        "",
        new_content,
        flags=re.DOTALL,
    )
    return new_content


@app.command()
def generate_readme() -> None:
    """
    Generate README.md content from main index.md
    """
    typer.echo("Generating README")
    readme_path = Path("README.md")
    new_content = generate_readme_content()
    readme_path.write_text(new_content, encoding="utf-8")


@app.command()
def verify_readme() -> None:
    """
    Verify README.md content from main index.md
    """
    typer.echo("Verifying README")
    readme_path = Path("README.md")
    generated_content = generate_readme_content()
    readme_content = readme_path.read_text("utf-8")
    if generated_content != readme_content:
        typer.secho(
            "README.md outdated from the latest index.md",
            color=typer.colors.RED,  # type: ignore
        )
        raise typer.Abort()
    typer.echo("Valid README ✅")


if __name__ == "__main__":
    app()
