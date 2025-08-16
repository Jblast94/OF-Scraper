#!/root/OF-Scraper/.venv/bin/python
# -*- coding: utf-8 -*-
import multiprocessing
import sys
import argparse

import ofscraper.main.open.load as load
import ofscraper.utils.system.system as system
from ofscraper.ui.gui import MainWindow  # Import desktop UI
from ofscraper.ui.web.app import app as web_app  # Import web UI

def parse_args():
    parser = argparse.ArgumentParser(description="OF-Scraper Launcher")
    parser.add_argument('--ui', choices=['desktop', 'web'], help="Launch UI mode: desktop or web")
    return parser.parse_args()

def main():
    args = parse_args()
    if args.ui == 'desktop':
        from PySide6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    elif args.ui == 'web':
        web_app.run(debug=False, port=5000)
    elif system.get_parent():
        load.main()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
