from __future__ import annotations

import math
from typing import Any

from tools._shared import err


def rank_by_engagement(
    items: list[dict[str, Any]] | None = None,
    metric: str = "favorites",
    limit: int | None = None,
) -> dict[str, Any]:
    """Rank existing posts by one metric, highest first, with missing values last."""
    try:
        if not isinstance(items, list):
            raise ValueError("items must be a list of posts")
        if metric not in ("favorites", "retweets", "views"):
            raise ValueError("metric must be favorites, retweets, or views")
        if limit is not None and (isinstance(limit, bool) or not isinstance(limit, int) or limit < 1):
            raise ValueError("limit must be a positive integer or omitted")

        def key(item: dict[str, Any]) -> tuple[bool, float]:
            if not isinstance(item, dict):
                raise ValueError("each item must be an object")
            metrics = item.get("metrics")
            if metrics is not None and not isinstance(metrics, dict):
                raise ValueError("metrics must be an object or null")
            value = (metrics or {}).get(metric)
            if value is None:
                return (True, 0.0)
            if isinstance(value, bool) or not isinstance(value, (int, float, str)):
                raise ValueError(f"{metric} must be a non-negative number or null")
            try:
                number = float(value.replace(",", "").strip() if isinstance(value, str) else value)
            except (ValueError, OverflowError):
                raise ValueError(f"{metric} must be a non-negative number or null") from None
            if not math.isfinite(number) or number < 0:
                raise ValueError(f"{metric} must be a non-negative finite number")
            return (False, -number)

        ranked = sorted(items, key=key)
        if limit is not None:
            ranked = ranked[:limit]
        return {"tool": "rank_by_engagement", "metric": metric, "items": ranked, "item_count": len(ranked)}
    except (ValueError, TypeError, OverflowError) as exc:
        return err("rank_by_engagement", exc)
