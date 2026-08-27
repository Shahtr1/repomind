import os
from pathlib import Path

from .config import (
    IGNORED_DIRECTORIES,
    IGNORED_FILES,
    MAX_SEARCH_RESULTS,
    REPOSITORY_ROOT
)


def read_file(path: str) -> str:

    requested_path = (
        # Path overloads the / operator so that it means:
        # Join these paths together.
        REPOSITORY_ROOT / path
    ).resolve() # "Give me the canonical form of this path."
    # C:\AI-Learning\native_tools\..\config.py 
    # can resolve to 
    # C:\AI-Learning\config.py

    if not requested_path.is_relative_to(
        REPOSITORY_ROOT
    ):
        return "Error: path is outside the repository."

    with open(
        requested_path,
        "r",
        encoding="utf-8"
    ) as file:

        return file.read()


def list_files() -> str:

    files = []

    for root, directories, filenames in os.walk(REPOSITORY_ROOT):

        directories[:] = [
            directory
            for directory in directories
            if directory not in IGNORED_DIRECTORIES
        ]

        for filename in filenames:

            if filename in IGNORED_FILES:
                continue

            path = Path(root) / filename

            relative_path = path.relative_to(
                REPOSITORY_ROOT
            )

            # could produce
            # C:\Users\tramb\OneDrive\Documents\AI-Learning\native_tools\models.py
            # Now:
            # path.relative_to(REPOSITORY_ROOT)
            # produces:
            # native_tools\models.py
            # So the LLM receives cleaner repository context.

            files.append(
                str(relative_path)
            )

    return "\n".join(files)


def create_note(content: str) -> str:
    with open("agent_note.txt", "w") as file:
        file.write(content)

    return "Created agent_note.txt"


def search_files(query: str) -> str:

    matches = []

    for root, directories, files in os.walk(REPOSITORY_ROOT):

        directories[:] = [
            directory
            for directory in directories
            if directory not in IGNORED_DIRECTORIES
        ]

        for filename in files:

            if filename in IGNORED_FILES:
                continue

            path = Path(root) / filename

            relative_path = path.relative_to(
                REPOSITORY_ROOT
            )

            try:

                with open(
                    path,
                    "r",
                    encoding="utf-8"
                ) as file:

                    for line_number, line in enumerate(
                        file,
                        start=1
                    ):

                        if query.lower() in line.lower():

                            matches.append(
                                f"{str(relative_path)}:{line_number}: "
                                f"{line.rstrip()}"
                            )

                            if len(matches) >= MAX_SEARCH_RESULTS:
                                return "\n".join(matches)

            except (
                UnicodeDecodeError,
                PermissionError,
                OSError
            ):
                continue

    if not matches:
        return f"No matches found for: {query}"

    return "\n".join(matches)