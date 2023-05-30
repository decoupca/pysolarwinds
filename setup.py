import setuptools

__version__ = "0.0.3"
__author__ = "Austin de Coup-Crank"

with open("README.md", "r", encoding="utf-8") as fh:
    README = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    INSTALL_REQUIRES = fh.read().splitlines()

setuptools.setup(
    name="pysolarwinds",
    version=__version__,
    author=__author__,
    author_email="austindcc@gmail.com",
    description="An ergonomic, object-based interface for the SolarWinds SWIS SWISClient",
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
