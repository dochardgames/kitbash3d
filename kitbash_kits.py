# d:\Assets\Unreal Assets\fab-key-management\kitbash3d\kitbash_kits.py
# Fetches and parses the "My Kits" list from the KitBash3D Cargo RSC endpoint.

import json

BASE_URL = "https://cargo-app.kitbash3d.com"
KITS_URL = f"{BASE_URL}/settings/kits"

# The Next.js router tree the browser sends so the server returns the kits segment.
NEXT_ROUTER_STATE_TREE = (
    '["",{"children":["(settings)",{"children":["settings",{"children":'
    '["kits",{"children":["__PAGE__",{},null,"refetch",0]},null,null,4]},'
    'null,null,8]},null,null,12]},null,null,24]'
)


def _extract_json_array(text, key):
    # Locate "key":[ ... ] in a flight payload and return the bracket-matched slice.
    print("[kitbash_kits.py][_extract_json_array] entering")
    marker = f'"{key}":'
    start = text.find(marker)
    if start == -1:
        print("[kitbash_kits.py][_extract_json_array] exiting - key not found")
        return None

    i = text.find("[", start)
    depth = 0
    in_string = False
    escape = False
    for pos in range(i, len(text)):
        ch = text[pos]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    print("[kitbash_kits.py][_extract_json_array] exiting - matched")
                    return text[i:pos + 1]

    print("[kitbash_kits.py][_extract_json_array] exiting - no closing bracket")
    return None


def get_kits(session):
    # Request the kits RSC segment and return the raw text/x-component payload.
    print("[kitbash_kits.py][get_kits] entering")
    headers = {
        "Accept": "*/*",
        "RSC": "1",
        "Next-Router-State-Tree": NEXT_ROUTER_STATE_TREE,
        "Next-Url": "/settings",
        "Referer": f"{BASE_URL}/settings",
    }
    # A dummy _rsc cache-buster keeps parity with the browser; value is not validated.
    response = session.get(KITS_URL, params={"_rsc": "python"}, headers=headers)
    response.raise_for_status()
    print(f"[kitbash_kits.py][get_kits] exiting - {len(response.text)} chars")
    return response.text


def parse_purchased_products(payload):
    # Pull the purchasedProducts array out of the flight payload into Python objects.
    print("[kitbash_kits.py][parse_purchased_products] entering")
    raw = _extract_json_array(payload, "purchasedProducts")
    if raw is None:
        print("[kitbash_kits.py][parse_purchased_products] exiting - not found")
        return []

    products = json.loads(raw)
    print(f"[kitbash_kits.py][parse_purchased_products] exiting - {len(products)} kits")
    return products


def summarize_kits(products):
    # Reduce each product to the fields most useful for a downloads workflow.
    print("[kitbash_kits.py][summarize_kits] entering")
    summary = []
    for product in products:
        metafields = product.get("metafields") or {}
        summary.append({
            "title": product.get("title"),
            "handle": product.get("handle"),
            "kitName": metafields.get("kitName"),
            "genre": metafields.get("genre"),
            "s3FileName": product.get("s3FileName", {}).get("value")
            if isinstance(product.get("s3FileName"), dict) else None,
            "renderers": metafields.get("renderers"),
        })
    print(f"[kitbash_kits.py][summarize_kits] exiting - {len(summary)} kits")
    return summary
