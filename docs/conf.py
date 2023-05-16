import os
import sys

sys.path.insert(0, os.path.abspath(".."))

project = "shelephant"
copyright = "2021, Tom de Geus"
author = "Tom de Geus"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.todo",
    "sphinxarg.ext",
]

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "furo"
