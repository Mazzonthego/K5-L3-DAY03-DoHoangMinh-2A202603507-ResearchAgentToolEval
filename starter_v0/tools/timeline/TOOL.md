---
name: timeline
track: core
kind: live_api
provider: RapidAPI Twitter API45
requires_env: [RAPIDAPI_KEY, RAPIDAPI_TWITTER_HOST]
inputs: [screenname, limit]
outputs: [items]
side_effect: false
---
# timeline

Fetches recent posts from a single account. `screenname` is an account handle
without `@`.

Use for posts BY a known account, not keyword searches ABOUT a topic. If the
account is missing or ambiguous, call `clarify` first; do not guess an account.
The implementation trims whitespace and an optional leading `@`, then validates
1-15 ASCII letters, digits, or underscores. URLs and display names are rejected.
`limit` defaults to 5 and must be positive; digit strings such as `"3"` are accepted.
Invalid input is rejected before HTTP; missing keys and HTTP failures return an
error dictionary. Entries without an ID are skipped.

One API page is fetched, so the result may contain fewer than `limit` posts.
The tool preserves API order and does not paginate or independently sort posts.
`RAPIDAPI_TWITTER_HOST` defaults to `twitter-api45.p.rapidapi.com`.
