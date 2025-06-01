from setuptools import setup
import os
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    version=os.environ.get('BUILD_VERSION'),
    name = "TCPLib",
    author = "Joshua Kitchen",
    description = "A basic library for implementing a TCP client/server",
    license="MIT",
    url = "https://github.com/kitchej/TCPLib",
    long_descriptionv = long_description,
    long_description_content_type = 'text/markdown'
)
