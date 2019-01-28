import os.path
from setuptools import setup

# The directory containing this file
HERE = os.path.abspath(os.path.dirname(__file__))

# The text of the README file
with open(os.path.join(HERE, "README.md")) as fid:
    README = fid.read()

# This call to setup() does all the work
setup(
    name="purestoragefa_exporter",
    version="1.0.0",
    description="Exports to Prometheus Purestorage Flasharray metrics",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/labazza/purestorage-prometheus.git",
    author="labazza",
    author_email="davide.obbi@booking.com",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
    ],
    packages=["purestoragefa_exporter"],
    include_package_data=True,
    install_requires=["prometheus_client", "purestorage", "urllib3", "requests"],
    entry_points={
        "console_scripts": [
            "purestoragefa_exporter=purestoragefa_exporter.__main__:main",
        ]
    },
)
