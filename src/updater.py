"""
Auto-updater — checks GitHub Releases for a newer version.
"""
import urllib.request
import urllib.error
import json
import re

APP_VERSION  = "1.0.0"
GITHUB_REPO  = "Zuptex/SexytexLauncher"
API_URL      = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
TIMEOUT      = 5   # seconds


def _parse_version(v: str):
    """Return tuple of ints from a version string like 'v1.2.3' or '1.2.3'."""
    v = v.lstrip("v")
    parts = re.findall(r"\d+", v)
    return tuple(int(x) for x in parts[:3])


def check_for_updates() -> dict | None:
    """
    Returns a dict {"version": str, "url": str, "notes": str}
    if a newer release exists, otherwise None.
    """
    try:
        req = urllib.request.Request(
            API_URL,
            headers={"User-Agent": f"SexytexBdoLauncher/{APP_VERSION}",
                     "Accept": "application/vnd.github+json"}
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read())

        latest_tag  = data.get("tag_name", "")
        latest_ver  = _parse_version(latest_tag)
        current_ver = _parse_version(APP_VERSION)

        if latest_ver > current_ver:
            notes = data.get("body", "").strip()
            # trim notes if very long
            if len(notes) > 400:
                notes = notes[:400] + "…"
            return {
                "version": latest_tag,
                "url":     data.get("html_url", f"https://github.com/{GITHUB_REPO}/releases"),
                "notes":   notes or "No release notes provided.",
            }
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError):
        pass
    return None
