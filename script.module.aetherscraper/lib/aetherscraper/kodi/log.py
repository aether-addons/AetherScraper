from __future__ import annotations


def kodi_logger(prefix="AetherScraper"):
    try:
        import xbmc  # type: ignore
    except Exception:
        return lambda message: print(f"[{prefix}] {message}")

    def log(message):
        xbmc.log(f"[{prefix}] {message}", xbmc.LOGINFO)

    return log
