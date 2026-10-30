"""Launch the downloader independently of the IDE."""
from opencpu.gui.app import downloader_main

if __name__ == "__main__":
    raise SystemExit(downloader_main())
