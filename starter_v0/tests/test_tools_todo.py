"""TODO(student): Tool Unit Test Challenge.

Each test below is a stub. Replace `pytest.skip(...)` with a real test.
Patterns to copy are in test_tools_examples.py. Fixtures are in conftest.py.

Rules:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

import pytest

from conftest import FakeResponse  # noqa: F401  (you will need it)
from tools import TOOL_FUNCTIONS  # noqa: F401

TODO = "TODO(student): implement this test"


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    options = ["Tài khoản A", "Tài khoản B"]
    result = TOOL_FUNCTIONS["clarify"]("Bạn chọn tài khoản nào?", "choice", options)
    assert result["options"] == options
    assert result["awaiting_user"] is True
    assert result["response_type"] == "choice"


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    # Items with section "A", "B", "A" -> markdown has exactly one "## A" and one "## B".
    pytest.skip(TODO)


def test_format_thread_numbers_items() -> None:
    # template="thread" -> lines start with "1/", "2/", ...
    pytest.skip(TODO)


def test_format_empty_items_does_not_crash() -> None:
    # items=None and items=[] -> item_count == 0, no exception.
    pytest.skip(TODO)


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    # Set TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID, mock HTTP.
    # Assert: exactly one POST, URL contains the token, json has chat_id + text, status == "sent".
    pytest.skip(TODO)


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    pytest.skip(TODO)


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    # timeframe=None -> request body has no "time_range" key.
    pytest.skip(TODO)


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    # Mock {"data": {"markdown": "...", "metadata": {"title": "T", "sourceURL": "https://..."}}}
    # Assert title/url/source/summary in result["items"][0].
    pytest.skip(TODO)


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    pytest.skip(TODO)


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    calls = fake_http(FakeResponse({"timeline": [
        {"text": "No ID"}, None,
        *[{"tweet_id": str(i), "screen_name": "example", "text": f"Post {i}"} for i in range(1, 7)],
    ]}))
    result = TOOL_FUNCTIONS["timeline"]("example", limit=3)
    assert [item["url"] for item in result["items"]] == [
        f"https://x.com/example/status/{i}" for i in range(1, 4)
    ]
    assert len(calls) == 1
    assert calls[0]["params"] == {"screenname": "example"}


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    # Assert the request params carry the query and search_type ("Top" / "Latest").
    pytest.skip(TODO)


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    pytest.skip(TODO)


def test_policy_area_filter_only_returns_that_area() -> None:
    # policy_area="data_privacy" -> every result has policy_area == "data_privacy".
    pytest.skip(TODO)


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    # One policy file contains a quoted line that tries to give the assistant orders.
    # Query that section (source_citation) and assert: that line is in untrusted_text, NOT in facts.
    pytest.skip(TODO)


# ---------------- YOUR NEW TOOL(S) ----------------
# Write at least 3 tests per tool your team adds:
#   1. happy path (mocked if it calls an API)
#   2. bad / missing input from the model (empty string, wrong type, out-of-enum value)
#   3. failure path (missing key, HTTP error, timeout) -> returns error dict, does not raise

def test_rank_by_engagement_sorts_limits_and_keeps_input() -> None:
    items = [
        {"title": "A", "metrics": {"views": "1,200"}},
        {"title": "B", "metrics": {"views": 2500}},
        {"title": "C", "metrics": {"views": "2500"}},
        {"title": "Missing", "metrics": {"views": None}},
    ]
    result = TOOL_FUNCTIONS["rank_by_engagement"](items, metric="views", limit=3)
    assert [item["title"] for item in result["items"]] == ["B", "C", "A"]
    assert result["item_count"] == 3
    assert [item["title"] for item in items] == ["A", "B", "C", "Missing"]


@pytest.mark.parametrize("args", [
    {}, {"items": "invalid"}, {"items": [None]},
    {"items": [], "metric": "likes"},
    {"items": [], "limit": 0}, {"items": [], "limit": True},
])
def test_rank_by_engagement_invalid_arguments_return_error(args) -> None:
    result = TOOL_FUNCTIONS["rank_by_engagement"](**args)
    assert result["error"] == "ValueError"
    assert "message" in result


@pytest.mark.parametrize("value", ["unknown", "NaN", -1, True, [], float("inf")])
def test_rank_by_engagement_invalid_metric_value_returns_error(value) -> None:
    result = TOOL_FUNCTIONS["rank_by_engagement"]([{"metrics": {"favorites": value}}])
    assert result["error"] == "ValueError"


def test_rank_by_engagement_missing_metric_is_last_not_zero() -> None:
    items = [{"title": "missing"}, {"title": "zero", "metrics": {"favorites": 0}}]
    result = TOOL_FUNCTIONS["rank_by_engagement"](items)
    assert [item["title"] for item in result["items"]] == ["zero", "missing"]


def test_rank_by_engagement_empty_items_succeeds() -> None:
    result = TOOL_FUNCTIONS["rank_by_engagement"]([])
    assert result["items"] == []
    assert result["item_count"] == 0


@pytest.mark.parametrize("tool_name", ["timeline", "social_search"])
def test_retweet_uses_original_post_metrics_and_url(tool_name, monkeypatch, fake_http):
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    original = {"tweet_id": "123", "text": "Original", "author": {"screen_name": "owner"},
                "favorites": 1663, "retweets": 197, "views": "48347"}
    wrapper = {"tweet_id": "456", "text": "RT @owner: Original", "screen_name": "owner",
               "favorites": 0, "retweets": 197, "retweeted_tweet": original}
    fake_http(FakeResponse({"timeline": [wrapper]}))
    args = {"screenname": "owner"} if tool_name == "timeline" else {"query": "test"}
    item = TOOL_FUNCTIONS[tool_name](**args)["items"][0]
    assert item["url"] == "https://x.com/owner/status/123"
    assert item["metrics"] == {"favorites": 1663, "retweets": 197, "views": "48347"}
    assert item["metrics_scope"] == "original_post"
    ranked = TOOL_FUNCTIONS["rank_by_engagement"]([item, {"metrics": {"favorites": 7}}])
    assert ranked["items"][0] == item


@pytest.mark.parametrize("tool_name", ["timeline", "social_search"])
def test_retweet_without_original_does_not_report_wrapper_metrics(tool_name, monkeypatch, fake_http):
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    fake_http(FakeResponse({"timeline": [{"id": "456", "text": "RT @owner: Original", "favorites": 0}]}))
    args = {"screenname": "owner"} if tool_name == "timeline" else {"query": "test"}
    item = TOOL_FUNCTIONS[tool_name](**args)["items"][0]
    assert item["metrics"]["favorites"] is None
    assert item["metrics_scope"] == "original_unavailable"


def test_timeline_reports_page_scope(monkeypatch, fake_http):
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    fake_http(FakeResponse({"timeline": [], "next_cursor": "next-page"}))
    result = TOOL_FUNCTIONS["timeline"]("owner")
    assert result["scope"] == "one_recent_api_page"
    assert result["has_more"] is True
