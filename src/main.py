from __future__ import annotations

import sys

from src.app import Application


def main() -> int:
    app = Application(sys.argv)
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
