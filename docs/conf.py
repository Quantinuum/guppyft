import guppyft  # noqa: INP001

html_title = f"Guppy FT v{guppyft.__version__} Documentation"

html_theme = "quantinuum_sphinx"
html_theme_options = {
    "sidebar_hide_name": False,
}

html_show_sourcelink = False
html_copy_source = False

templates_path = ["_templates"]

master_doc = "index"
author = "Quantinuum"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosummary",
    "sphinx_tabs.tabs",
    "myst_nb",
    "sphinx.ext.mathjax",
    "sphinx.ext.intersphinx",
    "quantinuum_sphinx",
    "sphinx_copybutton",
]

# --- MyST-NB config ---
# https://myst-nb.readthedocs.io/en/latest/configuration.html
nb_execution_mode = "cache"
nb_execution_show_tb = True  # Show traceback if cell execution fails
nb_execution_raise_on_error = True  # Cell execution failures are errors not warnings
nb_execution_timeout = 90  # Cells which take >90s give timeout error.
nb_merge_streams = True  # Accumulates all stdout streams into one, same with stderr
# ----------------------


exclude_patterns = ["build/**", "jupyter_execute", ".jupyter_cache", "**/README.md"]

myst_enable_extensions = [
    "dollarmath",
    "html_image",
    "attrs_inline",
    "colon_fence",
    "amsmath",
]

# Sphinx autosummary
# https://www.sphinx-doc.org/en/master/usage/extensions/autosummary.html

# __all__ dictates which classes and functions are documented for a module
autosummary_ignore_module_all = False  # Respect __all__ if specified


intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "hugr": ("https://quantinuum.github.io/hugr/", None),
    "zixy": ("https://quantinuum.github.io/zixy/", None),
    "guppylang": ("https://docs.quantinuum.com/guppy/", None),
}
