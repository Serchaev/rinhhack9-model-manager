from typing import Generator


def list_chunks(lst: list, chunk_size: int) -> Generator[list, None, None]:
    for i in range(0, len(lst), chunk_size):
        yield lst[i : i + chunk_size]
