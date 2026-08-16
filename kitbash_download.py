# d:\Assets\Unreal Assets\fab-key-management\kitbash3d\kitbash_download.py
# Builds and executes kit download requests for the KitBash3D Cargo app.
#
# Confirmed from capture: the actual file lives on S3 as a presigned URL, keyed as
#   https://kb3d-kits.s3.us-west-2.amazonaws.com/{kitName}/{kitName}.{software}.{res}.zip?X-Amz-...
# The S3 GET is unauthenticated (query-string signature is the auth), so it must NOT
# carry Cargo cookies or the Authorization header.
#
# STILL NEEDED: the Cargo API call that RETURNS the presigned URL. Until that capture
# arrives, build_download_request() is a placeholder; download_presigned() is complete.

import os
import re
import json
import requests

BASE_URL = "https://cargo-app.kitbash3d.com"
S3_BUCKET_URL = "https://kb3d-kits.s3.us-west-2.amazonaws.com"

# The download is a Next.js Server Action POSTed to /settings/kits, identified by a
# Next-Action id and carrying its arguments in a text/plain body. These ids are tied
# to a deployment (dpl_...) and change when KitBash3D redeploys - reconfirm if it 404s.
KITS_URL = f"{BASE_URL}/settings/kits"
NEXT_ACTION_ID = "7f1dbc3ee6c1982062623d0fa65a3637cd8780c61f"
NEXT_ROUTER_STATE_TREE = (
    '["",{"children":["(settings)",{"children":["settings",{"children":'
    '["kits",{"children":["__PAGE__",{},null,null,0]},null,null,4]},'
    'null,null,8]},null,null,12]},null,null,24]'
)

# Presigned S3 URLs for kits look like this in the flight response.
S3_URL_PATTERN = re.compile(r"https://kb3d-kits\.s3[^\s\"'\\]+")


def iter_renderer_options(kit):
    # Yield (software, renderer) pairs available for a kit summary from summarize_kits().
    print("[kitbash_download.py][iter_renderer_options] entering")
    renderers = kit.get("renderers") or {}
    for software, renderer_list in renderers.items():
        for renderer in renderer_list:
            yield software, renderer
    print("[kitbash_download.py][iter_renderer_options] exiting")


def build_s3_key(kit_name, software, resolution):
    # Reconstruct the observed S3 object key for a kit variant.
    print("[kitbash_download.py][build_s3_key] entering")
    filename = f"{kit_name}.{software.lower()}.{resolution}.zip"
    key = f"{kit_name}/{filename}"
    print(f"[kitbash_download.py][build_s3_key] exiting - {key}")
    return key


def build_action_body(kit_name, dcc, render_engine, resolution, download_preference="All files"):
    # Serialize the Server Action arguments for the download request body.
    # Confirmed shape (single-element array of one options object), e.g.:
    #   dcc="Unreal (5.1 and earlier)", renderEngine="Native", resolution="4K UAsset"
    print("[kitbash_download.py][build_action_body] entering")
    args = [{
        "dcc": dcc,
        "downloadPreference": download_preference,
        "kitName": kit_name,
        "renderEngine": render_engine,
        "resolution": resolution,
    }]
    # Compact separators match the browser's JSON.stringify (Content-Length 165).
    body = json.dumps(args, separators=(",", ":"))
    print("[kitbash_download.py][build_action_body] exiting")
    return body


def request_download_url(session, kit_name, dcc, render_engine, resolution,
                         download_preference="All files"):
    # Invoke the Next.js Server Action and extract the presigned S3 URL it returns.
    print("[kitbash_download.py][request_download_url] entering")
    headers = {
        "Accept": "text/x-component",
        "Content-Type": "text/plain;charset=UTF-8",
        "Next-Action": NEXT_ACTION_ID,
        "Next-Router-State-Tree": NEXT_ROUTER_STATE_TREE,
        "Origin": BASE_URL,
        "Referer": KITS_URL,
    }
    body = build_action_body(kit_name, dcc, render_engine, resolution, download_preference)
    response = session.post(KITS_URL, data=body, headers=headers)
    response.raise_for_status()

    match = S3_URL_PATTERN.search(response.text)
    download_url = match.group(0) if match else None
    print(f"[kitbash_download.py][request_download_url] exiting - {bool(download_url)}")
    return download_url


def download_presigned(url, dest_dir, chunk_size=1024 * 1024):
    # Stream a presigned S3 URL to disk WITHOUT Cargo auth (signature is in the query).
    print("[kitbash_download.py][download_presigned] entering")
    os.makedirs(dest_dir, exist_ok=True)
    filename = url.split("?")[0].rstrip("/").split("/")[-1] or "kit.zip"
    dest_path = os.path.join(dest_dir, filename)

    # A bare request - no session cookies/headers - matches the browser's S3 call.
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:153.0) "
            "Gecko/20100101 Firefox/153.0"
        ),
        "Referer": f"{BASE_URL}/",
    }
    with requests.get(url, headers=headers, stream=True) as response:
        response.raise_for_status()
        total = int(response.headers.get("Content-Length", 0))
        written = 0
        with open(dest_path, "wb") as handle:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    handle.write(chunk)
                    written += len(chunk)
                    if total:
                        pct = written * 100 // total
                        print(f"\r  {written // (1024*1024)} MB / {total // (1024*1024)} MB ({pct}%)", end="")
        if total:
            print()

    print(f"[kitbash_download.py][download_presigned] exiting - {dest_path}")
    return dest_path


def download_kit(session, kit_name, dcc, render_engine, resolution, dest_dir,
                 download_preference="All files"):
    # High-level helper: resolve a presigned URL for a kit variant and save the zip.
    print("[kitbash_download.py][download_kit] entering")
    url = request_download_url(session, kit_name, dcc, render_engine, resolution,
                               download_preference)
    if not url:
        print("[kitbash_download.py][download_kit] exiting - no url")
        return None
    path = download_presigned(url, dest_dir)
    print("[kitbash_download.py][download_kit] exiting")
    return path


def _main():
    # Standalone tester: paste a presigned URL to download it directly, no login needed.
    print("[kitbash_download.py][_main] entering")
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else input("Presigned S3 URL: ").strip()
    dest = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "downloads")
    path = download_presigned(url, dest)
    print(f"Saved to {path}")
    print("[kitbash_download.py][_main] exiting")


if __name__ == "__main__":
    _main()
