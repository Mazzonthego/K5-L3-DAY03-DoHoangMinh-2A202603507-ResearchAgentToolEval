---
name: rank_by_engagement
track: additional
kind: local_formatter
requires_env: []
inputs: [items, metric, limit]
outputs: [metric, items, item_count]
side_effect: false
---
# rank_by_engagement

Sắp xếp danh sách bài đã có theo `metrics.favorites`, `metrics.retweets` hoặc
`metrics.views`, từ cao xuống thấp. Mặc định dùng `favorites`; `limit` tùy chọn
giới hạn số kết quả. Phải lấy bài trước bằng `timeline` hoặc `social_search`.
Tool không gọi mạng, không tự tìm bài và không sửa danh sách đầu vào.
Kết quả chỉ xếp hạng trong `items` được truyền vào, không chứng minh là bài có
tương tác cao nhất trong toàn bộ lịch sử tài khoản. `timeline` chỉ lấy một
trang gần đây; lấy mẫu đủ rộng trước rồi nêu rõ phạm vi khi trình bày.
Với retweet, `timeline`/`social_search` dùng URL và chỉ số bài gốc nếu API
trả `retweeted_tweet`. Nếu API không cung cấp bài gốc, chỉ số được để null.
Số liệu là ảnh chụp tại thời điểm lấy và có thể thay đổi trên X.

Chấp nhận số và chuỗi số như `"1234"` hoặc `"1,234"`. Chỉ số thiếu/null được
giữ lại sau các bài có số; các bài bằng điểm hoặc cùng thiếu chỉ số giữ thứ tự
ban đầu. Chỉ số sai kiểu, âm hoặc không hữu hạn, metric không hợp lệ và limit
không phải số nguyên dương trả error dictionary. Chỉ số thiếu không phải là 0.
