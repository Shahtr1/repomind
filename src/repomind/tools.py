import os
from pathlib import Path

from .config import IGNORED_DIRECTORIES, IGNORED_FILES, MAX_SEARCH_RESULTS, REPOSITORY_ROOT
from .models import ToolOutcome


def read_file(path: str) -> ToolOutcome:
    requested_path = (REPOSITORY_ROOT / path).resolve()

    if not requested_path.is_relative_to(REPOSITORY_ROOT):
        return ToolOutcome(
            success=False,
            error="Path is outside the repository.",
        )

    try:
        with open(requested_path, encoding="utf-8") as file:
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

    except OSError as error:
        return ToolOutcome(
            success=False,
            error=f"Unable to read file '{path}': {error}",
        )


def list_files() -> ToolOutcome:
    files = []

    try:
        for root, directories, filenames in os.walk(REPOSITORY_ROOT):
            directories[:] = [
                directory for directory in directories if directory not in IGNORED_DIRECTORIES
            ]

            for filename in filenames:
                if filename in IGNORED_FILES:
                    continue

                path = Path(root) / filename

                relative_path = path.relative_to(REPOSITORY_ROOT)

                files.append(str(relative_path))

        return ToolOutcome(
            success=True,
            result="\n".join(files),
        )

    except OSError as error:
        return ToolOutcome(
            success=False,
            error=f"Unable to list repository files: {error}",
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


def search_files(query: str) -> ToolOutcome:
    matches = []

    try:
        for root, directories, files in os.walk(REPOSITORY_ROOT):
            directories[:] = [
                directory for directory in directories if directory not in IGNORED_DIRECTORIES
            ]

            for filename in files:
                if filename in IGNORED_FILES:
                    continue

                path = Path(root) / filename

                relative_path = path.relative_to(REPOSITORY_ROOT)

                try:
                    with open(path, encoding="utf-8") as file:
                        for line_number, line in enumerate(file, start=1):
                            if query.lower() in line.lower():
                                matches.append(f"{relative_path}:{line_number}: {line.rstrip()}")

                                if len(matches) >= MAX_SEARCH_RESULTS:
                                    return ToolOutcome(
                                        success=True,
                                        result="\n".join(matches),
                                    )

                # Individual unreadable files do not mean the entire
                # repository search failed. Continue searching other files.
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
