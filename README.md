# try_codex

This repository provides a small sample map and racing line.
Use `raceline_editor.py` to view the `lanelet2_map.osm` file
overlaid with the racing line CSV and to edit the racing line
interactively.

## Usage

```bash
python3 raceline_editor.py             # open GUI with sample files
python3 raceline_editor.py --nogui     # just check that files load
```

The editor allows you to drag each point of the racing line. After
editing, press the **Save** button and choose a path to write the
updated CSV.

