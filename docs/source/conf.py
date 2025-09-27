# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join('..','..')))
# from vcams import __version__ as vcams_version   # TODO
vcams_version = '3.1.2'

# -- Project information -----------------------------------------------------

project = 'VCAMS'
copyright = '2025, Mohammadreza Khoshbin'

author = 'Mohammadreza Khoshbin'

# The full version, including alpha/beta/rc tags
release = vcams_version  # TODO: check


# -- General configuration ---------------------------------------------------

numfig = True  # Default values of numfig_format and numfig_secnum_depth are OK.
#
# language = 'en'
# math_number_all = True
#
# highlight_language = 'python3'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx.ext.autodoc' ,
              'sphinx.ext.napoleon',
              'sphinx_autodoc_typehints',
              'sphinx.ext.mathjax' ,
              # 'matplotlib.sphinxext.plot_directive',  TODO
              'sphinx_rtd_theme']

# Options for autodoc.
autodoc_member_order = 'bysource'
autodoc_mock_imports = ['numpy', 'scipy', 'six', 'matplotlib', 'skimage',
                        'abaqus', 'abaqusConstants', 'abaqusExceptions',
                        'part', 'mesh', 'odbAccess', 'regionToolset']
# TODO: Why are these here? Has it been copied from PyAuxetic?
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'}
# TODO: check options at https://pypi.org/project/sphinx-autodoc-typehints/

# # Options for matplotlib.
# plot_html_show_source_link = False
# plot_html_show_formats = False

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

html_logo = '_static/logo.png'
html_favicon = '_static/favicon.ico'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
html_css_files = ['css/custom.css',]
#html_js_files = ['js/custom.js',]

# Add a GitHub button.
html_context = {
    "display_github": True,
    'github_user': 'mkhoshbin1',
    'github_repo': 'vcams',
    'github_version': 'main',
    'conf_py_path': '/docs/source/',
    'license': 'CC BY 4.0',
    'license_url': 'https://creativecommons.org/licenses/by/4.0/',
}
