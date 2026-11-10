"""Research Agent — Streamlit demo UI.

One screen that shows every core behaviour of the lab agent end to end:

* chat with the real multi-round tool loop (`chat.run_model_tool_loop`);
* a visible tool trace per turn: tool name, arguments, result summary, OK / FAIL,
  one step per tool call, grouped by round;
* the `clarify` pause: the agent asks, the user answers in the UI, the agent's
  original question is re-sent together with the answer and the turn resumes;
* the `send` safety gate: the model can only *request* a Telegram send. A real
  send happens solely when the user confirms the exact text in the UI, which
  then calls `send_telegram(text, confirmed=True)` server-side;
* the `format` digest with a preview and a markdown export;
* the tool registry read from `artifacts/tools.yaml` (what the model is given);
* an eval dashboard that reads real run JSON from `runs/` — no invented numbers;
* the artifact version (prompt hash / tools hash) the session is pinned to.

Run from this folder:

    streamlit run app.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

ROOT = Path(__file__).resolve().parent
ARTIFACTS_DIR = ROOT / "artifacts"
RUNS_DIR = ROOT / "runs"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env  # noqa: E402
from versioning import build_artifact_version  # noqa: E402

load_lab_env(ROOT)

st.set_page_config(page_title="Research Agent — Demo", layout="wide")

PROVIDERS = ["vietapi", "openrouter", "openai", "anthropic", "gemini", "ollama"]
# (eval case id, question) — routing, clarify, digest and send in one place.
SAMPLES = [
    ("R03", "Tổng hợp tin AI hôm nay trên X, có đủ nguồn, để mình đăng lên Telegram"),
    ("R10", "Tweet mới nhất của Sam Altman là gì?"),
    ("R12", "Đăng bản tin này lên Telegram giúp mình"),
    ("E04", "Tóm tắt giúp mình một paper mới trên arXiv về Transformer"),
]
STATUS_LABEL = {
    "answered": "đã trả lời",
    "waiting_for_user": "đang hỏi lại",
    "max_tool_rounds": "dừng vì hết số vòng",
    "provider_error": "lỗi provider",
}
SEND_OUTCOME = {
    "sent": ("đã gửi tới Telegram", "green"),
    "cancelled": ("giữ bản nháp, không gửi", "gray"),
}


# ---------------------------------------------------------------------------
# Backend (the same objects chat.py builds)
# ---------------------------------------------------------------------------


@st.cache_resource(show_spinner=False)
def load_backend(provider_name: str, model: str | None, version: str) -> dict[str, Any]:
    from providers import make_provider
    from providers.base import ToolCall  # noqa: F401 — imported for the provider contract
    from tools import load_tool_declarations, to_openai_tools

    prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    declarations = load_tool_declarations(tools_path)
    return {
        "provider": make_provider(provider_name),
        "model": model or None,
        "declarations": declarations,
        "openai_tools": to_openai_tools(declarations),
        "system_prompt": prompt_path.read_text(encoding="utf-8"),
        "artifact": build_artifact_version(version, prompt_path, tools_path),
    }


def backend(profile: dict[str, str]) -> dict[str, Any]:
    return load_backend(profile["provider"], profile["model"] or None, profile["version"])


def streamed_run_turn(
    bk: dict[str, Any], history: list[dict[str, str]], user_text: str
) -> tuple[dict[str, Any] | None, str]:
    """Run a turn, writing the progress trace into `st.status` steps in the main area.

    The tool loop is untouched: this only re-points its module-level `print`
    (which logs one line per tool call) at the placeholder, and fills each
    placeholder with the call's outcome once it has run. Returns (result, error);
    a provider failure is returned, never raised.
    """
    from chat import run_model_tool_loop, trim_history

    namespace = run_model_tool_loop.__globals__
    original_print = namespace.get("print", print)
    placeholders: list[Any] = []

    def _to_steps(*args: Any, **kwargs: Any) -> None:
        text = str(args[0]) if args else ""
        if text.startswith("🔧"):
            placeholders.append(st.markdown(f":gray[Đang chạy {text[2:].strip()}…]"))
            return
        original_print(*args, **kwargs)

    st.markdown(f"**Lượt mới** · {user_text}")
    st.caption(f"Gửi {len(history) + 1} tin nhắn tới `{bk['model']}` cùng {len(bk['declarations'])} tool")
    messages = [
        {"role": "system", "content": bk["system_prompt"]},
        *trim_history(history, st.session_state.history_window),
        {"role": "user", "content": user_text},
    ]
    started = time.perf_counter()
    namespace["print"] = _to_steps
    try:
        result = run_model_tool_loop(
            provider=bk["provider"],
            messages=messages,
            tools=bk["openai_tools"],
            model=bk["model"],
            max_tool_rounds=st.session_state.max_rounds,
        )
    except Exception as exc:  # noqa: BLE001 — surface it as a failed turn
        return None, f"{type(exc).__name__}: {exc}"
    finally:
        namespace["print"] = original_print
    result["elapsed_ms"] = int((time.perf_counter() - started) * 1000)

    for placeholder, event in zip(placeholders, result.get("tool_events") or []):
        badge, summary, _ = event_status(event)
        placeholder.markdown(f"{badge} `{event.get('tool', '?')}` · {summary}")
    if result.get("status") == "waiting_for_user":
        st.markdown("Agent cần bạn bổ sung thông tin — xem thẻ *Agent đang chờ* bên dưới.")
    elif result.get("status") == "max_tool_rounds":
        st.markdown("Hết số vòng tool cho phép trước khi agent chốt câu trả lời.")
    else:
        st.markdown(f"Xong sau {len(result.get('rounds') or [])} vòng.")
    return result, ""


def execute_confirmed(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Server side of a user-confirmed action. Only `send` with confirmed=True does anything external."""
    from tools import TOOL_FUNCTIONS

    func = TOOL_FUNCTIONS.get(tool_name)
    if func is None:
        return {"error": "unknown_tool", "message": tool_name}
    started = time.perf_counter()
    try:
        result = func(**{**args, "confirmed": True})
    except Exception as exc:  # show failures in the UI instead of crashing the page
        result = {"error": type(exc).__name__, "message": str(exc)}
    return {"result": result, "ms": int((time.perf_counter() - started) * 1000)}


# ---------------------------------------------------------------------------
# Tool events
# ---------------------------------------------------------------------------


def is_clarify_event(event: dict[str, Any]) -> bool:
    result = event.get("result")
    return event.get("tool") == "clarify" or (isinstance(result, dict) and bool(result.get("awaiting_user")))


def is_send_request(event: dict[str, Any]) -> bool:
    return event.get("tool") == "send" and isinstance(event.get("result"), dict)


def clarify_question(event: dict[str, Any]) -> str:
    result = event.get("result") or {}
    return (
        result.get("question")
        or (event.get("args") or {}).get("question")
        or "Bạn bổ sung thêm thông tin nhé."
    )


def digest_markdown(events: list[dict[str, Any]]) -> str:
    for event in events:
        result = event.get("result")
        if isinstance(result, dict) and isinstance(result.get("markdown"), str) and result["markdown"].strip():
            return result["markdown"]
    return ""


def compute_pending(row: dict[str, Any] | None) -> dict[str, Any]:
    """The user's outstanding action for the latest turn, derived from its events.

    Events are appended in order, so the *last* one decides: a send request after
    a digest is a send request, and a re-format after a send falls back to the
    digest. A turn that already sent shows "done"; a failed send falls back to
    the digest preview (never to a re-send).
    """
    if row is None:
        return {"kind": "none"}
    events = row.get("events") or []
    last_send = None
    for event in events:
        if is_send_request(event):
            last_send = event
    if last_send is not None and is_last_send(events, last_send):
        result = last_send.get("result") or {}
        if result.get("status") == "sent":
            return {"kind": "done", "result": result}
        if result.get("status") == "needs_confirmation":
            text = (last_send.get("args") or {}).get("text") or digest_markdown(events)
            return {"kind": "telegram", "text": text}
    digest = digest_markdown(events)
    if digest:
        return {"kind": "digest", "text": digest}
    return {"kind": "none"}


def is_last_send(events: list[dict[str, Any]], send_event: dict[str, Any]) -> bool:
    """True when no other tool ran after this send (a later send or format supersedes it)."""
    return events.index(send_event) == len(events) - 1


def request_prompt(text: str) -> None:
    """Queue a turn to run inside the main area on the next rerun."""
    st.session_state.pending_prompt = text
    st.rerun()


def history_of(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in rows:
        out.extend(row.get("history", []))
    return out


def turn_row(user_text: str, result: dict[str, Any] | None, error: str = "") -> dict[str, Any]:
    reply = (result or {}).get("assistant_text") or ""
    return {
        "user": user_text,
        "reply": reply,
        "status": (result or {}).get("status") or ("provider_error" if error else "answered"),
        "error": error,
        "rounds": (result or {}).get("rounds") or [],
        "events": (result or {}).get("tool_events") or [],
        "elapsed_ms": (result or {}).get("elapsed_ms", 0),
        "history": [{"role": "user", "content": user_text}, {"role": "assistant", "content": reply}],
    }


def store_row(row: dict[str, Any]) -> None:
    """Append a finished turn and clear the previous turn's send state."""
    st.session_state.turns.append(row)
    st.session_state.pop("send_outcome", None)


def run_and_store(bk: dict[str, Any], user_text: str) -> dict[str, Any]:
    """Run a queued turn under a `st.status` trace, then show it right away in the main area."""
    shown = history_of(st.session_state.turns)
    with st.status("Agent đang làm việc…", expanded=True) as status_box:
        result, error = streamed_run_turn(bk, shown, user_text)
        if result is None:
            row = turn_row(user_text, None, error)
            status_box.update(label="Lỗi provider", state="error", expanded=True)
        else:
            row = turn_row(user_text, result)
            label = STATUS_LABEL.get(row["status"], row["status"])
            status_box.update(label=f"Agent xong · {label}", state="complete", expanded=False)
    store_row(row)
    render_turn(row, len(st.session_state.turns))
    return row


def turn_state(row: dict[str, Any]) -> dict[str, Any]:
    """What the turn's outcome implies for the user's next move."""
    events = row.get("events") or []
    status = row.get("status")
    if status == "provider_error":
        return {"kind": "provider_error"}
    if status == "waiting_for_user":
        return {"kind": "waiting"}
    if status == "max_tool_rounds":
        return {"kind": "max_rounds"}
    if not events:
        return {"kind": "no_tool_use"}
    failed = [
        event for event in events
        if isinstance(event.get("result"), dict) and event["result"].get("error")
    ]
    if failed:
        return {"kind": "tool_errors", "failed": failed}
    return {"kind": "ok"}


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def result_summary(result: Any, limit: int = 300) -> str:
    if not isinstance(result, dict):
        return str(result)
    parts: list[str] = []
    for key in ("status", "error", "message", "template", "item_count"):
        if result.get(key) not in (None, ""):
            parts.append(f"{key}={result[key]}")
    for key in ("items", "results", "papers", "hits"):
        value = result.get(key)
        if isinstance(value, list):
            parts.append(f"{key}: {len(value)} mục")
    for key in ("markdown", "text", "answer"):
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            flat = " ".join(value.split())
            parts.append(f'"{flat[:140]}{"…" if len(flat) > 140 else ""}"')
    text = " · ".join(parts) or json.dumps(result, ensure_ascii=False)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def event_status(event: dict[str, Any]) -> tuple[str, str, bool]:
    """(badge, summary, failed) for one tool event."""
    result = event.get("result")
    if not isinstance(result, dict):
        return (":gray[KHÔNG CÓ KẾT QUẢ]", "tool không trả về gì", True)
    if result.get("error"):
        detail = f"{result.get('error')}: {result.get('message', '')}".strip(": ")
        return (":red[LỖI]", detail, True)
    if result.get("awaiting_user"):
        return (":orange[ĐANG HỎI LẠI]", "chờ người dùng trả lời", False)
    if result.get("status") == "needs_confirmation":
        return (":orange[CẦN DUYỆT]", "chưa gửi — chờ người dùng duyệt", False)
    return (":green[OK]", result_summary(result), False)


def render_trace(row: dict[str, Any]) -> None:
    rounds = row.get("rounds") or []
    events = row.get("events") or []
    if not events:
        return
    per_round = [r.get("tool_results", []) for r in rounds if r.get("tool_results")]
    if sum(len(group) for group in per_round) != len(events):
        per_round = [events]
    with st.expander(f"Tool trace · {len(events)} lần gọi tool", expanded=True):
        for round_index, group in enumerate(per_round, start=1):
            for event in group:
                badge, summary, failed = event_status(event)
                args = json.dumps(event.get("args") or {}, ensure_ascii=False, sort_keys=True)
                label = f"{badge} `{event.get('tool', '?')}` · {summary}"
                with st.status(label, type="step", state="error" if failed else "complete"):
                    st.code(args, language="json")
                    st.json(event.get("result") or {})
            if round_index < len(per_round):
                st.caption(f"— hết vòng {round_index}, agent đọc kết quả rồi gọi tiếp —")


def render_turn(row: dict[str, Any], index: int) -> None:
    with st.chat_message("user"):
        st.markdown(row["user"])

    with st.chat_message("assistant"):
        status = row.get("status")
        events = row.get("events") or []
        caption = (
            f"Lượt {index} · {STATUS_LABEL.get(status, status)} · "
            f"{len(events)} lần gọi tool · {row.get('elapsed_ms', 0)} ms"
        )
        if status == "provider_error":
            st.error(f"Lỗi provider: {row.get('error', '')}")
            st.caption(caption)
            return

        clarify = next((e for e in events if is_clarify_event(e)), None)
        if status == "waiting_for_user" and clarify is not None:
            st.markdown("**Agent cần hỏi lại trước khi làm tiếp**")
            st.markdown(f"> {clarify_question(clarify)}")
            st.caption("Trả lời ở thẻ *Agent đang chờ* bên dưới — câu trả lời được gửi kèm câu hỏi cũ của bạn.")
        elif row.get("reply"):
            st.markdown(row["reply"])
        if status == "max_tool_rounds":
            st.warning("Agent dùng hết số vòng tool cho phép mà chưa chốt.")

        digest = digest_markdown(events)
        if digest and status != "waiting_for_user":
            with st.expander("Bản tin markdown (từ tool format) — xem trước bản sẽ đăng", expanded=False):
                st.markdown(digest)

        for event in events:
            if is_send_request(event):
                result = event.get("result") or {}
                if result.get("status") == "sent":
                    st.success("Đã gửi bản này lên Telegram (bởi người dùng duyệt ở bước dưới).")
                elif result.get("status") == "cancelled":
                    st.caption("Lần gửi này đã bị bỏ — không có nội dung nào rời máy.")
                elif result.get("status") == "needs_confirmation":
                    st.info("Agent muốn gửi Telegram — chưa có gì được gửi. Duyệt ở thẻ bên dưới.")
                elif result.get("error") or result.get("message"):
                    st.error(f"Tool send báo lỗi: {result.get('error') or result.get('message')}")

        render_trace(row)
        st.caption(caption)


def render_clarify(clarify: dict[str, Any], row_index: int) -> None:
    result = clarify.get("result") or {}
    args = clarify.get("args") or {}
    response_type = result.get("response_type") or args.get("response_type") or "text"
    options = result.get("options") or args.get("options") or []
    question = clarify_question(clarify)
    original = st.session_state.turns[row_index]["user"]
    key = f"clarify_{row_index}"

    with st.container(border=True):
        st.markdown("**Agent đang chờ bạn trả lời**")
        st.markdown(f"> {question}")
        if response_type == "yes_no":
            choice = st.segmented_control("Trả lời", ["Có", "Không"], key=f"{key}_seg")
        elif response_type == "choice" and options:
            choice = st.segmented_control("Chọn một", options, key=f"{key}_seg")
        else:
            choice = st.text_input(
                "Câu trả lời của bạn", key=f"{key}_text", placeholder="Nhập thông tin còn thiếu…"
            )
        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.button("Gửi trả lời", type="primary", icon=":material/send:", key=f"{key}_send"):
                # The answer rides on the original question so the model sees both.
                if isinstance(choice, str) and choice.strip():
                    request_prompt(f"{original}\n\n(Trả lời câu hỏi của agent: {question}) → {choice.strip()}")
                else:
                    st.warning("Chọn hoặc nhập câu trả lời trước.")
            if st.button("Bỏ qua lượt này", key=f"{key}_skip"):
                request_prompt(
                    f"{original}\n\n(Trả lời câu hỏi của agent: {question}) → "
                    "Không có, cứ dùng mặc định hợp lý và ghi rõ giả định."
                )


def render_gate(pending: dict[str, Any]) -> bool:
    """Render confirm / cancel (and export). Returns True when the composer must wait for a decision."""
    if pending["kind"] == "none":
        return False

    outcome = st.session_state.get("send_outcome")
    if outcome:
        label, tone = SEND_OUTCOME.get(outcome.get("status"), ("không gửi được", "gray"))
        detail = outcome.get("message") or outcome.get("error") or ""
        message = f"{label.capitalize()}{(' — ' + detail) if detail else '.'}"
        if tone == "green":
            st.success(message)
        else:
            st.info(message)
        if st.button("Đóng", key="gate_ack"):
            st.session_state.pop("send_outcome", None)
            st.rerun()
        return False

    if pending["kind"] == "done":
        return False

    text = pending.get("text") or ""
    if pending["kind"] == "telegram":
        with st.container(border=True):
            st.markdown("**Duyệt trước khi gửi lên Telegram**")
            st.caption(
                "Agent chỉ đề xuất. Nội dung chỉ rời máy khi bạn bấm **Gửi lên Telegram**; "
                "tool `send` vẫn từ chối nếu thiếu cờ xác nhận."
            )
            with st.expander("Xem đúng nội dung sẽ gửi", expanded=True):
                st.markdown(text or "_(trống)_")
            with st.container(horizontal=True, horizontal_alignment="right"):
                if st.button("Không gửi", key="gate_cancel"):
                    st.session_state.send_outcome = {
                        "status": "cancelled",
                        "message": "Bản nháp vẫn còn, không có gì được gửi.",
                    }
                    st.rerun()
                if st.button(
                    "Gửi lên Telegram", type="primary", icon=":material/send:",
                    key="gate_send", disabled=not telegram_ready(),
                ):
                    st.session_state.send_outcome = execute_confirmed("send", {"text": text})["result"]
                    st.rerun()
            if not telegram_ready():
                st.warning(
                    "Thiếu `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` trong `starter_v0/.env` nên nút Gửi bị khóa. "
                    "Bot chỉ gửi được tới một chat đã nhắn cho bot, không phải kênh công khai."
                )
        return True

    with st.container(border=True):
        st.markdown("**Bản tin đã sẵn sàng**")
        with st.container(horizontal=True):
            st.download_button(
                "Xuất markdown",
                data=text,
                file_name=f"digest_{datetime.now():%Y%m%d_%H%M}.md",
                mime="text/markdown",
                icon=":material/download:",
                key="gate_download",
            )
            # A full loop of its own, so the gate can clear this turn's send state.
            if st.button(
                "Yêu cầu agent đăng lên Telegram",
                icon=":material/campaign:",
                key="gate_ask",
                help="Agent sẽ phải trả lời bằng yêu cầu gửi; bạn vẫn duyệt lần nữa.",
            ):
                request_prompt("Đăng bản tin vừa tổng hợp lên Telegram giúp mình.")
    return False


def telegram_ready() -> bool:
    return bool(os.getenv("TELEGRAM_BOT_TOKEN")) and bool(os.getenv("TELEGRAM_CHAT_ID"))


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------


def latest_row(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The newest turn. Only it can still need the user (clarify answer, send approval)."""
    return rows[-1] if rows else None


def console_tab(bk: dict[str, Any]) -> None:
    st.markdown("#### Console")
    st.caption(
        "Chạy đúng vòng lặp tool của `chat.py`. Agent có thể hỏi lại, soạn bản tin, "
        "và **chỉ đề xuất** gửi Telegram — bạn duyệt ở thẻ hiện ra sau câu trả lời."
    )

    if st.session_state.pending_prompt:
        # Samples, clarify answers and "post it to Telegram" all pass through
        # here, inside the tab, so the new turn renders in the main area.
        run_and_store(bk, st.session_state.pop("pending_prompt"))

    for index, row in enumerate(st.session_state.turns):
        render_turn(row, index + 1)

    waiting = False
    for index, row in enumerate(st.session_state.turns):
        events = row.get("events") or []
        clarify = next((e for e in events if is_clarify_event(e)), None)
        if row.get("status") == "waiting_for_user" and clarify is not None:
            render_clarify(clarify, index)
            waiting = True

    gate_open = render_gate(compute_pending(latest_row(st.session_state.turns)))

    if not st.session_state.turns:
        st.info("Chưa có lượt nào. Thử một câu hỏi mẫu ở thanh bên, hoặc hỏi trực tiếp bên dưới.")

    # A clarify answer or a send decision comes first; only then a new question.
    prompt = None if (waiting or gate_open) else st.chat_input("Hỏi agent…", submit_mode="disable")
    if prompt:
        row = run_and_store(bk, prompt)
        state = turn_state(row)
        if state["kind"] == "provider_error":
            st.error(f"Lỗi provider: {row.get('error', '')}. Kiểm tra key và model ở thanh bên.")
        elif state["kind"] == "no_tool_use":
            st.error(
                f"Model `{bk['model']}` trả lời mà không gọi tool nào. Demo này cần model có "
                "function calling (ví dụ `deepseek-v4-flash` qua VietAPI)."
            )
        elif state["kind"] == "max_rounds":
            st.warning(
                "Agent dùng hết số vòng tool cho phép mà chưa chốt — tăng **Số vòng tool tối đa** "
                "ở thanh bên (theo bài: Mục 4 `run_model_tool_loop`)."
            )


def tools_tab(bk: dict[str, Any]) -> None:
    st.markdown("#### Tool registry")
    st.caption(
        f"{len(bk['declarations'])} tool trong `artifacts/tools.yaml` — đây đúng là danh sách model nhìn thấy. "
        "Đổi tool thì phải đồng bộ cả tên trong `tools/__init__.py` và eval cases."
    )
    rows = []
    for item in bk["declarations"]:
        params = (item.get("parameters") or {}).get("properties") or {}
        rows.append(
            {
                "Tool": f"`{item.get('name', '?')}`",
                "Mô tả": item.get("description", ""),
                "Tham số": ", ".join(f"{k} ({v.get('type', '')})" for k, v in params.items()) or "—",
            }
        )
    st.dataframe(rows, hide_index=True)
    for item in bk["declarations"]:
        with st.expander(f"{item.get('name', '?')} — chi tiết tham số"):
            st.json(item.get("parameters") or {})


def eval_tab() -> None:
    st.markdown("#### Eval")
    if not RUNS_DIR.exists():
        st.warning("Chưa có thư mục `starter_v0/runs/`. Chạy `python run_eval.py …` trước.")
        return
    runs = sorted(RUNS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not runs:
        st.warning("Chưa có run nào trong `starter_v0/runs/`. Chạy `python run_eval.py …` trước.")
        return
    labels = {
        f"{p.stem} · {datetime.fromtimestamp(p.stat().st_mtime):%d/%m %H:%M}": p for p in runs
    }
    selected = st.selectbox("Run", list(labels), label_visibility="collapsed")
    data = json.loads(labels[selected].read_text(encoding="utf-8"))
    summary = data.get("summary") or {}
    st.caption(
        f"`{data.get('artifact_version')}` · {data.get('provider')} / {data.get('model')} · "
        f"suite {data.get('suite')} · phase {data.get('phase')} · {data.get('eval_cases', '')}"
    )

    def pct(value: Any) -> str:
        return "—" if value is None else f"{value * 100:.1f}%"

    cols = st.columns(4)
    cols[0].metric(
        "Case accuracy", pct(summary.get("case_accuracy")),
        help=f"{summary.get('passed_cases')}/{summary.get('total_cases')} case pass",
    )
    cols[1].metric("Tool routing", pct(summary.get("tool_routing_accuracy")))
    cols[2].metric("Arguments", pct(summary.get("argument_accuracy")))
    cols[3].metric("Multi-turn", pct(summary.get("multiturn_accuracy")))

    # `case_failure_type` is the type each case is designed to expose; `failure_type`
    # is what actually went wrong in this run (null when the case passed).
    results = data.get("results") or []
    counts: dict[str, int] = {}
    for item in results:
        kind = (item.get("result") or {}).get("failure_type")
        if kind:
            counts[kind] = counts.get(kind, 0) + 1
    st.markdown(f"**Loại lỗi thực tế ({sum(counts.values())} case fail)**")
    if counts:
        st.bar_chart(counts, x_label="Số case", y_label="Loại lỗi", horizontal=True)
    else:
        st.caption("Run này không có case fail nào được gán loại lỗi.")

    failed = [r for r in results if not (r.get("result") or {}).get("passed")]
    st.markdown(f"**Case fail ({len(failed)})**")
    if failed:
        st.dataframe(
            [
                {
                    "Case": r.get("id"),
                    "Input": (r.get("input") or "")[:110],
                    "Tool kỳ vọng": ", ".join(
                        c.get("name", "") for c in (r.get("expect") or {}).get("tool_calls", [])
                    ),
                    "Tool thực tế": ", ".join(
                        c.get("name", "") for c in ((r.get("result") or {}).get("actual_tool_calls") or [])
                    ),
                    "Loại lỗi": (r.get("result") or {}).get("failure_type")
                    or (r.get("result") or {}).get("case_failure_type")
                    or "",
                }
                for r in failed
            ],
            hide_index=True,
        )
    else:
        st.caption("Không có case fail.")
    with st.expander("Toàn bộ results của run này"):
        st.json(results)


# ---------------------------------------------------------------------------
# Shell
# ---------------------------------------------------------------------------


def init_state() -> None:
    profile = {
        "provider": os.getenv("LAB_PROVIDER", "vietapi"),
        "model": os.getenv("LAB_MODEL", "nemetron-3-ultra"),
        "version": os.getenv("LAB_VERSION", "v0"),
    }
    if profile["provider"] not in PROVIDERS:
        profile["provider"] = "openrouter"
    st.session_state.setdefault("profile", profile)
    st.session_state.setdefault("turns", [])
    st.session_state.setdefault("pending_prompt", None)
    st.session_state.setdefault("max_rounds", 4)
    st.session_state.setdefault("history_window", 5)


def sidebar(bk: dict[str, Any]) -> None:
    profile = st.session_state.profile
    with st.sidebar:
        st.markdown("### Research Agent")
        st.caption(f"Day 03 lab · {bk['model'] or 'chưa chọn model'}")

        if st.button("Cuộc trò chuyện mới", icon=":material/add_comment:", width="stretch"):
            st.session_state.turns = []
            st.session_state.pop("send_outcome", None)
            st.rerun()

        artifact = bk["artifact"]
        st.markdown(
            f":gray-badge[prompt {artifact.prompt_hash[:12]}] "
            f":gray-badge[tools {artifact.tools_hash[:12]}]"
        )
        st.caption(f"`{artifact.artifact_version}`")

        st.markdown("**Hỏi thử**")
        for case_id, question in SAMPLES:
            if st.button(question, key=f"sample_{case_id}", width="stretch", help=f"Case {case_id}"):
                request_prompt(question)

        with st.expander("Cấu hình chạy"):
            st.session_state.max_rounds = st.slider(
                "Số vòng tool tối đa", 1, 8, st.session_state.max_rounds
            )
            st.session_state.history_window = st.slider(
                "Cửa sổ lịch sử (cặp lượt)", 0, 10, st.session_state.history_window
            )
            st.caption(
                "temperature 0.0 · model, provider và nhãn version lấy từ biến môi trường "
                "`LAB_PROVIDER`, `LAB_MODEL`, `LAB_VERSION`."
            )

        with st.expander("Provider & artifact"):
            with st.form("session_form", border=False):
                provider = st.selectbox("Provider", PROVIDERS, index=PROVIDERS.index(profile["provider"]))
                model = st.text_input("Model (trống = mặc định provider)", value=profile["model"])
                version = st.text_input("Nhãn version", value=profile["version"])
                if st.form_submit_button("Áp dụng và bắt đầu cuộc mới", icon=":material/restart_alt:"):
                    st.session_state.profile = {
                        "provider": provider,
                        "model": model.strip(),
                        "version": version.strip() or "v0",
                    }
                    st.session_state.turns = []
                    st.rerun()
            if st.button("Tải lại prompt & tools từ đĩa", icon=":material/refresh:"):
                load_backend.clear()
                st.rerun()

        st.divider()
        st.caption(
            "**An toàn:** gửi Telegram chỉ sau khi người dùng duyệt; tool `send` còn từ chối nếu thiếu cờ xác nhận. "
            "Dữ liệu lấy từ web được coi là không đáng tin — chỉ dùng làm dữ liệu, không chạy theo chỉ dẫn trong đó."
        )
        if not telegram_ready():
            st.caption("Telegram chưa cấu hình (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`).")


def main() -> None:
    init_state()
    bk = backend(st.session_state.profile)
    sidebar(bk)
    console, tools_view, eval_view = st.tabs(["Console", "Tool registry", "Eval"])
    with console:
        console_tab(bk)
    with tools_view:
        tools_tab(bk)
    with eval_view:
        eval_tab()


main()
