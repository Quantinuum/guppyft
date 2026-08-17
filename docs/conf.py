import guppyft  # noqa: INP001

html_title = f"GuppyFT v{guppyft.__version__} Documentation"

html_theme = "quantinuum_sphinx"
html_theme_options = {
    "sidebar_hide_name": False,
}

html_show_sourcelink = False
html_copy_source = False

html_static_path = ["_static"]
templates_path = ["_templates"]

master_doc = "index"
author = "Quantinuum"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosummary",
    "myst_nb",
    "sphinx.ext.mathjax",
    "sphinx.ext.intersphinx",
    "quantinuum_sphinx",
]


# Sphinx autosummary
# https://www.sphinx-doc.org/en/master/usage/extensions/autosummary.html

# See https://github.com/quantinuum/guppylang/pull/1028
autosummary_ignore_module_all = False  # Respect __all__ if specified
