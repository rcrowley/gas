"""
Static Gas
Richard Crowley <richard@opendns.com>

A WSGI app for streaming static files.
"""

import os

class Static(object):
    """
    A WSGI app for streaming static files.  See also:
    http://www.python.org/dev/peps/pep-0333/

    For the moment, everything is text/plain but it'd be nice to
    incorporate automatic MIME type detection like this:
    http://hupp.org/adam/hg/python-magic/file/d3cd83e5a773/magic.py
    """

    def __init__(self, document_root):
        self.document_root = document_root

    def __call__(self, environ, start_response):
        pathname = os.path.join(
            self.document_root,
            environ["PATH_INFO"][1:]
        )
        if os.path.exists(pathname):
            start_response("200 OK", [
                ("Content-Type", "text/plain"),
            ])
            return open(pathname)
        else:
            start_response("404 Not Found", [
                ("Content-Type", "text/plain"),
                ("Content-Length", 0),
            ])
            return []
