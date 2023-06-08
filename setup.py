import setuptools

__version__ = "0.5.0"
__author__ = "Austin de Coup-Crank"

with open("README.md", encoding="utf-8") as fh:
    README = fh.read()

with open("requirements.txt", encoding="utf-8") as fh:
    INSTALL_REQUIRES = fh.read().splitlines()

setuptools.setup(
    name="pysolarwinds",
    version=__version__,
    author=__author__,
    author_email="austindcc@gmail.com",
    description="A modern Python API for the SolarWinds Information Service (SWIS).",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/decoupca/pysolarwinds",
    install_requires=INSTALL_REQUIRES,
    dependency_links=[],
    classifiers=[
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.9",
)

# ruff: noqa: D100
