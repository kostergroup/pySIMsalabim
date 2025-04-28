# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import sys
# import pySIMsalabim from two folders up
sys.path.insert(0, os.path.abspath('../..'))
import pySIMsalabim
import shutil
from pathlib import Path

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'pySIMsalabim'
copyright = '2024, Vincent M. Le Corre, Sander Heester, L. Jan Anton Koster'
author = 'Vincent M. Le Corre, Sander Heester, L. Jan Anton Koster'
release = '1.02'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['myst_parser',
                "sphinx.ext.viewcode",
                "sphinx.ext.autodoc",
                "sphinx.ext.napoleon",
                "sphinx.ext.todo",
                "sphinx.ext.intersphinx",
                "nbsphinx",
                "sphinx_gallery.load_style",
                "IPython.sphinxext.ipython_console_highlighting",
                "sphinx.ext.mathjax",  # Maths visualization
                "sphinx.ext.graphviz",  # Dependency diagrams
                "sphinx_copybutton",
                "notfound.extension",
                'sphinx_search.extension',
                'sphinx_gallery.gen_gallery',
                "sphinx_gallery.load_style",]

templates_path = ['_templates']
exclude_patterns = []
source_suffix = {
    '.rst': 'restructuredtext',
    '.txt': 'markdown',
    '.md': 'markdown',
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# ensure custom.css lives in _static/css for HTML builds
src = Path(__file__).parent / 'custom.css'
dest_dir = Path(__file__).parent / '_static' / 'css'
dest_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(src, dest_dir / 'custom.css')

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_logo = "pySIMsalabim_logo.png"
html_theme_options = {
    'logo_only': True,
    # 'display_version': False,
}
# load a custom CSS to size the logo
html_css_files = [
    'css/custom.css',
]

# # -- Options for HTML output -------------------------------------------------
# # https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = 'sphinx_rtd_theme'
# html_static_path = ['_static']


# -- Options for sphinx_gallery ----------------------------------------------
from plotly.io._sg_scraper import plotly_sg_scraper
image_scrapers = ('matplotlib', plotly_sg_scraper,)

sphinx_gallery_conf = {
     'doc_module': ('plotly',),
     'examples_dirs': 'examples',   # path to your example scripts
     'gallery_dirs': 'auto_examples',  # path to where to save gallery generated output
     'filename_pattern': r"\.ipynb", # Notebooks to include
     'image_scrapers': image_scrapers,
    #  'ignore_pattern': r"__init__\.py", # Ignore this file
    #  'subsection_order': ExplicitOrder([
    #                 '../../examples/DD_Fit_fake_OPV.ipynb',
    #                 '../../examples/DD_Fit_real_OPV.ipynb',]),


}

nbsphinx_execute = 'never' # so we don't run the notebooks

html_context = {
    "display_github": True, # Integrate GitHub
    "github_user": "kostergroup", # Username
    "github_repo": "pySIMsalabim", # Repo name
    "github_version": "main", # Version
    "conf_py_path": "/docs/source/", # Path in the checkout to the docs root
}