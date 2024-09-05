#!/usr/bin/python3
# Copyright 2023 Krzysztof Wiśniewski <argmaster.world@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the “Software”), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be included in all copies
# or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


"""Script for fixing missing copyright notices in project files."""

from __future__ import annotations

import logging
import operator
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from functools import lru_cache, reduce
from itertools import repeat
from pathlib import Path
from typing import Iterable, Optional

SCRIPTS_DIR: Path = Path(__file__).parent


try:
    import click
    import jellyfish
    import jinja2
    import tomlkit

except ImportError as __exc:
    print(
        f"Dependencies are missing ({__exc}), make sure you are running in virtual "
        + "environment!"
    )
    raise SystemExit(1) from __exc


__version__ = "1.1.0"


@click.command()
@click.option(
    "-v",
    "--verbose",
    count=True,
    help=(
        "Changes verbosity, when not used, verbosity is  warning, with every `v` "
        + "verbosity goes utp, `-vv` means debug."
    ),
)
@click.option("-s", "--comment-symbol", help="Symbol used to indicate comment.")
@click.option(
    "-d", "--directory", help="Path to directory to search.", type=Path, multiple=True
)
@click.option(
    "-g", "--glob", help="File glob used to search directories.", multiple=True
)
@click.option(
    "-e",
    "--exclude",
    help="Regex used to exclude files from updates.",
    multiple=True,
)
@click.option(
    "-l",
    "--license",
    "license_",
    type=Path,
    help="Path to license template.",
)
@click.option(
    "-p",
    "--pool",
    help="Size of thread pool used for file IO.",
    default=4,
    type=int,
)
def main(  # pylint: disable=too-many-arguments
    verbose: int,
    comment_symbol: str,
    directory: list[Path],
    glob: list[str],
    exclude: list[str],
    license_: Path,
    pool: int,
) -> int:  # pylint: enable=too-many-arguments
    """Add Copyright notices to all files selected by given glob in specified
    directories.

    Use -d/--directory and -g/--glob multiple times to specify more directories and
    globs to use at once.
    """
    configure_logging(verbose)
    raise SystemExit(run(comment_symbol, directory, glob, exclude, license_, pool))


def run(  # pylint: disable=too-many-arguments
    comment_symbol: str,
    directory: list[Path],
    glob: list[str],
    exclude: list[str],
    license_: Path,
    pool: int,
) -> int:  # pylint: enable=too-many-arguments
    """Run autocopyright from script."""

    license_ = license_.expanduser().resolve(strict=True)

    note = render_note(comment_symbol, license_)
    logging.debug("Rendered copyright note, %r characters.", len(note))

    for ex in exclude:
        logging.debug("Using exclude pattern: %r", ex)

    def _() -> Iterable[Path]:
        for dir_path in directory:
            dir_path = dir_path.resolve()

            for file_glob in glob:
                logging.debug("Walking %r", (dir_path / file_glob).as_posix())

                for file_path in dir_path.rglob(file_glob):
                    if is_excluded(
                        file_path, eval_exclude(exclude, directory=dir_path)
                    ):
                        logging.info("Excluded %r", file_path.as_posix())
                        continue

                    yield file_path

    if pool > 1:
        with ThreadPoolExecutor(max_workers=pool) as executor:
            return_values = executor.map(handle_file, _(), repeat(note))
    else:
        return_values = map(handle_file, _(), repeat(note))

    had_changes = reduce(operator.or_, return_values, 0)
    return had_changes


def eval_exclude(exclude: list[str], directory: Path) -> list[str]:
    """Evaluate special variables in exclude globs."""

    def _() -> Iterable[str]:
        cwd = Path.cwd().as_posix()
        directory_str = directory.as_posix()

        for path in exclude:
            yield path.format(cwd=cwd, directory=directory_str)

    return list(_())


def is_excluded(file_path: Path, exclude: list[str]) -> bool:
    """Check if path matches any exclude glob."""

    for exclude_glob in exclude:
        if re.match(exclude_glob, file_path.as_posix()) is not None:
            return True

    return False


def configure_logging(verbose: int) -> None:
    """Configure default logger."""
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    if verbose == 0:
        root_logger.setLevel(logging.WARNING)
    elif verbose == 1:
        root_logger.setLevel(logging.INFO)
    else:
        root_logger.setLevel(logging.DEBUG)

    normal_stream_handler: logging.Handler = logging.StreamHandler(stream=sys.stderr)

    normal_stream_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s [%(levelname)-5.5s] %(message)s",
            datefmt="%y.%m.%d %H:%M:%S",
        )
    )

    root_logger.addHandler(normal_stream_handler)
    logging.debug("Configured logger with level %r", verbose)


def render_note(comment_symbol: str, license_: Path) -> str:
    """Render license note from template `LICENSE_NOTE.md.jinja2`."""
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(license_.parent.as_posix()),
        autoescape=jinja2.select_autoescape(),
    )
    template = env.get_template(license_.name)
    logging.debug("Loaded template object %r", license_)

    render = template.render(
        now=datetime.now(),
        pyproject=pyproject(),
    )

    def _() -> Iterable[str]:
        for line in render.split("\n"):
            yield f"{comment_symbol} {line}".strip()

    render = str.join("\n", _())
    logging.debug("Rendered template object %r", license_)
    return render


@lru_cache(1)
def pyproject() -> tomlkit.TOMLDocument:
    """Load `pyproject.toml` file content from current working directory."""
    pyproject_path = Path.cwd() / "pyproject.toml"
    try:
        text_content = pyproject_path.read_text(encoding="utf-8")
        content = tomlkit.loads(text_content)
        logging.debug(
            "Loaded %r chars from %r.", len(text_content), pyproject_path.as_posix()
        )
    except FileNotFoundError as exc:
        logging.debug("Error reading pyproject.toml: %r", exc)
        content = None

    return content


def handle_file(file_path: Path, note: str) -> int:
    """Check if file needs copyright update and apply it."""
    try:
        return _handle_file(file_path, note)

    except Exception as exc:
        logging.exception(exc)
        raise


def _handle_file(file_path: Path, note: str) -> int:
    note_size = len(note)
    content = file_path.read_text(encoding="utf-8")
    logging.debug("Inspecting file %r", file_path.as_posix())

    shebang: Optional[str]
    if content.startswith("#!"):
        # Remove shebang line from content and store it.
        shebang, *rest = content.split("\n")
        content = str.join("\n", rest)
    else:
        shebang = None

    file_beginning = content[:note_size]
    distance = jellyfish.levenshtein_distance(note, file_beginning)
    ratio = 1.0 - (distance / note_size)

    logging.debug("Ratio %r for %r", ratio, file_path.as_posix())

    if ratio > 0.8:
        # License was found, mostly matching, maybe author has changed or sth.
        return 0

    if shebang is None:
        new_file_content = f"{note}\n\n\n{content}"
    else:
        new_file_content = f"{shebang}\n{note}\n\n\n{content}"

    tempfile = file_path.with_suffix(".temp")
    tempfile.write_text(new_file_content, encoding="utf-8")
    os.replace(tempfile, file_path)
    logging.warning("Updated %r", file_path.as_posix())

    return 1
