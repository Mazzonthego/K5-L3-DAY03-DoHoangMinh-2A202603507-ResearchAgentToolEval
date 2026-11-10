---
name: trending_on_X
track: bonus
kind: remote_api
requires_env: [RAPIDAPI_KEY]
inputs: [location, limit, contains]
outputs: [items, item_count, location, error]
side_effect: false
---
# trending

Fetches trending topics on X for a region (twitter-api45, falls back to X API v2 via `X_BEARER_TOKEN`). Returns items ready for `format`, each with a `query` to pass to `social_search` for actual content. Returns `error` instead of raising on failure.
