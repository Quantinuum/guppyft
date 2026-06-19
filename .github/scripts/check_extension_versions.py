# ruff: noqa: INP001

import json
import subprocess
import sys
from pathlib import Path


def get_changed_files(target: str) -> list[Path]:
    """Get list of changed extension files in the PR"""
    # Use git to get the list of files changed compared to target
    cmd = [
        "git",
        "diff",
        "--name-only",
        target,
        "--",
        "src/guppyft/extensions/data/",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)  # noqa: S603
    changed_files = [Path(f) for f in result.stdout.splitlines() if f.endswith(".json")]
    return changed_files


def check_version_changes(changed_files: list[Path], target: str) -> list[str]:
    """Check if versions have been updated in changed files"""
    errors = []

    for file_path in changed_files:
        # Skip files that don't exist anymore (deleted files)
        if not file_path.exists():
            continue

        # Get the version in the current branch
        with file_path.open("r") as f:
            current = json.load(f)
            current_version = current.get("version")

        # Get the version in the target branch
        try:
            cmd = ["git", "show", f"{target}:{file_path}"]
            result = subprocess.run(cmd, capture_output=True, text=True)  # noqa: S603

            if result.returncode == 0:
                # File exists in target
                target_content = json.loads(result.stdout)
                target_version = target_content.get("version")

                if current_version == target_version:
                    errors.append(
                        f"Error: {file_path} was modified but version {current_version}"
                        " was not updated."
                    )
                else:
                    sys.stdout.write(
                        f"Version updated in {file_path}: {target_version}"
                        f" -> {current_version}\n"
                    )

            else:
                # New file - no version check needed
                pass

        except json.JSONDecodeError:
            # File is new or not valid JSON in target
            pass
    return errors


def get_latest_release_tag() -> str | None:
    """Get the latest release tag from git if available, otherwise return None."""
    result = subprocess.run(
        ["git", "tag", "--sort=-version:refname", "--list"],  # noqa: S607
        capture_output=True,
        text=True,
    )
    tags = [t.strip() for t in result.stdout.splitlines() if t.strip()]
    if tags:
        sys.stdout.write(f"Using latest release tag: {tags[0]}\n")
        return tags[0]

    return None


def main() -> int:
    target = sys.argv[1] if len(sys.argv) > 1 else get_latest_release_tag()
    if target is None:
        sys.stdout.write("No release tags found.\n")
        return 0

    changed_files = get_changed_files(target)
    if not changed_files:
        sys.stdout.write("No extension files changed.\n")
        return 0

    sys.stdout.write(f"Changed extension files: {', '.join(map(str, changed_files))}\n")

    errors = check_version_changes(changed_files, target)
    if errors:
        for error in errors:
            sys.stderr.write(error + "\n")
        return 1

    sys.stdout.write("All changed extension files have updated versions.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
