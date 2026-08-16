# d:\Assets\Unreal Assets\fab-key-management\kitbash3d\kitbash_config.py
# Minimal .env loader so credentials live in a file instead of the shell each session.

import os

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")


def load_env(path=ENV_PATH):
    # Read KEY=VALUE lines from a .env file into os.environ (does not overwrite existing).
    print("[kitbash_config.py][load_env] entering")
    if not os.path.exists(path):
        print("[kitbash_config.py][load_env] exiting - no .env file")
        return False

    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            # Strip matching surrounding quotes so passwords with spaces survive intact.
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            os.environ.setdefault(key, value)

    print("[kitbash_config.py][load_env] exiting - loaded")
    return True
