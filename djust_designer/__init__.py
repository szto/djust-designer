from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("djust-designer")
except PackageNotFoundError:  # local checkout without install
    __version__ = "0.0.0+dev"
