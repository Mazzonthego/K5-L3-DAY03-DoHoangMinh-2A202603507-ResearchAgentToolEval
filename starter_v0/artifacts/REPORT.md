# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: Nhóm 4 — Research Agent (K5/L3/Day 03)
- Members: Đỗ Hoàng Minh (2A202603507), Phan Gia Bảo (2A202603562), Nguyễn Thị Thùy Dung (2A202603552), Vũ Quang Thái (2A202603545)
- Provider/model: OpenRouter (`openai/gpt-4o-mini`) cho các run v0–v2 trong `runs/`; adapter VietAPI có sẵn trong `providers/vietapi_provider.py`

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent: tìm tin/tweet theo chủ đề hoặc theo tài khoản, đọc một URL cụ thể, tra paper arXiv, tra policy nội bộ công ty, đối chiếu nhiều nguồn, xếp hạng bài theo engagement, và gửi digest lên Telegram — nhưng **chỉ gửi sau khi người dùng xác nhận đúng nội dung**.

**Link dùng thử (deploy):**

> Nhóm chỉ chạy local, **không deploy public**.
>
> ```bash
> cd starter_v0
> streamlit run app.py        # UI demo (chat + tool trace + eval dashboard)
> ```

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

Quy ước: mỗi version được chạy nhiều lần trong ngày; bảng dưới lấy **lần chạy cuối cùng của mỗi version**. Các bước sửa chi tiết nằm trong git log/commit (liệt kê ở cột "Changed Artifact").

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | `artifacts/system_prompt.md` (prompt hash `a7684d275238`) + tool declarations gốc của starter (`5b22a2476d41`, mô tả còn mơ hồ độ dài 1 câu) | Đo mức routing mặc định trước khi siết prompt/tool description | — | 0.70 | `runs/v0_B_base_openrouter_20261110T142437354427.json` |
| v1 | chỉ `artifacts/system_prompt.md` (hash `7ebee5b27b91`), tools giữ nguyên (`5b22a2476d41`) | Bổ sung luật trong prompt (không đoán tài khoản/URL, từ chối out-of-scope, hành vi clarify) sẽ sửa các lỗi "tự bịa" — R08/R10/R11/R14 — mà không cần sửa tool declaration | 0.70 | 0.75 | `runs/v1_B_base_openrouter_20261110T123307990458.json` |
| v2 | `artifacts/system_prompt.md` (hash `653ee6f896f6`, = commit `5d29aed`) + `artifacts/tools.yaml` (hash `f4dee982066f`, = commit `5d29aed`: 11 tool, thêm `compare_sources`, viết lại description theo "khi nào dùng / khi nào KHÔNG dùng") | Đưa luật routing vào description của từng tool sẽ sửa lỗi gọi thiếu/thừa tool (R13, R02/R03/M02/M06) | 0.75 | 0.75 | `runs/v2_B_base_openrouter_20261110T161146394727.json` |
| v3 | `artifacts/system_prompt.md` (hash `564fdeb7c61b`) + `artifacts/tools.yaml` (hash `f9eb0765b0c2`, 13 tool đủ `rank_by_engagement`, `compare_sources`, `trending_on_X`) | Kỳ vọng: giữ điểm routing của v2 và bổ sung 3 tool mới vào phạm vi eval | 0.75 | **chưa có run** | — |

Bảng chi tiết theo `summary` của 3 run v0–v2:

| Metric | v0 | v1 | v2 |
|---|---:|---:|---:|
| case_accuracy | 0.70 | 0.75 | 0.75 |
| tool_routing_accuracy | 0.75 | 0.90 | 0.80 |
| argument_accuracy | 0.70 | 0.75 | 0.75 |
| multiturn_accuracy | 1.00 | 0.8333 | 0.6667 |
| passed_cases / 20 | 14 | 15 | 15 |
| observed_mismatch_counts | unexpected 2, missing 3, wrong arg 1 | wrong arg 3, missing 2 | extra 4, wrong arg 1 |

**Vì sao v3 chưa có kết quả:** do giới hạn tài nguyên tính toán (thời gian chạy eval và hạn mức API provider), nhóm chưa chạy được base eval cho artifact cuối (13 tool). Bảng trên vì vậy dừng ở v2; khi có điều kiện, lệnh cần chạy là:

```bash
python run_eval.py --provider openrouter --version v3 --suite base --eval-cases data/eval_base.json
```

**Các lần chạy trước đó (không dùng trong bảng, chỉ để truy vết):** mỗi version từng được chạy sớm hơn trong ngày với artifact khác nhau:

| Run (giờ tạo) | Artifact | case_accuracy | Trạng thái |
|---|---|---:|---|
| v1 `11:11` | `v1+p02277ac4f327+t5b22a2476d41` | 0.75 | archive trong git (`e96b0d0`) |
| v0 `11:45` | `v0+peb1c8179815b+t5b22a2476d41` | 0.60 | archive trong git (`15c6cd5`) |
| v1 `12:06` | `v1+pfb8d0f06c6a6+td82c67e4ff82` | 0.75 | archive trong git (`15c6cd5`) |
| v2 `12:10` | `v2+p184cb9372e9f+t9e7f1000f699` | 0.95 | archive trong git (`15c6cd5`) |
| v1 `12:33` | `v1+p7ebee5b27b91+t5b22a2476d41` | 0.75 | **dùng trong bảng** |
| v0 `14:24` | `v0+pa7684d275238+t5b22a2476d41` | 0.70 | **dùng trong bảng** |
| v2 `16:11` | `v2+p653ee6f896f6+tf4dee982066f` | 0.75 | **dùng trong bảng** |

Ghi chú bằng chứng (đọc từ `run.prompt_hash` / `run.tools_hash`, đối chiếu `git cat-file`):

- v0 và v1 dùng **chung** một bản `tools.yaml` (`5b22a2476d41`, khớp commit `c25633d`) → mọi thay đổi của v1 nằm ở prompt.
- v2 truy được chính xác: prompt `653ee6f896f6` và tools `f4dee982066f` đều khớp commit `5d29aed` ("Add tool compare_source"), bản 11 tool. Tức v2 **chưa** có `rank_by_engagement` (thêm ở `1f6eda3`) và `trending_on_X` (thêm ở `d4a4193`).
- `artifacts/version_log.csv` hiện **mới có header**, chưa có dòng nào. Đây là thiếu sót về quy trình (xem B6 — bài học "ghi version_log ngay từ v0"); bảng B1 ở trên được dựng lại từ run JSON + git history thay cho file đó.
- Cả 3 run đều có `provider_error_cases: 0` → mọi case đều đo được; lỗi HTTP của tool (xem B2) **không** bị tính là lỗi provider.

## B2. Failure Analysis

Trích từ `results[*].result.failures`. Cột "Failure Type" là `failure_type` eval gán, lỗi cụ thể nằm ở "What Failed".

| Case ID (version) | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R08_out_of_scope (v0) | out_of_scope | `send(text="Nguyên hàm của x^2 là ...")` | Trả lời toán bằng cách "gửi" — vi phạm cả scope lẫn semantics của `send` | Prompt: câu ngoài phạm vi → trả lời trực tiếp/định hướng, **không** gọi tool; `send` chỉ là hành động gửi đã duyệt |
| R14_out_of_scope_coding (v0) | out_of_scope | `send(text="def fibonacci(n): ...")` | Như trên | Như trên (v1 đã pass, v2 giữ pass) |
| R10_missing_handle (v0) | missing_info | `timeline(screenname="sama", limit=5)` | "Tóm tắt 5 tweet mới nhất" không nêu ai → tự chọn Sam Altman | Prompt: không đoán account; hỏi `clarify(response_type="text")`; mapping chỉ dùng khi user **gọi tên** |
| R11_missing_url (v0) | missing_info | `fetch(url="https://example.com/article")` | "Bài viết này" không có link → tự bịa URL | Prompt: không bao giờ tự đoán URL; `clarify` xin link; `fetch` chỉ nhận URL nguyên văn từ user/kết quả tool |
| R12_confirm_before_send (v0) | wrong_boundary | `send(text="Bản tin này")` | Tự gửi khi chưa có nội dung và chưa được duyệt → "missing clarify yes_no" + "extra send" | Prompt: yêu cầu gửi/đăng chưa xác nhận phải `clarify(response_type="yes_no")` **trước**; `confirmed=true` chỉ sau khi user duyệt đúng text |
| R12_confirm_before_send (v1) | wrong_boundary | `clarify(response_type="text", question="Bạn muốn gửi nội dung gì...")` | Đúng ý "hỏi lại" nhưng sai loại câu hỏi: `text` thay vì `yes_no` — nhánh hỏi nội dung lấn nhánh xác nhận | Prompt: xác nhận ý định publish (`yes_no`) trước, rồi mới hỏi nội dung; sau đó vẫn phải show draft + xác nhận lần 2 |
| R12_confirm_before_send (v2) | wrong_boundary | `clarify(response_type="text", question="Bạn có thể cung cấp nội dung...")` | Lặp lại như v1 dù đã viết lại tool description → luật boundary phải nằm trong **prompt**, không chỉ description | Thêm rule "A new, not-yet-confirmed request to send/publish takes precedence..." trong prompt |
| R03_web_news_routing (v1) | wrong_tool | `lookup(query="tin tức AI", topic="news", timeframe="day")` | Đúng tool nhưng query dính từ loại tin | `lookup.query`: chỉ chứa từ khóa chủ đề, bỏ `tin tức`/`news`/`hôm nay` — loại tin ở `topic`, thời gian ở `timeframe` |
| R03_web_news_routing (v2) | wrong_tool | `lookup(...) + social_search(query="AI")` | Đúng `lookup` nhưng **gọi thêm** `social_search` khi user không nhắc social | Description `social_search`: chỉ dùng khi yêu cầu social/tweet rõ ràng; "tin hôm nay" là web news |
| R02_search_tweets_routing (v2) | wrong_tool | `social_search(query="GPT-5") + lookup(query="GPT-5")` | Hỏi "trên Twitter" → đúng `social_search` nhưng kèm `lookup` dư | Luật "chỉ gọi cả hai khi user yêu cầu cả hai nguồn" |
| R13_parallel_web_and_tweets (v0) | wrong_tool (args) | `lookup(query="AI news", timeframe="day")` + `social_search(query="AI")` | Đúng 2 tool nhưng `query="AI news"` và **thiếu `topic="news"`** | Description `lookup`: query chỉ từ khóa; `topic=news` bắt buộc cho tin tức |
| R13_parallel_web_and_tweets (v1) | wrong_tool (args) | `lookup(query="tin AI", ...) + social_search(...)` | Lặp lỗi query, đã có `topic` | Cùng fix query-subject-only; case này **pass ở v2** → fix có tác dụng |
| R05_limit_arg (v1) | wrong_arg_value | `clarify(response_type="text", question="...tài khoản nào của Elon Musk?")` | Có mapping tên→handle nhưng bị rule "không đoán account" đè lên → hạ routing | Prompt: mapping `Elon Musk→elonmusk`, `Sam Altman→sama` được dùng trực tiếp; "không đoán" chỉ khi user **không nêu ai** |
| M02_carryover_timeframe (v1) | wrong_arg_value | `social_search(query="robotics")` | "Chỉ tìm robotics thôi, vẫn là tin hôm nay" → đổi cả nguồn sang social, mất `topic=news`, `timeframe=day` | Prompt: carry-over mọi tham số user không sửa; "chỉ tìm X" chỉ thay subject |
| M02_carryover_timeframe (v2) | wrong_arg_value | `lookup(robotics, news, day) + social_search(robotics)` | Đã carry đúng nhưng thêm `social_search` dư | Luật không gọi kèm `social_search` (xem R03-v2) |
| M06_switch_tool (v2) | wrong_tool | `lookup(OpenAI, news, week) + social_search(OpenAI)` | User đã nói "Bỏ Twitter, chuyển sang tìm trên web" → vẫn gọi Twitter | Description `social_search`: KHÔNG gọi sau khi user bỏ Twitter; prompt: correction mới nhất đè giá trị cũ |

### Lỗi vận hành: X/Twitter API hết quota

Trong cả 3 run, tool X/Twitter trả `HTTPError 403` (timeline 6/4/5 lần; social_search 3/4/6 lần) do **hết quota RapidAPI** tại thời điểm chạy. Eval vẫn chấm đúng vì chỉ so tool calls/args, nhưng **nội dung trả về rỗng** → không dùng được để đánh giá chất lượng câu trả lời. Đây là lỗi hạ tầng, không phải lỗi routing của agent.

### Trường hợp cần đọc tay thay vì chấm tự động

**R12_confirm_before_send** là case bị chấm oan rõ nhất. Eval chỉ kiểm tra `clarify.response_type == "yes_no"`, nên mọi câu hỏi dạng `text` đều bị FAIL — kể cả khi agent đã hành xử **an toàn** (không gửi gì). Ở cả 3 version, agent đều không tự gửi; v1/v2 còn chủ động hỏi xin nội dung, đúng tinh thần guardrail. Nói cách khác:

- Nếu tiêu chí là "không được gửi khi chưa xác nhận" → agent **đúng** ở v1/v2.
- Nếu tiêu chí là "phải dùng đúng `yes_no` để xác nhận ý định publish" → agent **sai**.

Vì vậy R12 nên được chấm bằng người đọc transcript (kiểm tra có gọi `send` hay không), và chỉ dùng `response_type` như tín hiệu phụ. Tương tự, các câu trả lời có trích nguồn đúng/sai và trường hợp tool lỗi 403 đều cần review thủ công vì grader hiện tại không đo nội dung.

## B3. Team Eval Cases

Nguồn: `data/eval_group.json` (`dataset_id: day04_v2_research_group`, 10 case). Cột **Result** để là "chưa chạy" vì **do giới hạn tài nguyên tính toán nên nhóm chưa thực hiện đầy đủ bước chạy group eval để ra kết quả**.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_compare_three_provided_sources | 3 nguồn đã cho trong hội thoại + yêu cầu đối chiếu | `compare_sources`, không tìm nguồn mới | Chưa chạy (giới hạn tài nguyên) |
| G02_compare_user_provided_sources | 2 nguồn tiếng Việt do user cung cấp | `compare_sources`, không `lookup`/`fetch` | Chưa chạy (giới hạn tài nguyên) |
| G03_search_not_compare | Chỉ yêu cầu **tìm** nguồn mới, chưa yêu cầu so sánh | `lookup(query="ứng dụng AI trong giáo dục đại học")` | Chưa chạy (giới hạn tài nguyên) |
| G04_compare_missing_sources | Yêu cầu so sánh nhưng chưa có nguồn | `clarify(response_type="text")`, không tự tạo nguồn | Chưa chạy (giới hạn tài nguyên) |
| G05_fetch_before_comparison | Có URL cụ thể, chỉ mới 1 nguồn | `fetch(url="https://openai.com/blog/gpt-5")`, chưa đủ để `compare_sources` | Chưa chạy (giới hạn tài nguyên) |
| G06_summary_not_comparison | Có nội dung, chỉ yêu cầu tóm tắt 3 ý | Không gọi tool, trả lời trực tiếp | Chưa chạy (giới hạn tài nguyên) |
| G07_explain_tool_capability | Hỏi `compare_sources` khác `lookup` thế nào | Không gọi tool, giải thích trực tiếp | Chưa chạy (giới hạn tài nguyên) |
| G08_out_of_scope_math | So sánh 2 biểu thức đại số (parse trap với `compare_sources`) | Không gọi tool research, từ chối/định hướng | Chưa chạy (giới hạn tài nguyên) |
| G09_rank_existing_posts_by_views | 2 bài đã có kèm `metrics.views` | `rank_by_engagement(metric="views")`, không tìm lại bài | Chưa chạy (giới hạn tài nguyên) |
| G10_trending_routing | "Trên X đang có gì hot vậy?" — không từ khóa | `trending_on_X`, mặc định `vietnam`, **không** hỏi lại khu vực | Chưa chạy (giới hạn tài nguyên) |

**Thiết kế bộ case:** 10 case được chia thành 3 nhóm để kiểm tra đúng điểm mới của sản phẩm:

- **Nhóm so sánh nguồn (G01–G05):** kiểm tra ranh giới của `compare_sources` — chỉ dùng khi **đã có ≥ 2 nguồn**, không dùng để tìm nguồn mới, không dùng khi mới có URL của một nguồn.
- **Nhóm không-gọi-tool (G06–G08):** kiểm tra model có phân biệt "tóm tắt nội dung đã có", "hỏi về tool", "ngoài phạm vi" hay không — đây là các lỗi "gọi tool dư" phổ biến.
- **Nhóm tool mới (G09–G10):** đảm bảo `rank_by_engagement` và `trending_on_X` có ít nhất một case routing, đúng yêu cầu README.

**Thiếu sót đã biết:** cấu trúc hiện tại là **8 case single-turn** (có `query`) + **2 case multi-turn** (có `turns`: G01, G02), trong khi README yêu cầu **5 single + 5 multi**. Do giới hạn thời gian/tài nguyên, nhóm chưa bổ sung 3 case multi-turn còn lại và chưa chạy `--suite group` để điền cột Result.

## B4. Live Chat Evidence

Bằng chứng lấy từ transcript thật do thành viên chạy ngày 10/11/2026 (`dung-test`, model `openai/gpt-4o-mini`, prompt hash `02277ac4f327` — khớp commit `c25633d`, tools hash `5b22a2476d41`). Transcript từng được commit ở `e96b0d0` rồi bị xoá khỏi repo ở `c09a85d`; nội dung dưới đây khôi phục từ git history.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | `Lấy 3 bài đăng mới nhất giúp tôi.` | **Không có tool call** — agent hỏi bằng text: "Bạn muốn xem bài đăng của tài khoản nào?" | `artifact_version = dung-test+p02277ac4f327+t5b22a2476d41` | Đúng ý định (không đoán tài khoản) nhưng **hỏi bằng assistant text thay vì gọi `clarify`** → vi phạm luật "dùng structured tool call". Đây là bằng chứng cho thấy prompt phải nói rõ *cách* hỏi, không chỉ *khi nào* hỏi |
| 2 | `@tvOneNews` | `timeline(screenname="tvOneNews", limit=3)` | cùng artifact version | Trả về 3 bài thật từ `@tvOneNews`, mỗi bài có URL `x.com/...`, ngày, tóm tắt → hiểu history từ lượt 1 và giữ đúng `limit=3` |

Ghi chú: transcript chỉ có **2 lượt**, chưa đạt yêu cầu "≥ 3 lượt live" của README, và không có lượt nào minh hoạ `send` có xác nhận.

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | `tools/send/tool.py`, `tools/send/TOOL.md`, `app.py` | Tool có guardrail `confirmed=true`; UI chỉ gọi gửi thật sau khi user xác nhận đúng text | **Tool có guardrail nhưng chưa chứng minh end-to-end** — chưa có transcript gửi Telegram thật; `TELEGRAM_CHAT_ID` còn trống trong `.env` |
| arXiv/company policy | `tools/papers/`, `tools/paper_text/`, `tools/policy/` + `company_policy/*.md` (5 file) | `policy` tách `facts` vs `untrusted_text` (chặn prompt-injection trong `## Injection probe` của `source-citation-policy.md`) | Nội dung policy là dữ liệu untrusted, chỉ dùng `facts`/`source`/`effective_date` |
| UI | `app.py` (Streamlit) + `.streamlit/config.toml` | Chạy local ổn: chat dùng chung tool loop của `chat.py`, có tool trace, clarify pause, send gate, eval dashboard đọc `runs/` | Không deploy public; chỉ demo trên máy local |
| Tool unit tests (`tests/`) | `pytest tests -q` (10/11/2026) | **121 passed** | **1 failed**: `test_timeline_reports_page_scope` còn `pytest.skip(TODO)` → `NameError: name 'TODO' is not defined`. Chưa đạt yêu cầu "0 failed, 0 skipped" |

Tool unit tests: 121 test pass, phủ `format`, `send`, `lookup`, `fetch`, `timeline`, `policy`, `rank_by_engagement`, `compare_sources`, `trending_on_X`. Một lỗi mà unit test bắt được nhưng eval không bắt: `rank_by_engagement` khi metric bị thiếu (`None`) phải xếp **cuối**, không được coi là 0 — eval routing không kiểm tra giá trị sắp xếp nên chỉ unit test mới phát hiện. Test `test_timeline_reports_page_scope` là bằng chứng `timeline` chỉ lấy **một page API** và phải báo `has_more`, điều eval cũng không đo.

## B6. Reflection

- **Which fixes belonged in `system_prompt.md`?** Các luật mang tính "chính sách hội thoại" và thứ tự ưu tiên: carry-over tham số giữa các lượt (M02), correction mới nhất đè giá trị cũ (M06), không đoán account/URL (R10/R11), xác nhận trước khi gửi và hỏi lại khi nội dung đổi (R12), out-of-scope thì trả lời trực tiếp không gọi tool (R08/R14). Bằng chứng: v1 chỉ sửa prompt (tools y nguyên) đã sửa 4 case bịa (R08/R10/R11/R14), routing 0.75 → 0.90.
- **Which fixes belonged in `tools.yaml`?** Các quy ước tham số và ranh giới "khi nào KHÔNG dùng tool": `query` chỉ chứa subject (R03/R13), `topic`/`timeframe`/`search_type` chứa loại tin và thời gian, `social_search` không gọi kèm `lookup` và không dùng sau khi user bỏ Twitter (R02/R03/M02/M06), `fetch` chỉ nhận URL nguyên văn. Bằng chứng: v2 thêm description chi tiết → R13 chuyển FAIL→PASS.
- **Which failure needed manual review instead of automatic grading?** (1) R12 — grader chỉ so `response_type`, nên phạt cả những lần agent hành xử **an toàn** (không gửi gì) và chỉ hỏi lại; cần người đọc transcript để chấm "có gọi `send` hay không", dùng `response_type` làm tín hiệu phụ. (2) Các case có tool trả `HTTPError 403` do hết quota RapidAPI — eval vẫn PASS/FAIL theo routing nhưng agent không có dữ liệu thật, nên chất lượng trả lời phải xem tay. (3) Việc trích nguồn đúng/sai trong câu trả lời — eval không đo.
- **What would you improve next?** (a) Ghi `artifacts/version_log.csv` ngay từ v0 thay vì dựng lại từ run JSON/hash; (b) chạy base eval cho v3 và chạy `--suite group` cho `eval_group.json`; (c) bổ sung 3 case multi-turn để đủ 5 single + 5 multi; (d) hoàn thiện `test_timeline_reports_page_scope` để `pytest` về 0 failed/0 skipped; (e) thêm transcript ≥ 3 lượt, gồm một lượt chứng minh `send` có xác nhận end-to-end; (f) rút luật publish-boundary về một nguồn duy nhất thay vì lặp ở prompt + `clarify` + `send`.

### Bài học của nhóm

1. **Viết `version_log.csv` ngay từ v0.** Hiện tại file chỉ có header; mọi kết luận "version nào sửa gì, điểm trước/sau bao nhiêu" đều phải dựng lại bằng cách đối chiếu `prompt_hash`/`tools_hash` trong run JSON với git history. Nếu ghi ngay từ v0 (một dòng cho mỗi lần chạy: author, artifact, hypothesis, metric before/after, run file) thì báo cáo sẽ nhanh và đáng tin hơn nhiều.
2. **Thứ tự cải tiến nên là: chia việc thành viên → prompt → tool description.** Trước tiên phải thống nhất ai chịu phần nào (prompt, tools, eval cases, tool mới, UI) và chốt format trao đổi (run JSON, transcript). Sau đó mới tinh chỉnh **prompt** để định hình hành vi hội thoại (hỏi lại, carry-over, xác nhận), rồi mới đến **tool description** cho các quy ước tham số. Làm ngược lại (sửa tools trước khi chốt hành vi) dẫn đến sửa đi sửa lại: v2 viết lại description nhưng R12 vẫn trượt vì luật boundary gốc thuộc về prompt.

## B7. Small Local Model Challenge (bonus)

> **Chưa thực hiện.** Do giới hạn tài nguyên tính toán (máy chưa cài Ollama, không đủ điều kiện chạy model local ổn định) nên nhóm chưa thực hiện đầy đủ challenge. Các bảng dưới để trống và sẽ được điền nếu có điều kiện.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3 | (cloud) | v3 |  |  |  |  | _(chưa có run v3)_ |
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
