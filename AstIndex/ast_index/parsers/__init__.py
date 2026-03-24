"""Parser modules for different programming languages."""

from .base import BaseParser
from . import python
from . import csharp
from . import javascript
from . import typescript


def get_parser(language: str):
    return BaseParser.get_parser(language)


def get_supported_languages():
    return BaseParser.get_supported_languages()


__all__ = ["BaseParser", "get_parser", "get_supported_languages"]
