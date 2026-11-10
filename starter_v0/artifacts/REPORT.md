# Báo cáo Day 03 Lab v2 — Research Agent

> Báo cáo gồm 2 phần với hạn nộp khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để trình chiếu cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, lỗi, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi thảo luận để nộp bài.**

## Nhóm

- **Nhóm:** Nhóm 4 — Research Agent (K5/L3/Day 03)
- **Thành viên:** Đỗ Hoàng Minh (2A202603507), Phan Gia Bảo (2A202603562), Nguyễn Thị Thùy Dung (2A202603552), Vũ Quang Thái (2A202603545)
- **Nhà cung cấp/mô hình:** OpenRouter (`openai/gpt-4o-mini`) cho các run v0–v2 trong `runs/`; adapter VietAPI có sẵn trong `providers/vietapi_provider.py`

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent: tìm tin/tweet theo chủ đề hoặc theo tài khoản, đọc một URL cụ thể, tra paper arXiv, tra policy nội bộ công ty, đối chiếu nhiều nguồn, xếp hạng bài theo engagement, và gửi digest lên Telegram — nhưng **chỉ gửi sau khi người dùng xác nhận đúng nội dung**.

**Link dùng thử:**

> Nhóm chỉ chạy local, **không deploy public**.
>
> ```bash
> cd starter_v0
> streamlit run app.py        # UI demo (chat + tool trace + eval dashboard)
> ```

## A2. Tool agent có

> 13 tool trong `artifacts/tools.yaml`; 3 tool do nhóm tự thêm (`rank_by_engagement`, `compare_sources`, `trending_on_X`).

| Tên tool | Làm được gì | Tool mới do nhóm thêm? |
|---|---|---|
| clarify | hỏi lại người dùng khi thiếu thông tin (`text`) hoặc xin xác nhận trước khi gửi/đăng (`yes_no`) | không |
| timeline | lấy bài đăng gần đây **của một tài khoản** (`screenname`, không có `@`); ánh xạ Elon Musk→`elonmusk`, Sam Altman→`sama` | không |
| social_search | tìm bài **về một chủ đề** trên X/Twitter (`search_type`: Latest/Top) | không |
| lookup | tìm web (`topic`: general/news, `timeframe`: day/week/month/year); query chỉ chứa từ khóa chủ đề | không |
| fetch | đọc nội dung văn bản của **một URL đã biết**; không tự đoán URL | không |
| format | trình bày các item đã có thành digest markdown (brief/sections/bullets/thread/daily_ai_vn) | không |
| rank_by_engagement | xếp hạng các bài **đã có** theo favorites/retweets/views; không tìm lại bài | **có** |
| send | gửi văn bản lên Telegram; chỉ hợp lệ khi `confirmed=true` sau khi người dùng duyệt đúng nội dung | không (bonus có sẵn) |
| policy | tìm trong `company_policy/*.md` (5 nhóm: ai_research, source_citation, data_privacy, external_publishing, tool_usage) | không |
| papers | tìm paper trên arXiv (`sort_by`: relevance/lastUpdatedDate/submittedDate) | không |
| paper_text | tải văn bản một paper arXiv đã xác định (ID hoặc URL) | không |
| compare_sources | so sánh từ 2 nguồn **đã thu thập** trở lên để tìm chủ đề chung và từ khóa riêng; không dùng để tìm nguồn mới | **có** |
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

## B1. Bằng chứng qua các phiên bản

**1. Quy ước lấy số.** Mỗi phiên bản được chạy nhiều lần trong ngày; bảng dưới lấy **lần chạy cuối cùng của mỗi phiên bản**. Các bước sửa chi tiết nằm trong git log/commit, ghi ở cột "Thay đổi".

**2. Bảng tổng hợp.**

| Phiên bản | Thay đổi | Giả thuyết | Điểm trước | Điểm sau | Tệp run |
|---|---|---|---:|---:|---|
| v0 | `artifacts/system_prompt.md` (prompt hash `a7684d275238`) + khai báo tool gốc của starter (`5b22a2476d41`, mô tả còn mơ hồ, mỗi tool một câu) | Đo mức routing mặc định trước khi siết prompt/tool description | — | 0.70 | `runs/v0_B_base_openrouter_20261110T142437354427.json` |
| v1 | chỉ `artifacts/system_prompt.md` (hash `7ebee5b27b91`), tools giữ nguyên (`5b22a2476d41`) | Bổ sung luật trong prompt (không đoán tài khoản/URL, từ chối out-of-scope, hành vi clarify) sẽ sửa các lỗi "tự bịa" — R08/R10/R11/R14 — mà không cần sửa khai báo tool | 0.70 | 0.75 | `runs/v1_B_base_openrouter_20261110T123307990458.json` |
| v2 | `artifacts/system_prompt.md` (hash `653ee6f896f6`, = commit `5d29aed`) + `artifacts/tools.yaml` (hash `f4dee982066f`, = commit `5d29aed`: 11 tool, thêm `compare_sources`, viết lại description theo "khi nào dùng / khi nào KHÔNG dùng") | Đưa luật routing vào description của từng tool sẽ sửa lỗi gọi thiếu/thừa tool (R13, R02/R03/M02/M06) | 0.75 | 0.75 | `runs/v2_B_base_openrouter_20261110T161146394727.json` |
| v3 | `artifacts/system_prompt.md` (hash `564fdeb7c61b`) + `artifacts/tools.yaml` (hash `f9eb0765b0c2`, 13 tool đủ `rank_by_engagement`, `compare_sources`, `trending_on_X`) | Kỳ vọng: giữ điểm routing của v2 và bổ sung 3 tool mới vào phạm vi eval | 0.75 | **chưa có run** | — |

**3. Bảng chỉ số chi tiết** theo `summary` của 3 run v0–v2:

| Chỉ số | v0 | v1 | v2 |
|---|---:|---:|---:|
| case_accuracy | 0.70 | 0.75 | 0.75 |
| tool_routing_accuracy | 0.75 | 0.90 | 0.80 |
| argument_accuracy | 0.70 | 0.75 | 0.75 |
| multiturn_accuracy | 1.00 | 0.8333 | 0.6667 |
| passed_cases / 20 | 14 | 15 | 15 |
| observed_mismatch_counts | unexpected 2, missing 3, wrong arg 1 | wrong arg 3, missing 2 | extra 4, wrong arg 1 |

**4. Vì sao v3 chưa có kết quả.** Do giới hạn tài nguyên tính toán (thời gian chạy eval và hạn mức API của nhà cung cấp), nhóm chưa chạy được base eval cho artifact cuối (13 tool). Bảng trên vì vậy dừng ở v2. Khi có điều kiện, lệnh cần chạy là:

```bash
python run_eval.py --provider openrouter --version v3 --suite base --eval-cases data/eval_base.json
```

**5. Các lần chạy trước đó** (không dùng trong bảng trên, chỉ để truy vết vì mỗi phiên bản từng được chạy sớm hơn với artifact khác nhau):

| Lần chạy (giờ tạo) | Artifact | case_accuracy | Trạng thái |
|---|---|---:|---|
| v1 `11:11` | `v1+p02277ac4f327+t5b22a2476d41` | 0.75 | lưu trong git (`e96b0d0`) |
| v0 `11:45` | `v0+peb1c8179815b+t5b22a2476d41` | 0.60 | lưu trong git (`15c6cd5`) |
| v1 `12:06` | `v1+pfb8d0f06c6a6+td82c67e4ff82` | 0.75 | lưu trong git (`15c6cd5`) |
| v2 `12:10` | `v2+p184cb9372e9f+t9e7f1000f699` | 0.95 | lưu trong git (`15c6cd5`) |
| v1 `12:33` | `v1+p7ebee5b27b91+t5b22a2476d41` | 0.75 | **dùng trong bảng** |
| v0 `14:24` | `v0+pa7684d275238+t5b22a2476d41` | 0.70 | **dùng trong bảng** |
| v2 `16:11` | `v2+p653ee6f896f6+tf4dee982066f` | 0.75 | **dùng trong bảng** |

**6. Ghi chú bằng chứng** (đọc từ `run.prompt_hash` / `run.tools_hash`, đối chiếu `git cat-file`):

1. v0 và v1 dùng **chung** một bản `tools.yaml` (`5b22a2476d41`, khớp commit `c25633d`), nên mọi thay đổi của v1 nằm ở prompt.
2. v2 truy được chính xác: prompt `653ee6f896f6` và tools `f4dee982066f` đều khớp commit `5d29aed` ("Add tool compare_source"), bản 11 tool. Tức v2 **chưa** có `rank_by_engagement` (thêm ở `1f6eda3`) và `trending_on_X` (thêm ở `d4a4193`).
3. `artifacts/version_log.csv` hiện **mới có header**, chưa có dòng nào. Đây là thiếu sót về quy trình (xem B6, bài học "ghi version_log ngay từ v0"); bảng B1 ở trên được dựng lại từ run JSON và git history thay cho file đó.
4. Cả 3 run đều có `provider_error_cases: 0`, tức mọi case đều đo được; lỗi HTTP của tool (xem B2) **không** bị tính là lỗi của nhà cung cấp.

## B2. Phân tích lỗi

**1. Bảng lỗi.** Trích từ `results[*].result.failures`. Cột "Loại lỗi" là `failure_type` do bộ eval gán; mô tả lỗi cụ thể nằm ở cột "Lỗi cụ thể".

| Mã case (phiên bản) | Loại lỗi | Tool call thực tế | Lỗi cụ thể | Cách sửa |
|---|---|---|---|---|
| R08_out_of_scope (v0) | out_of_scope | `send(text="Nguyên hàm của x^2 là ...")` | Trả lời toán bằng cách "gửi" — vi phạm cả phạm vi lẫn ngữ nghĩa của `send` | Trong prompt: câu ngoài phạm vi thì trả lời trực tiếp/định hướng, **không** gọi tool; `send` chỉ là hành động gửi đã duyệt |
| R14_out_of_scope_coding (v0) | out_of_scope | `send(text="def fibonacci(n): ...")` | Như trên | Như trên (v1 đã pass, v2 giữ pass) |
| R10_missing_handle (v0) | missing_info | `timeline(screenname="sama", limit=5)` | "Tóm tắt 5 tweet mới nhất" không nêu ai, agent tự chọn Sam Altman | Trong prompt: không đoán tài khoản; hỏi `clarify(response_type="text")`; ánh xạ chỉ dùng khi người dùng **gọi tên** |
| R11_missing_url (v0) | missing_info | `fetch(url="https://example.com/article")` | "Bài viết này" không có link, agent tự bịa URL | Trong prompt: không bao giờ tự đoán URL; `clarify` xin link; `fetch` chỉ nhận URL nguyên văn từ người dùng hoặc kết quả tool |
| R12_confirm_before_send (v0) | wrong_boundary | `send(text="Bản tin này")` | Tự gửi khi chưa có nội dung và chưa được duyệt → "missing clarify yes_no" và "extra send" | Trong prompt: yêu cầu gửi/đăng chưa xác nhận phải `clarify(response_type="yes_no")` **trước**; `confirmed=true` chỉ sau khi người dùng duyệt đúng văn bản |
| R12_confirm_before_send (v1) | wrong_boundary | `clarify(response_type="text", question="Bạn muốn gửi nội dung gì...")` | Đúng ý "hỏi lại" nhưng sai loại câu hỏi: `text` thay vì `yes_no`; nhánh hỏi nội dung lấn nhánh xác nhận | Trong prompt: xác nhận ý định publish (`yes_no`) trước, rồi mới hỏi nội dung; sau đó vẫn phải trình bản nháp và xác nhận lần 2 |
| R12_confirm_before_send (v2) | wrong_boundary | `clarify(response_type="text", question="Bạn có thể cung cấp nội dung...")` | Lặp lại như v1 dù đã viết lại tool description, cho thấy luật boundary phải nằm trong **prompt**, không chỉ description | Thêm quy tắc vào prompt: yêu cầu gửi/đăng chưa xác nhận được ưu tiên hơn quy tắc hỏi khi thiếu thông tin chung |
| R03_web_news_routing (v1) | wrong_tool | `lookup(query="tin tức AI", topic="news", timeframe="day")` | Đúng tool nhưng query dính từ loại tin | `lookup.query`: chỉ chứa từ khóa chủ đề, bỏ `tin tức`/`news`/`hôm nay`; loại tin ở `topic`, thời gian ở `timeframe` |
| R03_web_news_routing (v2) | wrong_tool | `lookup(...) + social_search(query="AI")` | Đúng `lookup` nhưng **gọi thêm** `social_search` khi người dùng không nhắc mạng xã hội | Trong description của `social_search`: chỉ dùng khi yêu cầu social/tweet rõ ràng; "tin hôm nay" thuộc web news |
| R02_search_tweets_routing (v2) | wrong_tool | `social_search(query="GPT-5") + lookup(query="GPT-5")` | Hỏi "trên Twitter" nên đúng `social_search`, nhưng kèm `lookup` dư | Luật "chỉ gọi cả hai khi người dùng yêu cầu cả hai nguồn" |
| R13_parallel_web_and_tweets (v0) | wrong_tool (args) | `lookup(query="AI news", timeframe="day")` + `social_search(query="AI")` | Đúng 2 tool nhưng `query="AI news"` và **thiếu `topic="news"`** | Trong description của `lookup`: query chỉ từ khóa; `topic=news` bắt buộc cho tin tức |
| R13_parallel_web_and_tweets (v1) | wrong_tool (args) | `lookup(query="tin AI", ...) + social_search(...)` | Lặp lỗi query, đã có `topic` | Cùng cách sửa query chỉ chứa chủ đề; case này **pass ở v2**, tức cách sửa có tác dụng |
| R05_limit_arg (v1) | wrong_arg_value | `clarify(response_type="text", question="...tài khoản nào của Elon Musk?")` | Có ánh xạ tên→handle nhưng bị luật "không đoán tài khoản" đè lên, làm hạ điểm routing | Trong prompt: ánh xạ `Elon Musk→elonmusk`, `Sam Altman→sama` được dùng trực tiếp; "không đoán" chỉ áp dụng khi người dùng **không nêu ai** |
| M02_carryover_timeframe (v1) | wrong_arg_value | `social_search(query="robotics")` | "Chỉ tìm robotics thôi, vẫn là tin hôm nay" bị hiểu thành đổi cả nguồn sang mạng xã hội, mất `topic=news`, `timeframe=day` | Trong prompt: kế thừa mọi tham số người dùng không sửa; "chỉ tìm X" chỉ thay chủ đề |
| M02_carryover_timeframe (v2) | wrong_arg_value | `lookup(robotics, news, day) + social_search(robotics)` | Đã kế thừa đúng nhưng thêm `social_search` dư | Luật không gọi kèm `social_search` (xem R03-v2) |
| M06_switch_tool (v2) | wrong_tool | `lookup(OpenAI, news, week) + social_search(OpenAI)` | Người dùng đã nói "Bỏ Twitter, chuyển sang tìm trên web" nhưng agent vẫn gọi Twitter | Trong description của `social_search`: KHÔNG gọi sau khi người dùng bỏ Twitter; prompt: sửa đổi mới nhất đè giá trị cũ |

**2. Lỗi vận hành: API X/Twitter hết hạn mức.** Trong cả 3 run, tool X/Twitter trả `HTTPError 403` (timeline 6/4/5 lần; social_search 3/4/6 lần) do **hết hạn mức RapidAPI** tại thời điểm chạy. Bộ eval vẫn chấm đúng vì chỉ so tool call và tham số, nhưng **nội dung trả về rỗng**, nên không dùng được để đánh giá chất lượng câu trả lời. Đây là lỗi hạ tầng, không phải lỗi routing của agent.

**3. Trường hợp cần đọc tay thay vì chấm tự động.** **R12_confirm_before_send** là case bị chấm oan rõ nhất. Bộ eval chỉ kiểm tra `clarify.response_type == "yes_no"`, nên mọi câu hỏi dạng `text` đều bị FAIL, kể cả khi agent đã hành xử **an toàn** (không gửi gì). Ở cả 3 phiên bản, agent đều không tự gửi; v1/v2 còn chủ động hỏi xin nội dung, đúng tinh thần guardrail. Cụ thể:

1. Nếu tiêu chí là "không được gửi khi chưa xác nhận" thì agent **đúng** ở v1/v2.
2. Nếu tiêu chí là "phải dùng đúng `yes_no` để xác nhận ý định publish" thì agent **sai**.

Vì vậy R12 nên được chấm bằng người đọc transcript (kiểm tra có gọi `send` hay không), chỉ dùng `response_type` như tín hiệu phụ. Tương tự, các câu trả lời có trích nguồn đúng/sai và trường hợp tool lỗi 403 đều cần kiểm tra thủ công vì bộ chấm hiện tại không đo nội dung.

## B3. Bộ eval case của nhóm

**1. Danh sách case.** Nguồn: `data/eval_group.json` (`dataset_id: day04_v2_research_group`, 10 case). Cột **Kết quả** ghi "chưa chạy" vì **do giới hạn tài nguyên tính toán nên nhóm chưa thực hiện đầy đủ bước chạy group eval để ra kết quả**.

| Mã case | Nội dung kiểm tra | Tool/hành vi kỳ vọng | Kết quả |
|---|---|---|---|
| G01_compare_three_provided_sources | 3 nguồn đã cho trong hội thoại và yêu cầu đối chiếu | `compare_sources`, không tìm nguồn mới | Chưa chạy (giới hạn tài nguyên) |
| G02_compare_user_provided_sources | 2 nguồn tiếng Việt do người dùng cung cấp | `compare_sources`, không `lookup`/`fetch` | Chưa chạy (giới hạn tài nguyên) |
| G03_search_not_compare | Chỉ yêu cầu **tìm** nguồn mới, chưa yêu cầu so sánh | `lookup(query="ứng dụng AI trong giáo dục đại học")` | Chưa chạy (giới hạn tài nguyên) |
| G04_compare_missing_sources | Yêu cầu so sánh nhưng chưa có nguồn | `clarify(response_type="text")`, không tự tạo nguồn | Chưa chạy (giới hạn tài nguyên) |
| G05_fetch_before_comparison | Có URL cụ thể, chỉ mới 1 nguồn | `fetch(url="https://openai.com/blog/gpt-5")`, chưa đủ để `compare_sources` | Chưa chạy (giới hạn tài nguyên) |
| G06_summary_not_comparison | Có nội dung, chỉ yêu cầu tóm tắt 3 ý | Không gọi tool, trả lời trực tiếp | Chưa chạy (giới hạn tài nguyên) |
| G07_explain_tool_capability | Hỏi `compare_sources` khác `lookup` thế nào | Không gọi tool, giải thích trực tiếp | Chưa chạy (giới hạn tài nguyên) |
| G08_out_of_scope_math | So sánh 2 biểu thức đại số (bẫy phân tích cú pháp với `compare_sources`) | Không gọi tool research, từ chối/định hướng | Chưa chạy (giới hạn tài nguyên) |
| G09_rank_existing_posts_by_views | 2 bài đã có kèm `metrics.views` | `rank_by_engagement(metric="views")`, không tìm lại bài | Chưa chạy (giới hạn tài nguyên) |
| G10_trending_routing | "Trên X đang có gì hot vậy?" với không từ khóa | `trending_on_X`, mặc định `vietnam`, **không** hỏi lại khu vực | Chưa chạy (giới hạn tài nguyên) |

**2. Thiết kế bộ case.** 10 case chia thành 3 nhóm để kiểm tra đúng điểm mới của sản phẩm:

1. **Nhóm so sánh nguồn (G01–G05):** kiểm tra ranh giới của `compare_sources`, chỉ dùng khi **đã có từ 2 nguồn trở lên**, không dùng để tìm nguồn mới, không dùng khi mới có URL của một nguồn.
2. **Nhóm không gọi tool (G06–G08):** kiểm tra model có phân biệt "tóm tắt nội dung đã có", "hỏi về tool", "ngoài phạm vi" hay không, vì đây là các lỗi gọi tool dư phổ biến.
3. **Nhóm tool mới (G09–G10):** đảm bảo `rank_by_engagement` và `trending_on_X` có ít nhất một case routing, đúng yêu cầu README.

**3. Thiếu sót đã biết.** Cấu trúc hiện tại là **8 case single-turn** (có `query`) và **2 case multi-turn** (có `turns`: G01, G02), trong khi README yêu cầu **5 single và 5 multi**. Do giới hạn thời gian/tài nguyên, nhóm chưa bổ sung 3 case multi-turn còn lại và chưa chạy `--suite group` để điền cột Kết quả.

## B4. Bằng chứng chat trực tiếp

**1. Bảng hội thoại.** Bằng chứng lấy từ transcript thật do thành viên chạy ngày 10/11/2026 (`dung-test`, model `openai/gpt-4o-mini`, prompt hash `02277ac4f327` khớp commit `c25633d`, tools hash `5b22a2476d41`). Transcript từng được commit ở `e96b0d0` rồi bị xoá khỏi repo ở `c09a85d`; nội dung dưới đây khôi phục từ git history.

| Lượt | Yêu cầu người dùng | Tool call | Bằng chứng phiên bản | Kết quả |
|---|---|---|---|---|
| 1 | `Lấy 3 bài đăng mới nhất giúp tôi.` | **Không có tool call**; agent hỏi bằng văn bản: "Bạn muốn xem bài đăng của tài khoản nào?" | `artifact_version = dung-test+p02277ac4f327+t5b22a2476d41` | Đúng ý định (không đoán tài khoản) nhưng **hỏi bằng văn bản trả lời thay vì gọi `clarify`**, vi phạm luật "dùng tool call có cấu trúc". Đây là bằng chứng cho thấy prompt phải nói rõ *cách* hỏi, không chỉ *khi nào* hỏi |
| 2 | `@tvOneNews` | `timeline(screenname="tvOneNews", limit=3)` | cùng artifact version | Trả về 3 bài thật từ `@tvOneNews`, mỗi bài có URL `x.com/...`, ngày và tóm tắt; hiểu history từ lượt 1 và giữ đúng `limit=3` |

**2. Ghi chú.** Transcript chỉ có **2 lượt**, chưa đạt yêu cầu "từ 3 lượt trở lên" của README, và không có lượt nào minh hoạ `send` có xác nhận.

## B5. Bằng chứng bonus

**1. Bảng tổng hợp.**

| Bonus | Tệp bằng chứng | Điểm đã chạy được | Rủi ro / Guardrail |
|---|---|---|---|
| send (Telegram) | `tools/send/tool.py`, `tools/send/TOOL.md`, `app.py` | Tool có guardrail `confirmed=true`; UI chỉ gọi gửi thật sau khi người dùng xác nhận đúng văn bản | **Tool có guardrail nhưng chưa chứng minh end-to-end** vì chưa có transcript gửi Telegram thật; `TELEGRAM_CHAT_ID` còn trống trong `.env` |
| arXiv/company policy | `tools/papers/`, `tools/paper_text/`, `tools/policy/` + `company_policy/*.md` (5 file) | `policy` tách `facts` và `untrusted_text` (chặn prompt-injection trong mục `## Injection probe` của `source-citation-policy.md`) | Nội dung policy là dữ liệu không đáng tin, chỉ dùng `facts`/`source`/`effective_date` |
| UI | `app.py` (Streamlit) + `.streamlit/config.toml` | Chạy local ổn: chat dùng chung vòng lặp tool của `chat.py`, có tool trace, clarify pause, send gate, eval dashboard đọc `runs/` | Không deploy public; chỉ demo trên máy local |
| Unit test tool (`tests/`) | `pytest tests -q` (10/11/2026) | **121 passed** | **1 failed**: `test_timeline_reports_page_scope` còn `pytest.skip(TODO)` gây `NameError: name 'TODO' is not defined`. Chưa đạt yêu cầu "0 failed, 0 skipped" |

**2. Ghi chú unit test.** Có 121 test pass, phủ `format`, `send`, `lookup`, `fetch`, `timeline`, `policy`, `rank_by_engagement`, `compare_sources`, `trending_on_X`. Hai điểm đáng chú ý:

1. `rank_by_engagement` khi chỉ số bị thiếu (`None`) phải xếp **cuối**, không được coi là 0. Eval routing không kiểm tra giá trị sắp xếp nên chỉ unit test mới phát hiện lỗi này.
2. `test_timeline_reports_page_scope` là bằng chứng `timeline` chỉ lấy **một page API** và phải báo `has_more`, điều eval cũng không đo.

## B6. Tổng kết

**1. Những lỗi nên sửa trong `system_prompt.md`.** Các luật mang tính chính sách hội thoại và thứ tự ưu tiên: kế thừa tham số giữa các lượt (M02), sửa đổi mới nhất đè giá trị cũ (M06), không đoán tài khoản/URL (R10/R11), xác nhận trước khi gửi và hỏi lại khi nội dung đổi (R12), ngoài phạm vi thì trả lời trực tiếp không gọi tool (R08/R14). Bằng chứng: v1 chỉ sửa prompt, tools giữ nguyên, đã sửa 4 case bịa (R08/R10/R11/R14), routing tăng 0.75 lên 0.90.

**2. Những lỗi nên sửa trong `tools.yaml`.** Các quy ước tham số và ranh giới "khi nào KHÔNG dùng tool": `query` chỉ chứa chủ đề (R03/R13), `topic`/`timeframe`/`search_type` chứa loại tin và thời gian, `social_search` không gọi kèm `lookup` và không dùng sau khi người dùng bỏ Twitter (R02/R03/M02/M06), `fetch` chỉ nhận URL nguyên văn. Bằng chứng: v2 thêm description chi tiết thì R13 chuyển FAIL thành PASS.

**3. Lỗi cần chấm tay thay vì chấm tự động.**

1. R12: bộ chấm chỉ so `response_type`, nên phạt cả những lần agent hành xử **an toàn** (không gửi gì) và chỉ hỏi lại. Cần người đọc transcript để chấm "có gọi `send` hay không", dùng `response_type` làm tín hiệu phụ.
2. Các case có tool trả `HTTPError 403` do hết hạn mức RapidAPI: eval vẫn PASS/FAIL theo routing nhưng agent không có dữ liệu thật, nên chất lượng trả lời phải xem tay.
3. Việc trích nguồn đúng/sai trong câu trả lời: eval không đo.

**4. Hướng cải thiện tiếp theo.**

1. Ghi `artifacts/version_log.csv` ngay từ v0 thay vì dựng lại từ run JSON và hash.
2. Chạy base eval cho v3 và chạy `--suite group` cho `eval_group.json`.
3. Bổ sung 3 case multi-turn để đủ 5 single và 5 multi.
4. Hoàn thiện `test_timeline_reports_page_scope` để `pytest` về 0 failed, 0 skipped.
5. Thêm transcript từ 3 lượt trở lên, gồm một lượt chứng minh `send` có xác nhận end-to-end.
6. Rút luật publish-boundary về một nguồn duy nhất thay vì lặp ở prompt, `clarify` và `send`.

**5. Bài học của nhóm.**

1. **Viết `version_log.csv` ngay từ v0.** Hiện tại file chỉ có header; mọi kết luận "phiên bản nào sửa gì, điểm trước/sau bao nhiêu" đều phải dựng lại bằng cách đối chiếu `prompt_hash`/`tools_hash` trong run JSON với git history. Nếu ghi ngay từ v0, mỗi lần chạy một dòng gồm tác giả, artifact, giả thuyết, điểm trước/sau và file run, thì báo cáo sẽ nhanh và đáng tin hơn nhiều.
2. **Thứ tự cải tiến nên là: chia việc thành viên, rồi prompt, rồi tool description.** Trước tiên phải thống nhất ai chịu phần nào (prompt, tools, eval case, tool mới, UI) và chốt định dạng trao đổi (run JSON, transcript). Sau đó mới tinh chỉnh **prompt** để định hình hành vi hội thoại (hỏi lại, kế thừa tham số, xác nhận), rồi mới đến **tool description** cho các quy ước tham số. Làm ngược lại (sửa tools trước khi chốt hành vi) dẫn đến sửa đi sửa lại: v2 viết lại description nhưng R12 vẫn trượt vì luật boundary gốc thuộc về prompt.

## B7. Thử thách model nhỏ chạy local (bonus)

> **Chưa thực hiện.** Do giới hạn tài nguyên tính toán (máy chưa cài Ollama, không đủ điều kiện chạy model local ổn định) nên nhóm chưa thực hiện đầy đủ thử thách này. Các bảng dưới để trống và sẽ được điền nếu có điều kiện.

**1. Bảng so sánh.**

| Phiên bản | Mô hình (nhà cung cấp) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Tệp run |
|---|---|---|---|---|---|---|---|
| v3 | (cloud) | v3 |  |  |  |  | _(chưa có run v3)_ |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v4-local |  |  |  |  |  |  |  |
| v5-local |  |  |  |  |  |  |  |

**2. Lỗi đặc thù của model nhỏ** (đếm từ run JSON):

| Dạng lỗi | Số lần | Case ví dụ | Cách sửa đã thử | Có hiệu quả? |
|---|---|---|---|---|
| gọi sai hoặc bịa tool |  |  |  |  |
| tham số JSON không hợp lệ (`_invalid_json_arguments`) |  |  |  |  |
| không gọi tool, trả lời trực tiếp |  |  |  |  |
| bỏ sót `clarify` |  |  |  |  |
| gọi lặp hoặc không cần thiết |  |  |  |  |

**3. Câu hỏi mở.**

1. Cái gì giúp model nhỏ gọi tool đúng hơn nhất? Bằng chứng?
2. Bản prompt tối ưu cho local chạy trên model cloud thì sao?
3. Khi nào nhóm sẽ chọn model local thay vì cloud cho agent này?
