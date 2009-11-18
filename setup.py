import distutils.core

distutils.core.setup(
    name="gas",
    version="0.1",
    packages=["gas"],
    author="Richard Crowley",
    author_email="richard@opendns.com",
    url="http://github.com/rcrowley/gas",
    license="BSD",
    description="Gas is a tiny prefork WSGI server and app for streaming static files through grep-, awk- and sed-like generators."
)
