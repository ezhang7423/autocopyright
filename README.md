# autocopyright

Autocopyright is a script which was designed to automatically add copyright
notices at the top of source files. It uses jinja2 templates which can be
automatically filled with values pulled from `pyproject.toml` and other files.

## Example

To run autocopyright you must specify comment sign, directory to traverse, glob
patterns of files to modify and path to license template.

```
autocopyright -s "#" -d autocopyright -g "*.py" -g "*.pyi" -l "./templates/MIT.md.jinja2"
```
