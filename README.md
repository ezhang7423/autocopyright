# autocopyright

Autocopyright is a script which was designed to automatically add copyright notices at
the top of source files. It uses jinja2 templates which can be automatically filled with
values pulled from `pyproject.toml` and other files.

## Example

To run autocopyright you must specify comment sign, directory to traverse, glob patterns
of files to modify and path to license template.

```
autocopyright -s "#" -d autocopyright -g "*.py" -g "*.pyi" -l "./templates/MIT.md.jinja2"
```

## Templates

Autocopyright uses Jinja2 templates to determine content of copyright header. Such
template is loaded from predefined destination and rendered with few special variables
available. Those variables are listed below:

- `now` - `datetime.datetime` object holding current time (determined once, at the
  beginning of script execution)

- `pyproject` - dictionary-like object holding loaded content of `pyproject.toml` file
  loaded from current working directory of script.

Template for **LGPL-3.0** license could look like this:

```jinja
Copyright {{ now.year }} {{ pyproject.tool.poetry.authors[0] }}

This file is part of {{ pyproject.tool.poetry["name"] }}.
{{ pyproject.tool.poetry.repository }}

{{ pyproject.tool.poetry["name"] }} is free software: you can redistribute it and/or modify it under
the terms of the GNU Lesser General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option)
any later version.

{{ pyproject.tool.poetry["name"] }} is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
details.

You should have received a copy of the GNU Lesser General Public License
along with {{ pyproject.tool.poetry["name"] }}. If not, see <http://www.gnu.org/licenses/>.
```

## Pre-commit hook

To add this script as pre commit hook, create `.pre-commit-config.yaml` file, or append
to existing one, following lines:

```yaml
repos:
  - repo: https://github.com/Argmaster/autocopyright
    rev: "v1.0.0"
    hooks:
      - id: autocopyright
        args:
          [
            -s,
            "#",
            -d,
            <your-project-source-dir-name>,
            -g,
            "*.py",
            -l,
            <path-to-license-template>,
          ]
```

Replace `<your-project-source-dir-name>` with valid name of your project source
directory, for example `source` or `src`.

Replace `<path-to-license-template>` with path to jinja2 template file containing
license note, eg. `"./templates/LGPL3.md.jinja2"`. See **Templates** section for example
of template content.
