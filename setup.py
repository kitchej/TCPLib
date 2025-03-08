from setuptools import setup
import os
setup(
    version=os.environ.get('BUILD_VERSION'),
    name = "TCPLib",
    author = "Joshua Kitchen",
    description = "A basic library for implementing a TCP client/server",
    license="MIT",
    url = "https://github.com/kitchej/TCPLib",
)
