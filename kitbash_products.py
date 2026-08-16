# d:\Assets\Unreal Assets\fab-key-management\kitbash3d\kitbash_products.py
# Fetches a product detail page (RSC) by handle and scans it for download-option labels.

import os
import re

BASE_URL = "https://cargo-app.kitbash3d.com"

# Known-good example labels used to locate the option lists inside the flight payload.
# These match the captured Unreal download request and the S3 filename convention.
LABEL_HINTS = {
    "resolution": re.compile(r'"[^"]*(?:UAsset|\b\d+K\b)[^"]*"'),
    "dcc": re.compile(r'"(?:Unreal|Blender|Maya|Cinema 4d|3ds Max|Houdini|Unity|FBX[^"]*)[^"]*"'),
    "renderEngine": re.compile(r'"(?:Native|Arnold|Octane|Redshift|VRay|HDRP|BuiltIn|UE4|UE5)[^"]*"'),
}


def get_product(session, handle):
    # GET /products/{handle} as an RSC flight payload for the given kit handle.
    print("[kitbash_products.py][get_product] entering")
    url = f"{BASE_URL}/products/{handle}"
    headers = {
        "Accept": "*/*",
        "RSC": "1",
        "Referer": f"{BASE_URL}/products/{handle}",
    }
    # A dummy _rsc cache-buster keeps parity with the browser; value is not validated.
    response = session.get(url, params={"_rsc": "python"}, headers=headers)
    response.raise_for_status()
    print(f"[kitbash_products.py][get_product] exiting - {len(response.text)} chars")
    return response.text


def scan_option_labels(payload):
    # Best-effort: pull candidate dcc/renderEngine/resolution labels from the payload.
    print("[kitbash_products.py][scan_option_labels] entering")
    found = {}
    for field, pattern in LABEL_HINTS.items():
        matches = {m.strip('"') for m in pattern.findall(payload)}
        found[field] = sorted(matches)
    counts = {k: len(v) for k, v in found.items()}
    print(f"[kitbash_products.py][scan_option_labels] exiting - {counts}")
    return found


def save_payload(payload, handle, dest_dir):
    # Persist a raw product payload so its structure can be inspected offline.
    print("[kitbash_products.py][save_payload] entering")
    os.makedirs(dest_dir, exist_ok=True)
    path = os.path.join(dest_dir, f"product_{handle}.rsc.txt")
    with open(path, "w", encoding="utf-8") as handle_file:
        handle_file.write(payload)
    print(f"[kitbash_products.py][save_payload] exiting - {path}")
    return path
