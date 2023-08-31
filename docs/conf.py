# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import re
import sys
from typing import Any

sys.path.insert(0, os.path.abspath(".."))

project = "CurricularAnalytics.py"
copyright = "2023, Greg Heileman, Hayden Free, Orhan Abar, Will Thompson, Sean Yen"
author = "Greg Heileman, Hayden Free, Orhan Abar, Will Thompson, Sean Yen"
with open("../pyproject.toml") as f:
    _match = re.search(r'^version\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE)
    if _match is None:
        raise ValueError("Could not get version from pyproject.toml.")
    release = _match.group(1)

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.mathjax",
]
autosummary_generate = True
autodoc_member_order = "bysource"
autodoc_typehints = "description"
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

intersphinx_mapping: Any = {"py": ("https://docs.python.org/3", None)}


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]
