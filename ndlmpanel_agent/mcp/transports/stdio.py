"""stdio 传输层。"""
import sys
from collections.abc import Callable

Handler = Callable[[str], str | None]

def stdioServe(handler: Handler) -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        response = handler(line)
        if response is None:
            continue
        sys.stdout.write(response + "\n")
        sys.stdout.flush()
