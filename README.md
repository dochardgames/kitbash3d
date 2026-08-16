# KitBash3D Cargo Automation

Scripts to log in to the KitBash3D Cargo app, list the kits you own, and download
them from the command line instead of clicking through the web UI.

This automates your own authenticated account only. Keep the repository private and
review the KitBash3D terms of service before using it.

## Requirements

- Python 3 (`python`, not `python3`)
- The `requests` library: `pip install requests`

## Setup

1. Copy the example environment file and fill in your credentials:

   ```powershell
   copy .env.example .env
   ```

   Then edit `.env`:

   ```
   KITBASH_EMAIL="you@example.com"
   KITBASH_PASSWORD="your-password"
   ```

   Quote the values so special characters (spaces, `= ; ^ , >`) are preserved.
   `.env` is gitignored and must never be committed.

## Usage

Run the main script:

```powershell
python kitbash_login.py
```

It will:

1. Log in and verify the session.
2. Fetch and print your owned kits, and save the full data to `my_kits.json`.
3. Prompt you to pick a kit and a software type, then download the zip to `downloads/`.

## How it works

The Cargo app is a Next.js site. The scripts replicate three of its calls:

- Login: `POST /api/auth/login` returns a bearer token and sets auth cookies.
- Kit list: `GET /settings/kits` returns a React Server Component (RSC) flight payload
  that is parsed for the `purchasedProducts` array.
- Download: a Next.js Server Action (`POST /settings/kits` with a `Next-Action` header)
  returns a presigned Amazon S3 URL, which is then streamed to disk without auth.

## Files

| File                  | Purpose |
| --------------------- | ------- |
| `kitbash_login.py`    | Entry point: login, session verify, kit listing, and the download picker. |
| `kitbash_config.py`   | Minimal `.env` loader (no external dependency). |
| `kitbash_kits.py`     | Fetches and parses the "My Kits" RSC payload. |
| `kitbash_products.py` | Fetches a product detail page by handle and scans it for option labels. |
| `kitbash_download.py` | Builds the download Server Action request and streams the S3 zip. |
| `kitbash_labels.py`   | Static map of download-form dropdown labels per software. |
| `SUMMARY.md`          | One or two line summary of every file and function. |

See `SUMMARY.md` for a per-function breakdown.

## Adding support for more software

Only Unreal is confirmed to download out of the box. The exact download-form labels
(for example `"Unreal (5.1 and earlier)"`, `"4K UAsset"`) are defined in the app's
frontend JavaScript, not in any API response, so each software type needs one capture:

1. In the browser DevTools Network tab, download a kit in the target software.
2. Open that `POST /settings/kits` request and copy its request body. It looks like:

   ```json
   [{"dcc":"...","downloadPreference":"All files","kitName":"...","renderEngine":"...","resolution":"..."}]
   ```

3. Add an entry to `LABEL_MAP` in `kitbash_labels.py` with the `dcc`, `renderEngine`,
   and `resolution` values from that body, and set `"confirmed": True`.

## Maintenance note

`NEXT_ACTION_ID` in `kitbash_download.py` is tied to the current app deployment. When
KitBash3D ships a new build, the download Server Action returns a 404 and this id must
be re-captured from a fresh download request.

## Security

- `.env` stores your password in plaintext on disk. It is gitignored; keep it local.
- `my_kits.json` and `downloads/` contain personal account data and are gitignored.
- If your credentials are ever exposed, rotate your KitBash3D password and update `.env`.
