# d:\Assets\Unreal Assets\fab-key-management\kitbash3d\SUMMARY.md
# 1-2 sentence summaries of each file and function in the KitBash3D Cargo automation.

## kitbash_login.py
Logs in to the Cargo app and drives the end-to-end flow (login, list kits, download).
- get_credentials(): Reads email/password from env vars, prompting if absent.
- login(email, password): POSTs credentials to /api/auth/login, returns an authed session and user data.
- verify_session(session): GETs /api/auth/me to confirm the cookies/token are still valid.
- get_account_page(session, apex_user_id): GETs the account page for the user.
- prompt_and_download(session, kits): Interactively picks a kit and options, then downloads its zip.
- main(): Orchestrates login, account fetch, kit listing, JSON save, and optional download.

## kitbash_kits.py
Fetches and parses the "My Kits" list from the Next.js RSC endpoint.
- _extract_json_array(text, key): Bracket-matches a "key":[...] array out of a flight payload.
- get_kits(session): GETs /settings/kits with the RSC headers, returns the raw flight payload.
- parse_purchased_products(payload): Extracts the purchasedProducts array into Python objects.
- summarize_kits(products): Trims each product to title/handle/kitName/genre/s3FileName/renderers.

## kitbash_products.py
Fetches a product detail page (RSC) by handle and scans it for download-option labels.
- get_product(session, handle): GETs /products/{handle} with RSC headers, returns the flight payload.
- scan_option_labels(payload): Best-effort extraction of candidate dcc/renderEngine/resolution labels.
- save_payload(payload, handle, dest_dir): Writes a raw product payload to disk for inspection.

## kitbash_labels.py
Static map of download-form dropdown labels (dcc/renderEngine/resolution) per software,
since those exact labels live in the frontend JS bundle, not the API payloads.
- get_labels(software_key): Returns the confirmed option labels for a software key, or None.
- list_software(): Lists mapped software keys, flagging unconfirmed template entries.

## kitbash_download.py
Builds and executes kit download requests via the Next.js Server Action + S3.
- iter_renderer_options(kit): Yields (software, renderer) pairs available for a kit.
- build_s3_key(kit_name, software, resolution): Reconstructs the observed S3 object key.
- build_action_body(kit_name, dcc, render_engine, resolution, download_preference): Serializes the Server Action body (compact JSON, 165 bytes).
- request_download_url(session, kit_name, dcc, render_engine, resolution, download_preference): POSTs the Server Action, regex-extracts the presigned S3 URL from the response.
- download_presigned(url, dest_dir, chunk_size): Streams a presigned S3 URL to disk with no auth and a progress readout.
- download_kit(session, kit_name, dcc, render_engine, resolution, dest_dir, download_preference): Resolves a presigned URL and saves the zip.
- _main(): Standalone tester that downloads a pasted presigned URL without logging in.

## Notes
- NEXT_ACTION_ID in kitbash_download.py is tied to the current deployment (dpl_...) and
  must be re-captured when KitBash3D redeploys, or the Server Action returns 404.
- The dcc/renderEngine/resolution values are exact UI dropdown labels (e.g.
  "Unreal (5.1 and earlier)", "Native", "4K UAsset"); the server maps them to S3 filenames.
