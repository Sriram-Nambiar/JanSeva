"""Welfare portal parsers package."""

from scraper.parsers.base import BaseSchemeParser
from scraper.parsers.myscheme import MySchemeParser
from scraper.parsers.central_dbt import CentralDbtParser
from scraper.parsers.generic import GenericWelfareParser

__all__ = [
    "BaseSchemeParser",
    "MySchemeParser",
    "CentralDbtParser",
    "GenericWelfareParser",
]
