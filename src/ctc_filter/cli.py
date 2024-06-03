import os
import shutil
from pathlib import Path

import dotenv
import typer
from typer import Typer
from typing_extensions import Annotated

from ctc_filter.config import _Settings, settings
from ctc_filter.executor import Executor

app = Typer()


@app.command()
def run(
    config_dir: Annotated[str, typer.Argument(..., help="Config file path")],
):
    """Run ctc filter"""
    cfg_dir = Path(config_dir)
    env_path = cfg_dir.joinpath(".env")

    if not env_path.exists():
        typer.echo(f"Config file not found: {env_path}")
        raise typer.Exit(code=1)

    dotenv.load_dotenv(cfg_dir.joinpath(".env"))

    try:
        os.environ["USER_DATA_DIR"] = cfg_dir.resolve().as_posix()
        settings.load(_Settings())  # type: ignore
    except Exception as e:
        typer.echo(f"Error loading config: {e}")
        raise typer.Exit(code=1)

    Executor(exchange=settings.exchange).run()


@app.command(
    "config",
    help="Generate user config",
    short_help="Generate user config",
    no_args_is_help=True,
)
def config(
    output_path: Annotated[str, typer.Argument(..., help="Output file path")],
):
    """Generate user config"""
    p = Path(__file__).parent.joinpath("user_data")
    # 赋值 user_data 到 output
    shutil.copytree(p, Path(output_path).joinpath("user_data"))


@app.command(
    "download",
    help="Download data",
    short_help="Download data",
    no_args_is_help=True,
)
def download():
    ...

