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
import git

SCRIPTS_DIR: Path = Path(__file__).parent

# Binaries
binary_extensions = [
    ".exe",  # Executable file (Windows)
    ".bin",  # Binary file
    ".dll",  # Dynamic Link Library (Windows)
    ".so",  # Shared Object Library (Linux)
    ".o",  # Compiled Object File
    ".a",  # Static Library Archive (Unix)
    ".pyc",  # Compiled Python Bytecode
    ".pyo",  # Optimized Python Bytecode
    ".iso",  # Disk Image
    ".img",  # Disk Image File
    ".dmg",  # Apple Disk Image
    ".elf",  # Executable and Linkable Format (Linux)
    ".class",  # Compiled Java Bytecode
    ".msi",  # Microsoft Installer Package
    ".jar",  # Java Archive
    ".deb",  # Debian Package File
    ".rpm",  # Red Hat Package Manager File
    ".apk",  # Android Package File
]

# Images
image_extensions = [
    ".bmp",  # Bitmap Image File
    ".dib",  # Device-Independent Bitmap
    ".jpg",  # Joint Photographic Experts Group
    ".jpeg",  # Joint Photographic Experts Group
    ".jfif",  # JPEG File Interchange Format
    ".jp2",  # JPEG 2000
    ".png",  # Portable Network Graphics
    ".svg",  # Scalable Vector Graphics
    ".gif",  # Graphics Interchange Format
    ".tiff",  # Tagged Image File Format
    ".webp",  # WebP Image
    ".ico",  # Icon Image
    ".psd",  # Adobe Photoshop Document
    ".heic",  # High Efficiency Image Format
    ".heif",  # High Efficiency Image Format
    ".raw",  # Raw Image File
    ".cr2",  # Canon Raw Image File
    ".nef",  # Nikon Raw Image File
    ".arw",  # Sony Alpha Raw Image File
    ".dds",  # DirectDraw Surface
]

# Videos
video_extensions = [
    ".mp4",  # MPEG-4 Video File
    ".mkv",  # Matroska Video File
    ".avi",  # Audio Video Interleave
    ".mov",  # Apple QuickTime Movie
    ".wmv",  # Windows Media Video
    ".flv",  # Flash Video
    ".webm",  # WebM Video
    ".m4v",  # MPEG-4 Video
    ".mpg",  # MPEG Video
    ".mpeg",  # MPEG Video
    ".ts",  # Transport Stream
    ".3gp",  # 3GPP Multimedia File
    ".mxf",  # Material Exchange Format
    ".rm",  # RealMedia File
    ".ogv",  # Ogg Video File
    ".vob",  # Video Object File (DVD)
    ".dv",  # Digital Video File
    ".f4v",  # Flash MP4 Video
    ".asf",  # Advanced Systems Format
]

# Audio
audio_extensions = [
    ".mp3",  # MPEG Audio Layer III
    ".wav",  # Waveform Audio File
    ".flac",  # Free Lossless Audio Codec
    ".aac",  # Advanced Audio Coding
    ".ogg",  # Ogg Vorbis Audio
    ".wma",  # Windows Media Audio
    ".m4a",  # MPEG-4 Audio
    ".alac",  # Apple Lossless Audio Codec
    ".aiff",  # Audio Interchange File Format
    ".pcm",  # Pulse Code Modulation
    ".amr",  # Adaptive Multi-Rate Audio
    ".opus",  # Opus Audio Codec
]

# Archives & Compressed Files
archive_extensions = [
    ".zip",  # ZIP Archive
    ".rar",  # RAR Archive
    ".7z",  # 7-Zip Archive
    ".tar",  # Tarball Archive
    ".gz",  # Gzip Compressed File
    ".bz2",  # Bzip2 Compressed File
    ".xz",  # XZ Compressed File
    ".lz",  # Lzip Compressed File
    ".iso",  # ISO Disk Image (also binary)
    ".tgz",  # Gzipped Tar Archive
]

# Fonts
font_extensions = [
    ".ttf",  # TrueType Font
    ".otf",  # OpenType Font
    ".woff",  # Web Open Font Format
    ".woff2",  # Web Open Font Format 2
    ".eot",  # Embedded OpenType Font
    ".pfb",  # Printer Font Binary
    ".pfa",  # Printer Font ASCII
]

# Documents (Non-Plain Text)
document_extensions = [
    ".pdf",  # Portable Document Format
    ".doc",  # Microsoft Word Document
    ".docx",  # Microsoft Word Open XML Document
    ".xls",  # Microsoft Excel Spreadsheet
    ".xlsx",  # Microsoft Excel Open XML Spreadsheet
    ".ppt",  # Microsoft PowerPoint Presentation
    ".pptx",  # Microsoft PowerPoint Open XML Presentation
    ".odt",  # OpenDocument Text
    ".ods",  # OpenDocument Spreadsheet
    ".odp",  # OpenDocument Presentation
    ".rtf",  # Rich Text Format
]

# 3D Models and CAD Files
model_extensions = [
    ".obj",  # Wavefront OBJ File
    ".stl",  # Stereolithography File
    ".fbx",  # Autodesk FBX File
    ".dae",  # Digital Asset Exchange
    ".glb",  # GL Transmission Format Binary
    ".gltf",  # GL Transmission Format
    ".3ds",  # 3D Studio File
    ".dwg",  # AutoCAD Drawing Database File
    ".dxf",  # Drawing Exchange Format File
]

# Others (Non-Text)
misc_extensions = [
    ".dat",  # Generic Data File
    ".db",  # Database File
    ".bak",  # Backup File
    ".log",  # Log File (Can be text-based or binary)
    ".msg",  # Outlook Mail Message
    ".torrent",  # BitTorrent File
]

all_extensions = binary_extensions + image_extensions + video_extensions + audio_extensions + archive_extensions + font_extensions + document_extensions + model_extensions + misc_extensions

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


__version__ = "1.2.5"


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
            repo = None
            try:
                repo = git.Repo(dir_path, search_parent_directories=True)
            except git.InvalidGitRepositoryError:
                logging.warning("Directory %r is not a git repository.", dir_path)
                continue

            for file_glob in glob:
                logging.debug("Walking %r", (dir_path / file_glob).as_posix())

                for file_path in dir_path.rglob(file_glob):
                    if is_excluded(
                        repo,
                        license_,
                        file_path,
                        eval_exclude(exclude, directory=dir_path),
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


def is_excluded(
    repo: Optional[git.Repo], license_: Path, file_path: Path, exclude: list[str]
) -> bool:
    """Check if path matches any exclude glob."""

    if repo is not None and len(repo.ignored(file_path.as_posix())) > 0:
        return True

    for exclude_glob in exclude:
        if re.match(exclude_glob, file_path.as_posix()) is not None:
            return True

    # exclude .git
    if ".git" in file_path.parts:
        return True

    if file_path == license_:
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
        # if file is binary or image or video, skip it
        if file_path.suffix in all_extensions:
            return 0
        return _handle_file(file_path, note)
    except IsADirectoryError:
        return 0
    except Exception as exc:
        logging.exception(exc)
        raise


def _handle_file(file_path: Path, note: str) -> int:
    note_size = len(note)
    logging.debug(f"Note: {note}")
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
