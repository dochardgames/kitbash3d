# d:\Assets\Unreal Assets\fab-key-management\kitbash3d\kitbash_login.py
# Logs in to the KitBash3D Cargo app and returns an authenticated session.

import os
import json
import getpass
import requests

from kitbash_config import load_env
from kitbash_kits import get_kits, parse_purchased_products, summarize_kits
from kitbash_download import download_kit
from kitbash_labels import get_labels

BASE_URL = "https://cargo-app.kitbash3d.com"
LOGIN_URL = f"{BASE_URL}/api/auth/login"
ACCOUNT_URL = f"{BASE_URL}/api/account-page"
ME_URL = f"{BASE_URL}/api/auth/me"

# Match the browser so the API responds identically to the captured request.
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:153.0) "
        "Gecko/20100101 Firefox/153.0"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/json",
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/login",
}


def get_credentials():
    # Read credentials from .env / environment variables, prompting only if missing.
    print("[kitbash_login.py][get_credentials] entering")
    load_env()
    email = os.environ.get("KITBASH_EMAIL") or input("Email: ").strip()
    password = os.environ.get("KITBASH_PASSWORD") or getpass.getpass("Password: ")
    print("[kitbash_login.py][get_credentials] exiting")
    return email, password


def login(email, password):
    # POST credentials to the login endpoint and return the authenticated session.
    print("[kitbash_login.py][login] entering")
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    response = session.post(LOGIN_URL, json={"email": email, "password": password})
    response.raise_for_status()
    data = response.json()

    # The response body carries the bearer token; cookies are stored on the session.
    token = data.get("token")
    if token:
        session.headers["Authorization"] = f"Bearer {token}"

    print(
        "[kitbash_login.py][login] exiting - "
        f"user={data.get('fullName')} apexUserId={data.get('apexUserId')}"
    )
    return session, data


def verify_session(session):
    # GET /api/auth/me to confirm the current cookies/token are still valid.
    print("[kitbash_login.py][verify_session] entering")
    response = session.get(ME_URL)
    ok = response.status_code == 200
    data = response.json() if ok else None
    print(f"[kitbash_login.py][verify_session] exiting - valid={ok}")
    return ok, data


def get_account_page(session, apex_user_id):
    # Fetch the account page for the logged-in user using the authenticated session.
    print("[kitbash_login.py][get_account_page] entering")
    response = session.get(ACCOUNT_URL, params={"apexUserId": apex_user_id})
    response.raise_for_status()
    print("[kitbash_login.py][get_account_page] exiting")
    return response.json()


def main():
    # Entry point: log in, then demonstrate an authenticated follow-up request.
    print("[kitbash_login.py][main] entering")
    email, password = get_credentials()

    session, user = login(email, password)
    print(f"Logged in as {user.get('fullName')} ({user.get('userEmail')})")
    print(f"Roles: {user.get('userRoles')}")

    account = get_account_page(session, user.get("apexUserId"))
    subscription = account.get("subscription", {})
    print(f"Subscription status: {subscription.get('status')}")

    # Fetch the owned kits from the RSC endpoint and report what was found.
    payload = get_kits(session)
    products = parse_purchased_products(payload)
    kits = summarize_kits(products)
    print(f"Owned kits: {len(kits)}")
    for index, kit in enumerate(kits, start=1):
        print(f"  {index}. {kit['title']} ({kit['kitName']}) [{kit['genre']}]")

    # Persist the FULL product objects (all fields) for downstream use.
    out_path = os.path.join(os.path.dirname(__file__), "my_kits.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(products, handle, indent=2, ensure_ascii=False)
    print(f"Saved full kit data ({len(products)} kits) to {out_path}")

    # Optionally download one of the owned kits.
    prompt_and_download(session, kits)

    print("[kitbash_login.py][main] exiting")


def prompt_and_download(session, kits):
    # Interactively pick a kit and download options, then fetch the zip.
    print("[kitbash_login.py][prompt_and_download] entering")
    choice = input("\nDownload a kit? Enter its number (or blank to skip): ").strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(kits)):
        print("[kitbash_login.py][prompt_and_download] exiting - skipped")
        return

    kit = kits[int(choice) - 1]

    # List the software this specific kit offers (from its renderers metafield),
    # flagging which ones have a confirmed download preset in kitbash_labels.py.
    kit_renderers = kit.get("renderers") or {}
    print(f"\nSoftware available for '{kit['title']}':")
    for software_name, engines in kit_renderers.items():
        preset = get_labels(software_name)
        status = "downloadable" if (preset and preset.get("confirmed")) else "no preset - needs capture"
        print(f"  - {software_name}: {', '.join(engines)}  [{status}]")

    software = input("\nSoftware name [Unreal]: ").strip() or "Unreal"

    labels = get_labels(software)
    if not labels:
        print(f"No confirmed label preset for '{software}'. Capture one download for it,")
        print("then add its dcc/renderEngine/resolution to LABEL_MAP in kitbash_labels.py.")
        print("[kitbash_login.py][prompt_and_download] exiting - no preset")
        return

    dest_dir = os.path.join(os.path.dirname(__file__), "downloads")
    path = download_kit(
        session, kit["kitName"], labels["dcc"], labels["renderEngine"],
        labels["resolution"], dest_dir, labels["downloadPreference"],
    )
    if path:
        print(f"Downloaded to {path}")
    else:
        print("No download URL was returned - check the DCC/renderEngine/resolution labels.")
    print("[kitbash_login.py][prompt_and_download] exiting")


if __name__ == "__main__":
    main()
