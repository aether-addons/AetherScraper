from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(__file__)
LIB = os.path.join(ROOT, "resources", "lib")
if LIB not in sys.path:
    sys.path.insert(0, LIB)


def main() -> None:
    from aetherscraper_program.routes import run

    run()


if __name__ == "__main__":
    main()
