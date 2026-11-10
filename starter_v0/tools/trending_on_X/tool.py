from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

LOCATIONS: dict[str, tuple[str, int]] = {
    "worldwide": ("Worldwide", 1),
    "vietnam": ("Vietnam", 23424984),
    "us": ("UnitedStates", 23424977),
    "uk": ("UnitedKingdom", 23424975),
    "japan": ("Japan", 23424856),
    "korea": ("Korea", 23424868),
    "singapore": ("Singapore", 23424948),
    "thailand": ("Thailand", 23424960),
    "india": ("India", 23424848),
}
ALIASES = {"vn": "vietnam", "global": "worldwide", "world": "worldwide", "usa": "us", "gb": "uk", "jp": "japan", "kr": "korea", "sg": "singapore", "th": "thailand", "in": "india"}


def _error(message: str, location: str = "") -> dict[str, Any]:
    return {"tool": "trending", "location": location, "items": [], "item_count": 0, "error": message}

def _to_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).upper().replace(",", "").replace("POSTS", "").replace("TWEETS", "").strip()
    mult = {"K": 1_000, "M": 1_000_000}.get(text[-1:], 1)
    try:
        return int(float(text[:-1] if mult > 1 else text) * mult)
    except ValueError:
        return None


def _get_json(url: str, headers: dict[str, str]) -> Any:
    req = urllib.request.Request(url, headers={"Accept": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _parse(data: Any) -> list[tuple[str, int | None]]:
    raw = (data.get("trends") or data.get("data") or []) if isinstance(data, dict) else data
    out: list[tuple[str, int | None]] = []
    for it in raw if isinstance(raw, list) else []:
        if isinstance(it, str):
            name, volume = it, None
        elif isinstance(it, dict):
            name = it.get("name") or it.get("trend_name") or ""
            volume = _to_int(it.get("tweet_volume") or it.get("tweet_count") or it.get("volume"))
        else:
            continue
        if str(name).strip():
            out.append((str(name).strip(), volume))
    return out


def trending_on_X(location: str = "vietnam", limit: int = 10, contains: str = "") -> dict[str, Any]:
    key = (location or "vietnam").strip().lower()
    key = ALIASES.get(key, key)
    if key not in LOCATIONS:
        return _error(f"location '{location}' không hỗ trợ. Chọn: {', '.join(LOCATIONS)}", key)
    try:
        limit = max(1, min(int(limit), 50))
    except (TypeError, ValueError):
        limit = 10

    country, woeid = LOCATIONS[key]
    rapid_key, x_token = os.getenv("RAPIDAPI_KEY"), os.getenv("X_BEARER_TOKEN")
    if rapid_key:
        host = os.getenv("RAPIDAPI_HOST", "twitter-api45.p.rapidapi.com")
        url = f"https://{host}/trends.php?" + urllib.parse.urlencode({"country": country})
        headers = {"x-rapidapi-key": rapid_key, "x-rapidapi-host": host}
    elif x_token:
        url = f"https://api.x.com/2/trends/by/woeid/{woeid}?max_trends=50"
        headers = {"Authorization": f"Bearer {x_token}"}
    else:
        return _error("Thiếu RAPIDAPI_KEY hoặc X_BEARER_TOKEN.", key)

    try:
        trends = _parse(_get_json(url, headers))
    except urllib.error.HTTPError as exc:
        return _error(f"HTTP {exc.code}: {exc.reason}", key)
    except (urllib.error.URLError, TimeoutError) as exc:
        return _error(f"Không kết nối được API: {getattr(exc, 'reason', exc)}", key)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _error("API trả về dữ liệu không phải JSON.", key)

    if contains:
        trends = [t for t in trends if contains.lower() in t[0].lower()]

    items = [
        {
            "rank": rank,
            "title": name,
            "query": name,
            "volume": volume,
            "summary": f"{name} ({volume:,} posts)" if volume else name,
            "url": "https://x.com/search?" + urllib.parse.urlencode({"q": name}),
            "source": "X Trending",
            "section": "Trending",
        }
        for rank, (name, volume) in enumerate(trends[:limit], start=1)
    ]
    return {"tool": "trending", "location": key, "items": items, "item_count": len(items)}