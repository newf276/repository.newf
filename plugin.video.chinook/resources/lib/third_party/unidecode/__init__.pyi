from typing import Any, Dict, Optional, Sequence

Cache: Dict[int, Optional[Sequence[Optional[str]]]]


class UnidecodeError(ValueError):
    index: Optional[int] = ...

    def __init__(self, message: str, index: Optional[int] = ...) -> None: ...


def unidecode_expect_ascii(string: str, errors: str = ..., replace_str: str = ...) -> str: ...


def unidecode_expect_nonascii(string: str, errors: str = ..., replace_str: str = ...) -> str: ...


unidecode = unidecode_expect_ascii
