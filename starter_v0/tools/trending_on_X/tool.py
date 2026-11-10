from __future__ import annotations

import os
import urllib.parse
from typing import Any

import requests

from tools._shared import TIMEOUT

TOOL_NAME = "trending_on_X"
MAX_LIMIT = 50
DEFAULT_LIMIT = 10

# key -> (country name for twitter-api45, WOEID for X API v2)
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
ALIASES = {
    "vn": "vietnam", "viet nam": "vietnam", "global": "worldwide", "world": "worldwide",
    "usa": "us", "united states": "us", "gb": "uk", "jp": "japan", "kr": "korea",
    "south korea": "korea", "sg": "singapore", "th": "thailand", "in": "india",
}


def _error(message: str, location: str = "") -> dict[str, Any]:
    return {"tool": TOOL_NAME, "location": location, "items": [], "item_count": 0, "error": message}


def _to_int(value: Any) -> int | None:
    """'12.5K' -> 12500, '1,234 posts' -> 1234, None/garbage -> None."""
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


def _normalize_limit(limit: Any) -> int:
    """Model may send "5", 5.0, 0, -3 or garbage. Clamp to 1..50, fall back to default."""
    if isinstance(limit, bool):
        return DEFAULT_LIMIT
    try:
        value = int(float(limit))
    except (TypeError, ValueError):
        return DEFAULT_LIMIT
    if value < 1:
        return DEFAULT_LIMIT
    return min(value, MAX_LIMIT)


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


def trending_on_X(location: str = "vietnam", limit: int = DEFAULT_LIMIT, contains: str = "") -> dict[str, Any]:
    key = str(location or "vietnam").strip().lower()
    key = ALIASES.get(key, key)
    if key not in LOCATIONS:
        return _error(f"location '{location}' không hỗ trợ. Chọn: {', '.join(LOCATIONS)}", key)
    limit = _normalize_limit(limit)
    contains = str(contains or "").strip()

    country, woeid = LOCATIONS[key]
    rapid_key, x_token = os.getenv("RAPIDAPI_KEY"), os.getenv("X_BEARER_TOKEN")
    if rapid_key:
        host = os.getenv("RAPIDAPI_TWITTER_HOST") or os.getenv("RAPIDAPI_HOST") or "twitter-api45.p.rapidapi.com"
        url = f"https://{host}/trends.php"
        params: dict[str, Any] = {"country": country}
        headers = {"x-rapidapi-key": rapid_key, "x-rapidapi-host": host}
    elif x_token:
        url = f"https://api.x.com/2/trends/by/woeid/{woeid}"
        params = {"max_trends": MAX_LIMIT}
        headers = {"Authorization": f"Bearer {x_token}"}
    else:
        return _error("Thiếu RAPIDAPI_KEY hoặc X_BEARER_TOKEN.", key)

    try:
        response = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        trends = _parse(response.json())
    except requests.HTTPError as exc:
        return _error(f"HTTP error: {exc}", key)
    except requests.RequestException as exc:
        return _error(f"Không kết nối được API: {exc}", key)
    except ValueError:
        return _error("API trả về dữ liệu không phải JSON.", key)
    except Exception as exc:  # never raise into the agent loop
        return _error(f"{type(exc).__name__}: {exc}", key)

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
    return {"tool": TOOL_NAME, "location": key, "items": items, "item_count": len(items)}
