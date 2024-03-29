# -*- coding: utf-8 -*-
#
# manheim-c7n-tools documentation build configuration file, created by
# sphinx-quickstart on Sat Jun  6 16:12:56 2015.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import sys
import os
import re
# to let sphinx find the actual source...
sys.path.insert(0, os.path.abspath("../.."))
from manheim_c7n_tools.version import VERSION
import sphinx.environment
from docutils.utils import get_source_line
from docutils.nodes import GenericNodeVisitor, inline, Text, literal
from sphinx.addnodes import pending_xref

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
# sys.path.insert(0, os.path.abspath('.'))

is_rtd = os.environ.get('READTHEDOCS', None) != 'True'
readthedocs_version = os.environ.get('READTHEDOCS_VERSION', '')

rtd_version = VERSION

if (readthedocs_version in ['stable', 'latest', 'master'] or
    re.match(r'^\d+\.\d+\.\d+', readthedocs_version)):
    # this is a tag or stable/latest/master; show the actual version
    rtd_version = VERSION

# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.viewcode',
    'm2r2'
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The encoding of source files.
# source_encoding = 'utf-8-sig'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'manheim-c7n-tools'
copyright = u'2019 Manheim / Cox Automotive'
author = u'Manheim Release Engineering'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = rtd_version
# The full version, including alpha/beta/rc tags.
release = version

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
# today = ''
# Else, today_fmt is used as the format for a strftime call.
# today_fmt = '%B %d, %Y'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = []

# The reST default role (used for this markup: `text`) to use for all
# documents.
# default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
# add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
# add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
# show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# A list of ignored prefixes for module index sorting.
# modindex_common_prefix = []

# If true, keep warnings as "system message" paragraphs in the built documents.
# keep_warnings = False

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True


# -- Options for HTML output ----------------------------------------------

if is_rtd:
    import sphinx_rtd_theme
    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [
        sphinx_rtd_theme.get_html_theme_path(),
    ]
    html_static_path = ['_static']

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
html_title = 'v{v} - manheim-c7n-tools'.format(v=version)

htmlhelp_basename = 'manheim-c7n-toolsdoc'

# Add any extra paths that contain custom files (such as robots.txt or
# .htaccess) here, relative to this directory. These files are copied
# directly to the root of the documentation.
# html_extra_path = []

# thanks to: https://rackerlabs.github.io/docs-rackspace/tools/rtd-tables.html
#   see: https://docs.readthedocs.io/en/stable/guides/adding-custom-css.html
#   for the updated way to do this (as used here)
html_css_files = [
    '_static/theme_overrides.css',  # override wide tables in RTD theme
]

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
# html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
# html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
# html_additional_pages = {}

# If false, no module index is generated.
# html_domain_indices = True

# If false, no index is generated.
# html_use_index = True

# If true, the index is split into individual pages for each letter.
# html_split_index = False

# If true, links to the reST sources are added to the pages.
# html_show_sourcelink = True

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
# html_show_sphinx = True

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
# html_show_copyright = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
# html_use_opensearch = ''

# This is the file name suffix for HTML files (e.g. ".xhtml").
# html_file_suffix = None

# Language to be used for generating the HTML full-text search index.
# Sphinx supports the following languages:
#   'da', 'de', 'en', 'es', 'fi', 'fr', 'hu', 'it', 'ja'
#   'nl', 'no', 'pt', 'ro', 'ru', 'sv', 'tr'
# html_search_language = 'en'

# A dictionary with options for the search language support, empty by default.
# Now only 'ja' uses this config value
# html_search_options = {'type': 'default'}

# The name of a javascript file (relative to the configuration directory) that
# implements a search results scorer. If empty, the default will be used.
# html_search_scorer = 'scorer.js'

# Output file base name for HTML help builder.
# htmlhelp_basename = 'manheim-c7n-toolsdoc'

# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
# The paper size ('letterpaper' or 'a4paper').
# 'papersize': 'letterpaper',

# The font size ('10pt', '11pt' or '12pt').
# 'pointsize': '10pt',

# Additional stuff for the LaTeX preamble.
# 'preamble': '',

# Latex figure (float) alignment
# ' figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
  (master_doc, 'manheim-c7n-tools.tex', u'manheim-c7n-tools Documentation',
   u'Manheim RE', 'manual'),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
# latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
# latex_use_parts = False

# If true, show page references after internal links.
# latex_show_pagerefs = False

# If true, show URL addresses after external links.
# latex_show_urls = False

# Documents to append as an appendix to all manuals.
# latex_appendices = []

# If false, no module index is generated.
# latex_domain_indices = True


# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'manheim-c7n-tools', u'manheim-c7n-tools Documentation',
     [author], 1)
]

# If true, show URL addresses after external links.
# man_show_urls = False


# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
  (master_doc, 'manheim-c7n-tools', u'manheim-c7n-tools Documentation',
   author, 'manheim-c7n-tools', 'One line description of project.',
   'Miscellaneous'),
]

# Documents to append as an appendix to all manuals.
# texinfo_appendices = []

# If false, no module index is generated.
# texinfo_domain_indices = True

# How to display URL addresses: 'footnote', 'no', or 'inline'.
# texinfo_show_urls = 'footnote'

# If true, do not generate a @detailmenu in the "Top" node's menu.
# texinfo_no_detailmenu = False


# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
    'https://docs.python.org/3/': None,
    'boto3': ('https://boto3.amazonaws.com/v1/documentation/api/latest/', None),
    'cloud custodian': ('https://cloudcustodian.io/docs/', None)
}

autoclass_content = 'class'

autodoc_default_options = {
    'members': None,
    'undoc-members': None,
    'private-members': None,
    'show-inheritance': None
}

linkcheck_ignore = [
    r'https?://landscape\.io.*',
    r'https?://www\.virtualenv\.org.*',
    r'https?://.*\.readthedocs\.org.*',
    r'https?://codecov\.io.*',
    r'https?://.*readthedocs\.org.*',
    r'https?://manheim-c7n-tools\.readthedocs\.io.*',
    r'https?://pypi\.python\.org/pypi/manheim-c7n-tools',
    # broken bit.ly link in upstream c7n docs
    r'https?://bit\.ly/.*',
    r'https?://.*wikipedia\.org.*'
]


# exclude module docstrings - see http://stackoverflow.com/a/18031024/211734
def remove_module_docstring(app, what, name, obj, options, lines):
    if what == "module":
        del lines[:]


# ignore non-local image warnings
def _warn_node(self, msg, node, **kwargs):
    if not (
        msg.startswith('nonlocal image URI found:') or
        'Unexpected indentation' in msg or
        'Definition list ends without a blank line' in msg or
        'document isn\'t included in any toctree' in msg
    ):
        self._warnfunc(msg, '%s:%s' % get_source_line(node))


sphinx.environment.BuildEnvironment.warn_node = _warn_node


# BEGIN code to replace hard-coded links in README with internal references

class LinkToRefVisitor(GenericNodeVisitor):
    """
    To simplify documentation and reduce duplication, we want to include
    README.rst in docs/source/index.rst, since the files are *almost* identical.
    However, the one major difference is that index.rst uses Sphinx/rST refs for
    crosslinks, whereas README.rst is intended to be viewed on GitHub or PyPI,
    and uses absolute links (URLs) to the RTD docs.

    The solution to this is to find all of the links (reference and target) in
    the original doctree (for files that were originally /README.rst or
    /CHANGES.rst) and replace them with refrerences.

    See also on_doctree_read().
    """

    def __init__(self, document, replacements):
        GenericNodeVisitor.__init__(self, document)
        self.replacements = replacements
        self.lastref = None

    def visit_reference(self, node):
        """
        Hyperlinks are made up of a reference node, and a target node somewhere
        after it (with one or more Text nodes visited in-between them. When we
        find a reference node, just store it in an instance variable, to be used
        when the corresponding target node is found.
        """
        self.lastref = node

    def visit_target(self, node):
        """
        When we find a target node, first make sure it matches the last
        reference node we saw. Assuming it does, see if its refuri (link URI)
        is in our replacement list. If so, replace the link with an internal
        reference.
        """
        if self.lastref is None:
            return
        if (
            self.lastref.attributes['name'].lower() not in
            node.attributes['names'] and
            self.lastref.attributes['name'].lower() not in
            node.attributes['dupnames']
        ):
            # return if target doesn't match last reference found
            return
        if node.attributes['refuri'] not in self.replacements:
            # return if the refuri isn't in our replacement mapping
            return
        # ok, we have a node to replace...
        params = self.replacements[node.attributes['refuri']]
        meth = params[0]
        args = params[1:]
        # remove the target itself; we'll just replace the reference
        node.parent.remove(node)
        self.lastref.parent.replace(self.lastref, meth(*args))

    def unknown_visit(self, node):
        pass

    def default_visit(self, node):
        pass

    def default_departure(self, node):
        pass


def label_ref_node(docname, ref_to, title):
    """Generate a node that references a label"""
    txt = Text(title, rawsource=title)
    newchild = inline(
        ':ref:`%s`' % ref_to,
        '',
        txt,
        classes=['xref', 'std', 'std-ref']
    )
    newnode = pending_xref(
        ':ref:`%s`' % ref_to,
        newchild,
        reftype='ref',
        refwarn='True',
        reftarget=ref_to,
        refexplicit='False',
        refdomain='std',
        refdoc=docname
    )
    return newnode


def meth_ref_node(docname, ref_to, title=None):
    """Generate a node that references a :py:meth:"""
    if title is None:
        title = ref_to
    txt = Text(title, rawsource=title)
    newchild = literal(
        ':py:meth:`%s`' % ref_to,
        '',
        txt,
        classes=['xref', 'py', 'py-meth']
    )
    newnode = pending_xref(
        ':py:meth:`%s`' % ref_to,
        newchild,
        reftype='meth',
        refwarn='True',
        reftarget=ref_to,
        refexplicit='False',
        refdomain='py',
        refdoc=docname
    )
    return newnode


def on_doctree_read(_, doctree):
    """
    When the doctree has been read in, and ``include`` directives have been
    executed and replaced with the included file, walk the tree via
    LinkToRefVisitor.
    """
    docname = os.path.splitext(
        os.path.basename(doctree.attributes['source']))[0]
    if docname == 'index':
        ref_mapping = {
            'https://manheim-c7n-tools.readthedocs.io/':
                [
                    label_ref_node, docname, 'index',
                    'Index'
                ],
            'https://manheim-c7n-tools.readthedocs.io/en/latest/runner/':
                [
                    label_ref_node, docname, 'runner',
                    'manheim-c7n-runner'
                ],
            'https://manheim-c7n-tools.readthedocs.io/en/latest/policygen/':
                [
                    label_ref_node, docname, 'policygen',
                    'policygen'
                ],
            'https://manheim-c7n-tools.readthedocs.io/en/latest/s3archiver/':
                [
                    label_ref_node, docname, 's3archiver',
                    's3-archiver'
                ],
            'https://manheim-c7n-tools.readthedocs.io/en/latest/dryrun-diff/':
                [
                    label_ref_node, docname, 'dryrun-diff',
                    'dryrun-diff'
                ],
            'https://manheim-c7n-tools.readthedocs.io/en/latest/usage/':
                [
                    label_ref_node, docname, 'usage',
                    'Installation and Usage'
                ]
        }
        doctree.walk(LinkToRefVisitor(doctree, ref_mapping))

# END code to replace hard-coded links in README with internal references


def setup(app):
    app.connect("autodoc-process-docstring", remove_module_docstring)
    app.connect('doctree-read', on_doctree_read)
