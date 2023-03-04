# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'teamtalk.py'
copyright = '2023, Jessica Tegner'
author = 'Jessica Tegner'

# check if the current commit is tagged as a release (vX.Y.Z) and set the version
import subprocess, re

GIT_TAG_OUTPUT = subprocess.check_output(["git", "tag", "--points-at", "HEAD"])
current_tag = GIT_TAG_OUTPUT.decode().strip()
if re.match(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$", current_tag):
    version = current_tag
else:
    version = "latest"

release = version

import os
import sys

sys.path.insert(0, os.path.abspath('..'))

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinxcontrib_trio",
    "sphinx.ext.autodoc",
    "sphinx_sitemap",
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'scrolls'
html_static_path = ['_static']

sitemap_url_scheme = "{lang}/{version}/{link}"
html_baseurl = 'https://teamtalkpy.readthedocs.io/'
html_extra_path = [
    "robots.txt",
]

# autodoc settings
autodoc_class_signature = "separated"
autodoc_member_order = 'bysource'

extlinks = {
    'issue': ('https://github.com/JessicaTegner/teamtalk.py/issues/%s', '#%s'),
    'version': ('https://pypi.org/project/teamtalk.py/%s', 'v%s'),
}

# Links used for cross-referencing stuff in other documentation
intersphinx_mapping = {
    'py': ('https://docs.python.org/3', None),
}

rst_prolog = """
.. |coro| replace:: This function is a |coroutine_link|_.
.. |maybecoro| replace:: This function *could be a* |coroutine_link|_.
.. |coroutine_link| replace:: *coroutine*
.. _coroutine_link: https://docs.python.org/3/library/asyncio-task.html#coroutine
"""

# napoleon settings

napoleon_google_docstring = True
napoleon_include_init_with_doc = True
