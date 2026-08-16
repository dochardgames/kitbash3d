# d:\Assets\Unreal Assets\fab-key-management\kitbash3d\kitbash_labels.py
# Static map of the download-form dropdown labels the Server Action expects.
#
# WHY THIS IS STATIC: these exact labels (e.g. "Unreal (5.1 and earlier)", "4K UAsset")
# are NOT in the product/kits API payloads - they live in the frontend JS bundle. The
# only reliable source is a captured download request. Add an entry per DCC by capturing
# one download (DevTools -> that POST /settings/kits -> Request body) and copying the
# dcc / renderEngine / resolution values here.

# Keyed by a short software key. Each entry mirrors one confirmed Server Action payload.
# "confirmed": True means it was taken from a real captured request and verified to work.
LABEL_MAP = {
    "unreal": {
        "dcc": "Unreal (5.1 and earlier)",
        "renderEngine": "Native",
        "resolution": "4K UAsset",
        "downloadPreference": "All files",
        "confirmed": True,
    },
    # Templates below are UNCONFIRMED guesses - replace with captured values before use.
    # "blender": {"dcc": "Blender", "renderEngine": "Native", "resolution": "4K", "downloadPreference": "All files", "confirmed": False},
    # "maya":    {"dcc": "Maya",    "renderEngine": "Arnold", "resolution": "4K", "downloadPreference": "All files", "confirmed": False},
}


def normalize_key(software_name):
    # Map a metafield software name ("Unreal", "3ds Max") to a LABEL_MAP key.
    print("[kitbash_labels.py][normalize_key] entering")
    key = software_name.strip().lower().replace(" ", "").replace("+", "")
    print(f"[kitbash_labels.py][normalize_key] exiting - {key}")
    return key


def get_labels(software_key):
    # Return the option labels for a software key, or None if not mapped.
    print("[kitbash_labels.py][get_labels] entering")
    entry = LABEL_MAP.get(normalize_key(software_key))
    print(f"[kitbash_labels.py][get_labels] exiting - found={bool(entry)}")
    return entry


def list_software():
    # List the software keys that have a label mapping, flagging unconfirmed ones.
    print("[kitbash_labels.py][list_software] entering")
    keys = [
        (key, entry.get("confirmed", False))
        for key, entry in LABEL_MAP.items()
    ]
    print(f"[kitbash_labels.py][list_software] exiting - {len(keys)} entries")
    return keys
