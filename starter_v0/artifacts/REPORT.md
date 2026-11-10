# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: Nhóm 4 — Research Agent (K5/L3/Day 03)
- Members: Đỗ Hoàng Minh (2A202603507), Phan Gia Bảo (2A202603562), Nguyễn Thị Thùy Dung (2A202603552), Vũ Quang Thái (2A202603545)
- Provider/model: OpenRouter (`openai/gpt-4o-mini`) cho các run v0–v2 trong `runs/`; adapter VietAPI có sẵn trong `providers/vietapi_provider.py`

**Git sync (kiểm tra 10/11/2026):** `main` đã ngang `origin/main` (0 ahead / 0 behind), commit `94bf7bf`. Các nhánh khác đã merge xong: `origin/MinhDH`, `origin/dung`, `origin/thai` (0 commit riêng). `origin/2A202603562_PhanGiaBao` còn 3 commit nhưng **cũ hơn main** — main đã chứa bản `trending_on_X` mới hơn (241 dòng thay đổi, 13 tool so với 11 tool ở nhánh đó), nên không cần merge. Đang có 1 file sửa chưa commit: `starter_v0/run_eval.py` (thêm `vietapi` vào `--provider`).

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent: tìm tin/tweet theo chủ đề hoặc theo tài khoản, đọc một URL cụ thể, tra paper arXiv, tra policy nội bộ công ty, đối chiếu nhiều nguồn, xếp hạng bài theo engagement, và gửi digest lên Telegram — nhưng **chỉ gửi sau khi người dùng xác nhận đúng nội dung**.

**Link dùng thử (deploy):**

> Chưa deploy public. Chạy local:
>
> ```bash
> cd starter_v0
> streamlit run app.py        # UI demo (chat + tool trace + eval dashboard)
> ```
>
> URL: _(cần điền sau khi deploy Cloudflare Tunnel / Streamlit Cloud)_

## A2. Tool agent có

> 13 tool trong `artifacts/tools.yaml`; 3 tool nhóm tự thêm (`rank_by_engagement`, `compare_sources`, `trending_on_X`).

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại người dùng khi thiếu thông tin (`text`) hoặc xin xác nhận trước khi gửi/đăng (`yes_no`) | không |
| timeline | lấy bài đăng gần đây **của một tài khoản** (`screenname`, không có `@`); map Elon Musk→`elonmusk`, Sam Altman→`sama` | không |
| social_search | tìm bài **về một chủ đề** trên X/Twitter (`search_type`: Latest/Top) | không |
| lookup | tìm web (`topic`: general/news, `timeframe`: day/week/month/year); query chỉ chứa từ khóa chủ đề | không |
| fetch | đọc nội dung text của **một URL đã biết**; không tự đoán URL | không |
| format | render các item đã có thành digest markdown (brief/sections/bullets/thread/daily_ai_vn) | không |
| rank_by_engagement | xếp hạng các bài **đã có** theo favorites/retweets/views; không tìm lại bài | **có** |
| send | gửi text lên Telegram; chỉ hợp lệ khi `confirmed=true` sau khi người dùng duyệt đúng nội dung | không (bonus có sẵn) |
| policy | tìm trong `company_policy/*.md` (5 nhóm: ai_research, source_citation, data_privacy, external_publishing, tool_usage) | không |
| papers | tìm paper trên arXiv (`sort_by`: relevance/lastUpdatedDate/submittedDate) | không |
| paper_text | tải text một paper arXiv đã xác định (ID hoặc URL) | không |
| compare_sources | so sánh ≥ 2 nguồn **đã thu thập** để tìm chủ đề chung + từ khóa riêng; không dùng để tìm nguồn mới | **có** |
| trending_on_X | lấy hashtag/chủ đề đang trending trên X theo khu vực; **không cần từ khóa**, mặc định Việt Nam | **có** |

## A3. Câu hỏi mẫu để thử

> Lấy từ các case đã đưa vào eval (`data/eval_base.json`, `data/eval_group.json`).

1. `Tweet mới nhất của Sam Altman là gì?` — kỳ vọng: `timeline(screenname="sama", limit=1)`.
2. `Tin tức AI hôm nay có gì nổi bật?` — kỳ vọng: `lookup(query="AI", topic="news", timeframe="day")`, **không** kèm `social_search`.
3. `Nguồn 1: AI giúp doanh nghiệp tự động hóa quy trình... Nguồn 2: Ứng dụng AI giúp cải thiện hiệu quả... So sánh hai nguồn trên về điểm chung và từ khóa khác biệt.` — kỳ vọng: `compare_sources`, không gọi `lookup`/`fetch`.
4. `Trên X đang có gì hot vậy?` — kỳ vọng: `trending_on_X(location="vietnam")`, không hỏi lại khu vực.
5. `Đăng bản tin này lên Telegram giúp mình` — kỳ vọng: `clarify(response_type="yes_no")` trước, **không** gọi `send` ngay.

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Nguồn: `runs/v0_B_base_openrouter_20261110T142437354427.json`, `runs/v1_B_base_openrouter_20261110T123307990458.json`, `runs/v2_B_base_openrouter_20261110T161146394727.json` (suite `base`, 20 case, model `openai/gpt-4o-mini`).

> **Thiếu run v3.** Hiện chưa có `runs/v3_*.json` cho artifact hiện tại (13 tool, prompt hiện hành) — đã thử chạy nhưng dừng lại. README yêu cầu `version_log.csv` có ít nhất v0–v3, nên cần chạy:
>
> ```bash
> python run_eval.py --provider openrouter --version v3 --suite base --eval-cases data/eval_base.json
> ```
>
> rồi thêm 1 dòng v3 vào bảng dưới và ghi lại vào `artifacts/version_log.csv` (file này hiện **chỉ có header**, chưa có dòng nào).


| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline: `artifacts/system_prompt.md` (prompt hash `a7684d275238`) + tool declarations gốc của starter (`5b22a2476d41`) | Đo mức routing mặc định trước khi siết prompt/tool description | — | 0.70 | `v0_...T142437...json` |
| v1 | chỉ `artifacts/system_prompt.md` (hash `7ebee5b27b91`), giữ nguyên tools starter (`5b22a2476d41`) | Bổ sung luật trong prompt (không đoán tài khoản/URL, từ chối out-of-scope, hành vi clarify) sẽ sửa các lỗi "tự bịa" — R08/R10/R11/R14 — mà không cần sửa tool declaration | 0.70 | 0.75 | `v1_...T123307...json` |
| v2 | `artifacts/system_prompt.md` (hash `653ee6f896f6`, = commit `5d29aed`) + `artifacts/tools.yaml` (hash `f4dee982066f`, = commit `5d29aed`: 11 tool, thêm `compare_sources`, viết lại description) | Đưa luật "khi nào dùng / khi nào KHÔNG dùng" vào description của từng tool sẽ sửa lỗi gọi thiếu/thừa tool (R13, R02/R03/M02/M06) | 0.75 | 0.75 | `v2_...T161146...json` |

Bảng chi tiết theo metric trong `summary` của từng run:

| Metric | v0 | v1 | v2 |
|---|---:|---:|---:|
| case_accuracy | 0.70 | 0.75 | 0.75 |
| tool_routing_accuracy | 0.75 | 0.90 | 0.80 |
| argument_accuracy | 0.70 | 0.75 | 0.75 |
| multiturn_accuracy | 1.00 | 0.8333 | 0.6667 |
| passed_cases / 20 | 14 | 15 | 15 |
| observed_mismatch_counts | unexpected 2, missing 3, wrong arg 1 | wrong arg 3, missing 2 | extra 4, wrong arg 1 |

Ghi chú bằng chứng (đọc từ `run.prompt_hash` / `run.tools_hash`, đối chiếu `git cat-file`):

- v0 và v1 **dùng chung** một bản `tools.yaml` (starter, mô tả còn mơ hồ) → mọi thay đổi của v1 nằm ở prompt.
- Bản prompt của v0 (`a7684d275238`) và v1 (`7ebee5b27b91`) **không còn trong git history** (chỉ có hash trong run JSON), nên cột "hypothesis" của v0/v1 là suy ra từ chênh lệch case pass/fail — **nhóm cần xác nhận lại nội dung đã sửa**.
- Bản v2 truy được chính xác: cả `prompt_hash` `653ee6f896f6` và `tools_hash` `f4dee982066f` đều khớp ở commit `5d29aed` ("Add tool compare_source") — bản tools đó có 11 tool (starter 10 + `compare_sources`), tức v2 **chưa** có `rank_by_engagement`/`trending_on_X` (2 tool này thêm sau, ở commit `1f6eda3` và `d4a4193`).
- v0/v1 dùng tools gốc 10 tool (hash `5b22a2476d41`, khớp commit `c25633d`); khác biệt duy nhất giữa v0 và v1 là prompt.
- ⚠️ Mốc thời gian trong file run: v1 `generated_at = 12:33`, v0 `= 14:24` → lần chạy v0 diễn ra **sau** v1, dù nhãn version là v0. Bảng B1 so sánh theo **nhãn version** (v0 = baseline artifact gốc), không theo thứ tự đồng hồ; khi trích dẫn "before → after" cần nói rõ điều này.
- 3 run đều có `provider_error_cases: 0` → mọi case đều đo được; lỗi HTTP của tool (xem B2) **không** bị tính là lỗi provider.

## B2. Failure Analysis

Trích từ `results[*].result.failures` (cột "Failure" là `failure_type` do eval gán, "Mismatch" là `observed_mismatch`). Số liệu dưới đây là của run được ghi rõ ở đầu mỗi nhóm.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R12_confirm_before_send (v0) | wrong_boundary | `send(text="Bản tin này")` | Tự gửi khi chưa có nội dung và chưa được duyệt → "missing clarify yes_no" + "extra send" | Prompt: yêu cầu gửi/đăng chưa xác nhận phải `clarify(response_type="yes_no")` **trước**; `confirm=true` chỉ sau khi user duyệt đúng text (§Clarification, §send) |
| R12_confirm_before_send (v1) | wrong_boundary | `clarify(response_type="text", question="Bạn muốn gửi nội dung gì...")` | Đúng ý "hỏi lại" nhưng sai loại câu hỏi: `text` thay vì `yes_no` — nhánh hỏi nội dung lấn nhánh xác nhận | Prompt: đặt rõ thứ tự ưu tiên — xác nhận ý định publish (`yes_no`) trước, rồi mới hỏi nội dung; sau đó vẫn phải show draft + xác nhận lần 2 |
| R12_confirm_before_send (v2) | wrong_boundary | `clarify(response_type="text", question="Bạn có thể cung cấp nội dung...")` | Lặp lại y hệt v1 dù đã viết lại tool description → luật boundary phải nằm trong **cả** prompt, không chỉ description | Thêm rule "A new, not-yet-confirmed request to send/publish takes precedence over the generic missing-information rule" trong prompt (hiện đang có, dòng 26–31) |
| R03_web_news_routing (v1) | wrong_tool | `lookup(query="tin tức AI", topic="news", timeframe="day")` | Đúng tool nhưng query dính từ loại tin | Prompt/description `lookup.query`: chỉ chứa từ khóa chủ đề, bỏ `tin tức`/`news`/`hôm nay` — thông tin loại tin đã nằm ở `topic`/`timeframe` |
| R03_web_news_routing (v2) | wrong_tool | `lookup(...) + social_search(query="AI")` | Đúng `lookup` nhưng **gọi thêm** `social_search` khi user không nhắc social | Description `social_search`: chỉ dùng khi yêu cầu social/tweet rõ ràng; "tin hôm nay" là web news; không tự gọi kèm `lookup` để "bổ sung nguồn" |
| R02_search_tweets_routing (v2) | wrong_tool | `social_search(query="GPT-5") + lookup(query="GPT-5")` | Hỏi "trên Twitter" → đúng `social_search` nhưng kèm `lookup` dư | Cùng fix trên: luật "chỉ gọi cả hai khi user yêu cầu cả hai nguồn" |
| R13_parallel_web_and_tweets (v0) | wrong_tool (args) | `lookup(query="AI news", timeframe="day")` + `social_search(query="AI")` | Đúng 2 tool nhưng `query="AI news"` và **thiếu `topic="news"`** | Description `lookup`: query chỉ từ khóa; `topic=news` bắt buộc cho tin tức; `timeframe=day` cho hôm nay |
| R13_parallel_web_and_tweets (v1) | wrong_tool (args) | `lookup(query="tin AI", ...) + social_search(...)` | Lặp lỗi query, đã có `topic` | Cùng fix query-subject-only; case này **pass ở v2** → fix có tác dụng |
| R05_limit_arg (v1) | wrong_arg_value | `clarify(response_type="text", question="...tài khoản nào của Elon Musk?")` | Có mapping tên→handle trong prompt nhưng bị rule "không đoán account" đè lên → hạ route (routing=False) | Prompt: mapping `Elon Musk→elonmusk`, `Sam Altman→sama` được phép dùng trực tiếp; "không đoán" chỉ áp dụng khi user **không nêu ai** |
| M02_carryover_timeframe (v1) | wrong_arg_value | `social_search(query="robotics")` | "Chỉ tìm robotics thôi, vẫn là tin hôm nay" → đổi cả nguồn sang social, mất `topic=news`, `timeframe=day` | Prompt: carry-over mọi tham số user không sửa; "chỉ tìm X" chỉ thay subject, không đổi nguồn/thời gian |
| M02_carryover_timeframe (v2) | wrong_arg_value | `lookup(robotics, news, day) + social_search(robotics)` | Đã carry đúng nhưng thêm `social_search` dư | Luật không gọi kèm social_search trong description (xem R03-v2) |
| M06_switch_tool (v2) | wrong_tool | `lookup(OpenAI, news, week) + social_search(OpenAI)` | User đã nói "Bỏ Twitter, chuyển sang tìm trên web" → vẫn còn gọi Twitter | Description `social_search`: KHÔNG gọi sau khi user bỏ Twitter/chuyển sang web; prompt: latest correction override giá trị cũ |
| R08_out_of_scope (v0) | out_of_scope | `send(text="Nguyên hàm của x^2 là ...")` | Trả lời toán bằng cách "gửi" — vi phạm cả scope lẫn semantics của `send` | Prompt: câu ngoài phạm vi → trả lời trực tiếp/định hướng, **không** gọi tool; `send` chỉ là hành động gửi đã duyệt |
| R14_out_of_scope_coding (v0) | out_of_scope | `send(text="def fibonacci(n): ...")` | Như trên | Như trên (v1 đã pass, v2 giữ pass) |
| R10_missing_handle (v0) | missing_info | `timeline(screenname="sama", limit=5)` | "Tóm tắt 5 tweet mới nhất" không nêu ai → tự chọn Sam Altman | Prompt: không đoán account; hỏi `clarify(response_type="text")`; mapping chỉ dùng khi user **gọi tên** |
| R11_missing_url (v0) | missing_info | `fetch(url="https://example.com/article")` | "Bài viết này" không có link → tự bịa URL | Prompt: không bao giờ tự đoán URL; `clarify` xin link; `fetch` chỉ nhận URL nguyên văn từ user/kết quả tool |

Ghi chú vận hành (không phải lỗi routing): trong cả 3 run, tool X/Twitter trả `HTTPError 403` (timeline 6/4/5 lần; social_search 3/4/6 lần). Eval vẫn chấm đúng vì chỉ so tool calls/args, nhưng **nội dung trả về rỗng** → không dùng được để đánh giá chất lượng câu trả lời. Khi kiểm tra lại thủ công (10/11/2026) cùng endpoint trả `200`, nên khả năng cao là quota/key của RapidAPI đổi giữa các lần chạy — cần ghi rõ trong báo cáo để không quy lỗi cho agent.

## B3. Team Eval Cases

Nguồn: `data/eval_group.json` (`dataset_id: day04_v2_research_group`, 10 case). Cột **Result** để trống vì group eval **chưa chạy** trên suite này — sẽ điền từ run `--suite group --eval-cases data/eval_group.json`.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_compare_three_provided_sources | 3 nguồn đã cho trong hội thoại + yêu cầu đối chiếu | `compare_sources`, không tìm nguồn mới | _(chờ chạy)_ |
| G02_compare_user_provided_sources | 2 nguồn tiếng Việt do user cung cấp | `compare_sources`, không `lookup`/`fetch` | _(chờ chạy)_ |
| G03_search_not_compare | Chỉ yêu cầu **tìm** nguồn mới, chưa yêu cầu so sánh | `lookup(query="ứng dụng AI trong giáo dục đại học")` | _(chờ chạy)_ |
| G04_compare_missing_sources | Yêu cầu so sánh nhưng chưa có nguồn | `clarify(response_type="text")`, không tự tạo nguồn | _(chờ chạy)_ |
| G05_fetch_before_comparison | Có URL cụ thể, chỉ mới 1 nguồn | `fetch(url="https://openai.com/blog/gpt-5")`, chưa đủ để `compare_sources` | _(chờ chạy)_ |
| G06_summary_not_comparison | Có nội dung, chỉ yêu cầu tóm tắt 3 ý | Không gọi tool, trả lời trực tiếp | _(chờ chạy)_ |
| G07_explain_tool_capability | Hỏi `compare_sources` khác `lookup` thế nào | Không gọi tool, giải thích trực tiếp | _(chờ chạy)_ |
| G08_out_of_scope_math | So sánh 2 biểu thức đại số (parse trap với `compare_sources`) | Không gọi tool research, từ chối/định hướng | _(chờ chạy)_ |
| G09_rank_existing_posts_by_views | 2 bài đã có kèm `metrics.views` | `rank_by_engagement(metric="views")`, không tìm lại bài | _(chờ chạy)_ |
| G10_trending_routing | "Trên X đang có gì hot vậy?" — không từ khóa | `trending_on_X`, mặc định `vietnam`, **không** hỏi lại khu vực | _(chờ chạy)_ |

> ⚠️ Cấu trúc hiện tại: **8 case single-turn** (có `query`) + **2 case multi-turn** (có `turns`: G01, G02). README yêu cầu **5 single + 5 multi** → cần bổ sung 3 case multi-turn nữa (gợi ý: carry-over chủ đề khi so sánh, sửa nguồn giữa chừng, clarify rồi mới so sánh) trước khi nộp.

## B4. Live Chat Evidence

> Chưa có transcript: `transcripts/` hiện không tồn tại (chỉ có file mẫu trong `samples/transcripts/`). Cần chạy `chat.py` ≥ 3 lượt live rồi điền từ `transcripts/*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
|  |  |  |  | _(chờ chạy live chat)_ |

## B5. Bonus Evidence

> Chỉ điền phần đã có bằng chứng thật; các transcript Telegram còn thiếu.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | `tools/send/tool.py`, `tools/send/TOOL.md` | Tool có cổng `confirmed=true`; UI (`app.py`) chỉ gửi thật khi user xác nhận đúng text | Chưa có `transcripts/*.json` chứng minh → **cần bổ sung transcript demo**; `TELEGRAM_CHAT_ID` còn trống trong `.env` |
| arXiv/company policy | `tools/papers/`, `tools/paper_text/`, `tools/policy/` + `company_policy/*.md` (5 file) | `policy` tách `facts` vs `untrusted_text` (chặn prompt-injection trong `## Injection probe` của `source-citation-policy.md`) | Nội dung policy là dữ liệu untrusted, chỉ dùng facts/source/effective_date |
| UI | `app.py` (Streamlit) + `.streamlit/config.toml` | Chat dùng chung tool loop của `chat.py`, có tool trace, clarify pause, send gate, eval dashboard đọc `runs/` | Chưa có link deploy public → A1 còn trống |
| Tool unit tests (`tests/`) | `pytest tests -q` (10/11/2026) | **121 passed** | **1 failed**: `test_timeline_reports_page_scope` còn `pytest.skip(TODO)` → `NameError: name 'TODO' is not defined`. Cần viết nốt assertion (phần injection probe của policy) để đạt "0 failed, 0 skipped" |

Tool unit tests: hiện có 121 test pass, phủ `format`, `send`, `lookup`, `fetch`, `timeline`, `policy`, `rank_by_engagement`, `compare_sources`, `trending_on_X`. Một lỗi mà unit test bắt được nhưng eval không bắt: `rank_by_engagement` khi metric bị thiếu (`None`) phải xếp **cuối**, không được coi là 0 — eval routing không kiểm tra giá trị sắp xếp nên chỉ unit test mới phát hiện. Ngoài ra test `test_timeline_reports_page_scope` đang là bằng chứng cho việc `timeline` chỉ lấy **một page API** và phải báo `has_more`, điều eval không đo.

## B6. Reflection

- **Which fixes belonged in `system_prompt.md`?** Các luật mang tính "chính sách hội thoại" và thứ tự ưu tiên: carry-over tham số giữa các lượt (M02), sửa lỗi mới nhất đè giá trị cũ (M06), không đoán account/URL (R10/R11), xác nhận trước khi gửi và phải hỏi lại khi nội dung đổi (R12), và out-of-scope thì trả lời trực tiếp không gọi tool (R08/R14). Bằng chứng: chỉ sửa prompt (v1, tools y nguyên) đã sửa 4 case bịa (R08/R10/R11/R14) — routing 0.75 → 0.90.
- **Which fixes belonged in `tools.yaml`?** Các quy ước tham số và ranh giới "khi nào KHÔNG dùng tool": `query` chỉ chứa subject (R03/R13), `topic`/`timeframe`/`search_type` là nơi chứa loại tin và thời gian, `social_search` không được gọi kèm `lookup` và không dùng sau khi user bỏ Twitter (R02/R03/M02/M06), `fetch` chỉ nhận URL nguyên văn. Bằng chứng: v2 thêm description chi tiết → R13 chuyển FAIL→PASS.
- **Which failure needed manual review instead of automatic grading?** (1) R12 — eval chỉ so `response_type` của `clarify`, nên cả câu hỏi "yes_no hợp lý" lẫn "hỏi nội dung" đều có thể trượt dù hành vi an toàn đã đúng; cần người đọc transcript để chấm "có tự gửi hay không". (2) Các case mà tool trả `HTTPError 403` — eval vẫn PASS vì chỉ chấm routing, nhưng agent không có dữ liệu thật để trả lời, nên chất lượng câu trả lời phải xem tay. (3) Câu trả lời có trích nguồn đúng/không đúng — eval không chấm.
- **What would you improve next?** (a) Chạy `eval_group.json` + bổ sung đủ 5 case multi-turn; (b) làm nốt test `test_timeline_reports_page_scope` để `pytest` về 0 failed/0 skipped; (c) thống nhất một chỗ cho luật publish-boundary (hiện lặp ở prompt + description `clarify` + description `send`, model vẫn trượt R12 cả 3 version → thử cách rút gọn còn một nguồn duy nhất); (d) chạy lại v3 với `gpt-4o-mini` rồi mới so với local model, vì hiện chưa có run v3 và chưa cài Ollama nên B7 để trống; (e) ghi `artifacts/version_log.csv` (đang trống header) để truy vết đúng "changed artifact → hypothesis → metric" thay vì suy từ hash.

## B7. Small Local Model Challenge (bonus)

> Chưa thực hiện: máy chưa cài Ollama (`ollama` không có trong PATH) và chưa có run local nào. Để trống, sẽ điền nếu nhóm chạy challenge.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3 | (cloud) | v3 |  |  |  |  | _(chưa chạy)_ |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v4-local |  |  |  |  |  |  |  |
| v5-local |  |  |  |  |  |  |  |

Lỗi đặc thù của model nhỏ (đếm từ run JSON):

| Failure Pattern | Count | Example Case | Fix Tried | Helped? |
|---|---|---|---|---|
| wrong / hallucinated tool |  |  |  |  |
| invalid JSON args (`_invalid_json_arguments`) |  |  |  |  |
| no tool call / answered directly |  |  |  |  |
| missed `clarify` |  |  |  |  |
| repeated / unnecessary calls |  |  |  |  |

- Cái gì giúp model nhỏ gọi tool đúng hơn nhất? Bằng chứng?
- Bản prompt tối ưu cho local chạy trên model cloud thì sao?
- Khi nào nhóm sẽ chọn model local thay vì cloud cho agent này?
