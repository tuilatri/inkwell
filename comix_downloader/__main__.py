"""
Entry point for comix_downloader module
Allows running as: python -m comix_downloader
"""

from .cli import app

if __name__ == "__main__":
    app()
