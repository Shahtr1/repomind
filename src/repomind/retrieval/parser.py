from ..models import (
    SearchMatch,
    SearchResult,
)


def parse_search_results(query: str, result: str) -> SearchResult:

    matches = []

    for line in result.splitlines():
        try:
            location, content = line.split(": ", maxsplit=1)

            path, line_number = location.rsplit(":", maxsplit=1)

            matches.append(SearchMatch(path=path, line_number=int(line_number), content=content))

        except ValueError:
            continue

    return SearchResult(query=query, matches=matches)
