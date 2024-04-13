import logging

try:
    from PyInstaller.utils.hooks import collect_submodules

    hiddenimports = collect_submodules('scripts')
    hiddenimports += collect_submodules('PySubtitle.Providers')

except ImportError:
    logging.info("PyInstaller not found, skipping hook")