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

"""This module contains acceptance tests for autocopyright.

Those test are conducted to determine if the requirements of a use purpose are met
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable, ClassVar

import pytest

import autocopyright


class TestAcceptance:
    PYPROJECT_CONTENT: ClassVar[
        str
    ] = """[tool.poetry]
name="example"
authors=["EXAMPLE_AUTHOR <examle.email@email.com>"]

"""

    TEMPLATE_CONTENT: ClassVar[
        str
    ] = """Copyright {{ now.year }} {{ pyproject.tool.poetry.authors[0] }}

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the “Software”), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be included in all copies
or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

    RENDERED_TEMPLATE: ClassVar[
        str
    ] = """# Copyright {year} EXAMPLE_AUTHOR <examle.email@email.com>
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


"""

    def setup_method(self) -> None:
        """setup any state tied to the execution of the given method in a class.

        setup_method is invoked for every test method of a class.
        """
        self.primary_cwd = Path.cwd().resolve().as_posix()

        self.tmp_dir = TemporaryDirectory()  # pylint: disable=consider-using-with

        self.work_dir = Path(self.tmp_dir.name).resolve()
        os.chdir(self.work_dir)

        self.create_test_dir()
        self.create_assets()
        self.create_comparison_asset()

    def create_test_dir(self) -> None:
        """Create test directory files.

        ```
        test_dir/
            __init__.py
            log.py
            logging/
                __init__.py
                log.py
        ```
        """
        self.test_dir = self.work_dir / "test_dir"
        self.test_dir.mkdir()

        self.test_dir__init__ = self.work_dir / "test_dir" / "__init__.py"
        self.test_dir__init__.touch()

        self.test_dir_log = self.work_dir / "test_dir" / "log.py"
        self.test_dir_log.touch()

        self.test_dir_logging = self.work_dir / "test_dir" / "logging"
        self.test_dir_logging.mkdir()

        self.test_dir_logging__init__ = (
            self.work_dir / "test_dir" / "logging" / "__init__.py"
        )
        self.test_dir_logging__init__.touch()

        self.test_dir_logging_log = self.work_dir / "test_dir" / "logging" / "log.py"
        self.test_dir_logging_log.touch()

    def create_assets(self) -> None:
        """Create template file in root of work_dir called `license.md.jinja2`"""
        (self.work_dir / "license.md.jinja2").write_text(self.TEMPLATE_CONTENT, "utf-8")
        (self.work_dir / "pyproject.toml").write_text(self.PYPROJECT_CONTENT, "utf-8")

    def create_comparison_asset(self) -> None:
        """Create comparison rendered template content."""
        self.rendered_template = self.RENDERED_TEMPLATE.format(year=datetime.now().year)

    def teardown_method(self) -> None:
        """teardown any state that was previously setup with a setup_method call."""
        os.chdir(self.primary_cwd)
        self.tmp_dir.cleanup()

    @pytest.mark.parametrize("pool_size", [1, 4, 8])
    def test_run_add_to_all_files(self, pool_size: int) -> None:
        """Purpose of test is to check if autocopyright will add copyright to all files
        in test_dir."""
        autocopyright.run(
            comment_symbol="#",
            directory=[Path("test_dir")],
            glob=["*.py"],
            exclude=[],
            license_=Path("license.md.jinja2"),
            pool=pool_size,
        )

        self.check_content(
            __init__=self.check_rendered,
            log=self.check_rendered,
            logging__init__=self.check_rendered,
            logging_log=self.check_rendered,
        )
        self.check_files_list()

    def check_content(
        self,
        *,
        __init__: Callable[[str], bool],
        log: Callable[[str], bool],
        logging__init__: Callable[[str], bool],
        logging_log: Callable[[str], bool],
    ) -> None:
        """Check length of content of files in test dir."""

        assert __init__(self.test_dir__init__.read_text("utf-8"))
        assert log(self.test_dir_log.read_text("utf-8"))
        assert logging__init__(self.test_dir_logging__init__.read_text("utf-8"))
        assert logging_log(self.test_dir_logging_log.read_text("utf-8"))

    def check_rendered(self, content: str) -> bool:
        """Check string against expected rendered content."""
        return content == self.rendered_template

    def check_empty(self, content: str) -> bool:
        """Check string against empty string."""
        return content == ""

    def check_files_list(self) -> None:
        """Check if there are no additional files/dirs in test_dir."""
        files_and_dirs = set(self.test_dir.rglob("*"))
        paths = {
            self.test_dir__init__,
            self.test_dir_log,
            self.test_dir_logging,
            self.test_dir_logging__init__,
            self.test_dir_logging_log,
        }

        assert files_and_dirs == paths

    @pytest.mark.parametrize("pool_size", [1, 4, 8])
    def test_run_exclude_dir(self, pool_size: int) -> None:
        """Purpose of test is to check if autocopyright will add copyright to all files
        in test_dir."""
        autocopyright.run(
            comment_symbol="#",
            directory=[Path("test_dir")],
            glob=["*.py"],
            exclude=["{directory}/logging/*.*"],
            license_=Path("license.md.jinja2"),
            pool=pool_size,
        )

        self.check_content(
            __init__=self.check_rendered,
            log=self.check_rendered,
            logging__init__=self.check_empty,
            logging_log=self.check_empty,
        )
        self.check_files_list()

    @pytest.mark.parametrize("pool_size", [1, 4, 8])
    def test_run_exclude_dir_with_cwd(self, pool_size: int) -> None:
        """Purpose of test is to check if autocopyright will add copyright to all files
        in test_dir."""
        autocopyright.run(
            comment_symbol="#",
            directory=[Path("test_dir")],
            glob=["*.py"],
            exclude=["{cwd}/test_dir/logging/*.*"],
            license_=Path("license.md.jinja2"),
            pool=pool_size,
        )

        self.check_content(
            __init__=self.check_rendered,
            log=self.check_rendered,
            logging__init__=self.check_empty,
            logging_log=self.check_empty,
        )
        self.check_files_list()
