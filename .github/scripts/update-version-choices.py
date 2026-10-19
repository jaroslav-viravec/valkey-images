#!/usr/bin/env python3
"""Replace the auto-updated options block in a build workflow YAML file.

Usage:
    update-version-choices.py <workflow-file> <version> [<version> ...]

The file must contain a line ending with:
    # auto-updated by refresh-version-choices.yaml
as an anchor.  Everything beneath it (lines starting with '          - "')
is replaced with the new version list.  "latest" is always prepended so the
user can pick "build whatever is newest" without knowing the version number.
"""
import re
import sys

MARKER = "# auto-updated by refresh-version-choices.yaml"


def update(filepath: str, versions: list[str]) -> None:
    with open(filepath) as f:
        content = f.read()

    options = ["latest"] + [v for v in versions if v and v != "latest"]
    new_block = f"        options:  {MARKER}\n"
    for opt in options:
        new_block += f'          - "{opt}"\n'

    pattern = rf'        options:.*{re.escape(MARKER)}\n(?:          - "[^"]*"\n)+'
    new_content, n = re.subn(pattern, new_block, content)

    if n == 0:
        print(f"ERROR: marker '{MARKER}' not found in {filepath}", file=sys.stderr)
        sys.exit(1)

    with open(filepath, "w") as f:
        f.write(new_content)

    print(f"Updated {filepath} with options: {options}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <workflow-file> <version> [...]", file=sys.stderr)
        sys.exit(1)
    update(sys.argv[1], sys.argv[2:])
