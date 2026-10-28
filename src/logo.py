"""The site logo files. Run by hand only when the logo changes: python src/logo.py [--png]

The ASA mark (October 2026, filed with EGIPA) is defined only in src/asa_mark.py; src/site_assets.py writes every
logo file from it (same file names, URLs and pixel sizes as before, so templates and email signatures keep
working). This script is the old entry point and simply runs site_assets.py. Never draw a logo by hand.
"""
import os, runpy

if __name__ == '__main__':
    runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'site_assets.py'), run_name='__main__')
