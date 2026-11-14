"""python3 tools/levelang <command> ...   (same as `python3 -m levelang` from inside tools/levelang)"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from levelang.cli import main  # noqa: E402

raise SystemExit(main())
