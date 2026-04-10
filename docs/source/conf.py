# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "devinput"
copyright = "2026, Adam Jenča"
author = "Adam Jenča"
release = "0.0.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx_mdinclude",
]

templates_path = ["_templates"]
exclude_patterns = []
autosummary_generate = True

myst_heading_anchors = 4
# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]
root_doc = "index"
html_theme_options = {
    "sidebar_includehidden": True,
    "extra_nav_links": {},
}
html_sidebars = {
    "**": [
        "searchbox.html",
        "about.html",
        "navigation.html",
    ]
}
