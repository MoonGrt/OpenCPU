"""Launch either window from an installed package or the source checkout."""
import sys
from PyQt5.QtWidgets import QApplication


def _run(window_type):
    app = QApplication.instance() or QApplication(sys.argv)
    window = window_type()
    window.show()
    return app.exec_()


def ide_main():
    from .ide import IDEWindow
    return _run(IDEWindow)


def downloader_main():
    from .downloader import DownloaderWindow
    return _run(DownloaderWindow)
