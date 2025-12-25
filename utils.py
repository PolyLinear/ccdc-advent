

import sys

def err_print(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)
