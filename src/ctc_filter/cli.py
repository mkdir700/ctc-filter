import shutil
from pathlib import Path

import typer
from typer import Typer
from typing_extensions import Annotated

app = Typer()


@app.command()
def run(
    config_dir: Annotated[str, typer.Argument(..., help="Config file path")],
):
    """Run ctc filter"""
    cfg_dir = Path(config_dir)
    user_data_dir = cfg_dir.joinpath("user_data")


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
