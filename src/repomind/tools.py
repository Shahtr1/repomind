import os
from collections.abc import Iterator
from pathlib import Path

from repomind.data.models import ToolOutcome

from .config import IGNORED_DIRECTORIES, IGNORED_FILES, MAX_SEARCH_RESULTS, REPOSITORY_ROOT


def is_ignored_path(path: Path) -> bool:
    """
    Returns True when any part of the path belongs to an ignored
    directory or when the final filename is explicitly ignored.
    """

    # Check directory names anywhere in the path.
    if any(part in IGNORED_DIRECTORIES for part in path.parts):
        return True

    # Check the final filename.
    if path.name in IGNORED_FILES:
        return True

    return False


def iter_repository_files() -> Iterator[Path]:
    """
    Yields repository files while pruning ignored directories.

    The directory pruning happens before os.walk() enters those
    directories, which avoids scanning their contents entirely.
    """

    for root, directories, filenames in os.walk(REPOSITORY_ROOT):
        root: str
        directories: list[str]
        filenames: list[str]

        # Prevent os.walk() from entering ignored directories.
        directories[:] = sorted(
            directory for directory in directories if directory not in IGNORED_DIRECTORIES
        )

        for filename in sorted(filenames):
            path = Path(root) / filename

            if is_ignored_path(path):
                continue

            yield path


def read_file(path: str) -> ToolOutcome:
    requested_path = (REPOSITORY_ROOT / path).resolve()

    # Security boundary: prevent paths such as ../../secret.txt.
    if not requested_path.is_relative_to(REPOSITORY_ROOT):
        return ToolOutcome(
            success=False,
            error="Path is outside the repository.",
        )

    # Repository boundary: do not allow direct access to ignored paths.
    if is_ignored_path(requested_path):
        return ToolOutcome(
            success=False,
            error=f"Path is ignored by repository policy: {path}",
        )

    try:
        with requested_path.open(encoding="utf-8") as file:
            return ToolOutcome(
                success=True,
                result=file.read(),
            )

    except FileNotFoundError:
        return ToolOutcome(
            success=False,
            error=f"File not found: {path}",
        )

    except PermissionError:
        return ToolOutcome(
            success=False,
            error=f"Permission denied reading: {path}",
        )

    except UnicodeDecodeError:
        return ToolOutcome(
            success=False,
            error=f"File is not valid UTF-8 text: {path}",
        )

    except OSError as error:
        return ToolOutcome(
            success=False,
            error=f"Unable to read file '{path}': {error}",
        )


def list_files() -> ToolOutcome:
    try:
        files = [str(path.relative_to(REPOSITORY_ROOT)) for path in iter_repository_files()]

        return ToolOutcome(
            success=True,
            result="\n".join(files),
        )

    except OSError as error:
        return ToolOutcome(
            success=False,
            error=f"Unable to list repository files: {error}",
        )


def search_files(query: str) -> ToolOutcome:
    matches = []

    try:
        for path in iter_repository_files():
            relative_path = path.relative_to(REPOSITORY_ROOT)

            try:
                with path.open(encoding="utf-8") as file:
                    for line_number, line in enumerate(file, start=1):
                        if query.lower() in line.lower():
                            matches.append(f"{relative_path}:{line_number}: {line.rstrip()}")

                            if len(matches) >= MAX_SEARCH_RESULTS:
                                return ToolOutcome(
                                    success=True,
                                    result="\n".join(matches),
                                )

            # One unreadable/binary file should not fail the entire search.
            except (UnicodeDecodeError, PermissionError, OSError):
                continue

        if not matches:
            return ToolOutcome(
                success=True,
                result=f"No matches found for: {query}",
            )

        return ToolOutcome(
            success=True,
            result="\n".join(matches),
        )

    except OSError as error:
        return ToolOutcome(
            success=False,
            error=f"Unable to search repository files: {error}",
        )


def create_note(content: str) -> ToolOutcome:
    try:
        with open("agent_note.txt", "w", encoding="utf-8") as file:
            file.write(content)

        return ToolOutcome(
            success=True,
            result="Created agent_note.txt",
        )

    except OSError as error:
        return ToolOutcome(
            success=False,
            error=f"Unable to create agent_note.txt: {error}",
        )
