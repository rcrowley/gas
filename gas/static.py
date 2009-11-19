"""
Static Gas
Richard Crowley <richard@opendns.com>

Gas WSGI app for streaming static files through grep-, awk- and sed-like
generators.
"""

import cgi
import os
import re

class Static(object):
    """
    Gas WSGI app for streaming static files through grep-, awk- and sed-like
    generators.  See also:
    http://www.python.org/dev/peps/pep-0333/

    For the moment, everything is text/plain but it'd be nice to
    incorporate automatic MIME type detection like this:
    http://hupp.org/adam/hg/python-magic/file/d3cd83e5a773/magic.py
    """

    def __init__(self, document_root):
        """
        Create a Gas WSGI app to serve files from the given
        document_root.
        """
        self.document_root = document_root

    def __call__(self, environ, start_response):
        """
        Process a request.
        """
        pathname = os.path.join(self.document_root, environ["PATH_INFO"][1:])

        if "GET" != environ["REQUEST_METHOD"]:
            start_response("405 Method Not Allowed", [
                ("Content-Type", "text/plain"),
                ("Content-Length", 0),
            ])
            return []

        if not os.path.exists(pathname):
            start_response("404 Not Found", [
                ("Content-Type", "text/plain"),
                ("Content-Length", 0),
            ])
            return []

        try:
            fd = open(pathname)
        except IOError:
            start_response("500 Internal Server Error", [
                ("Content-Type", "text/plain"),
                ("Content-Length", 0),
            ])
            return []
        start_response("200 OK", [
            ("Content-Type", "text/plain"),
        ])

        if "QUERY_STRING" not in environ:
            return fd

        # Chain available utilities in the order they appear in QUERY_STRING
        params = cgi.parse_qsl(environ["QUERY_STRING"])
        for param in params:
            if hasattr(self, param[0]):
                fd = getattr(self, param[0])(fd, param[1])
        return fd

    def grep(self, fd, pattern):
        """
        Yield all lines of the given iterable that match the given pattern.
        """
        regex = re.compile(pattern)
        for line in fd:
            if regex.search(line):
                yield line

    def awk(self, fd, fields):
        """
        TODO
        """
        for line in fd:
            yield line

    def sed(self, fd, expr):
        """
        TODO
        """
        for line in fd:
            yield line

    def wc(self, fd, arg):
        """
        Count characters or lines in the given iterable.
        """
        if "c" == arg:
            chars = 0
            for line in fd:
                chars += len(line)
            yield "%s\n" % chars
        if "l" == arg:
            lines = 0
            for line in fd:
                lines += 1
            yield "%s\n" % lines
        else:
            yield ""
