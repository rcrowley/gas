"""
Gas
Richard Crowley <richard@opendns.com>

Gas prefork WSGI server and friends.
(With apologies to Jacob Kaplan-Moss and Ryan Tomayko.)
"""

import os
import socket
import sys

class Gas(object):
    """
    A prefork HTTP server.  See also:
    http://jacobian.org/writing/python-is-unix/
    http://www.python.org/dev/peps/pep-0333/
    """

    def __init__(self, application, host="localhost", port=80, n=3):
        self.application = application
        self.host = host
        self.port = port
        self.n = n

    def run(self):
        self.acceptor = socket.socket()
        self.acceptor.bind((self.host, self.port))
        self.acceptor.listen(10)
        for i in range(self.n):
            pid = os.fork()
            if 0 == pid:
                try:
                    self.child()
                except KeyboardInterrupt:
                    sys.exit()
            elif -1 == pid:
                sys.exit(1)
        try:
            os.waitpid(-1, 0)
        except KeyboardInterrupt:
            sys.exit()

    def child(self):
        while 1:
            conn, addr = self.acceptor.accept()
            fd = conn.makefile()
            environ = Environ(fd, self.host, self.port)

            # WSGI plumbing
            headers_set = []
            headers_sent = []
            def write(data):
                if not headers_set:
                    raise AssertionError("write() before start_response()\n")
                elif not headers_sent:
                    status, response_headers = headers_sent[:] = headers_set
                    fd.write("%s %s\r\n" % (environ.protocol, status))
                    for header in response_headers:
                        fd.write("%s: %s\r\n" % header)
                    fd.write("\r\n")
                fd.write(data)
                fd.flush()
            def start_response(status, response_headers, exc_info=None):
                if exc_info:
                    try:
                        raise exc_info[0], exc_info[1], exc_info[2]
                    finally:
                        exc_info = None
                elif headers_set:
                    raise AssertionError("headers already sent!\n")
                headers_set[:] = [status, response_headers]
                return write

            # Actually run the app
            result = application(environ, start_response)
            try:
                for data in result:
                    if data:
                        write(data)
                if not headers_sent:
                    write("")
            finally:
                if hasattr(result, "close"):
                    result.close()
            fd.flush()
            fd.close()
            conn.close()

class Environ(dict):
    """
    An environment ready to be sent to WSGI (with some extras).  See also:
    http://www.python.org/dev/peps/pep-0333/
    http://github.com/facebook/tornado/blob/master/tornado/httpserver.py
    """

    def __init__(self, fd, host="localhost", port=80):

        # Setup base environment
        dict.__init__(self, dict(os.environ.items()))
        self["wsgi.input"] = fd
        self["wsgi.errors"] = sys.stderr
        self["wsgi.version"] = (1, 0)
        self["wsgi.multithread"] = False
        self["wsgi.multiprocess"] = True
        self["wsgi.run_once"] = True
        self["wsgi.url_scheme"] = "http"

        # GET /foo/bar HTTP/1.1
        self.method, self.uri, self.protocol = fd.next().strip().split()
        # TODO Error checking
        self["REQUEST_METHOD"] = self.method
        self["SCRIPT_NAME"] = ""
        pos = self.uri.find("?")
        if -1 != pos:
            self["PATH_INFO"] = self.uri[:pos]
            self["QUERY_STRING"] = self.uri[pos+1:]
        else:
            self["PATH_INFO"] = self.uri
        self["SERVER_NAME"] = host
        self["SERVER_PORT"] = port
        self["SERVER_PROTOCOL"] = self.protocol

        # Headers
        for line in fd:
            line = line.strip()
            if "" == line:
                break
            name, value = line.split(": ", 1)
            name = name.strip().replace("-", "_").upper()
            if name in ("CONTENT_TYPE", "CONTENT_LENGTH"):
                self[name] = value
            else:
                self["HTTP_%s" % name] = value

if "__main__" == __name__:

    import optparse
    parser = optparse.OptionParser(add_help_option=False)
    parser.add_option("--help", dest="help", action="store_true",
        default=False, help="show this help message")
    parser.add_option("-a", "--app", dest="application",
        default="static.Static", help="path to Python WSGI callable",
        metavar="MODULE")
    parser.add_option("-c", "--construct", dest="construct",
        action="store_true", default=False,
        help="construct a WSGI callable with the remaining arguments")
    parser.add_option("-h", "--host", dest="host", default="localhost",
        help="hostname to bind to", metavar="HOST")
    parser.add_option("-p", "--port", dest="port", type="int", default=80,
        help="port number to bind to", metavar="PORT")
    parser.add_option("-n", dest="n", type="int", default=3,
        help="number of children to fork()", metavar="N")
    options, args = parser.parse_args()

    # Import the app
    path = options.application.split(".")
    if 1 == len(path):
        name = "__main__"
    else:
        name = ".".join(path[:-1])
        __import__(name)
    application = getattr(sys.modules[name], path[-1])
    if options.construct:
        application = application(*args)

    Gas(application, options.host, options.port, options.n).run()
