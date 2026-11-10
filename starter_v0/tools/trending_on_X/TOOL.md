---
name: trending_on_X
track: bonus
kind: live_api
provider: RapidAPI twitter-api45 (fallback X API v2)
requires_env: [RAPIDAPI_KEY]
inputs: [location, limit, contains]
outputs: [items, item_count, location, error]
side_effect: false
---
# trending_on_X

Lấy danh sách trend đang hot trên X cho một khu vực.
Env tuỳ chọn: `RAPIDAPI_TWITTER_HOST` (mặc định `twitter-api45.p.rapidapi.com`), `X_BEARER_TOKEN` (fallback).

- API: `GET https://<RAPIDAPI_TWITTER_HOST>/trends.php?country=<Country>` (twitter-api45).
  Nếu không có `RAPIDAPI_KEY` thì fallback sang X API v2
  `GET /2/trends/by/woeid/<woeid>` với `X_BEARER_TOKEN`.
- `location`: `vietnam` (mặc định), `worldwide`, `us`, `uk`, `japan`, `korea`,
  `singapore`, `thailand`, `india`. Có alias như `vn`, `global`, `usa`.
  Giá trị khác thì trả `error`, không tự đổi sang nước gần giống.
- `limit`: 1..50, mặc định 10. Nếu model gửi chuỗi số (`"5"`) thì ép kiểu.
  Giá trị `0`, số âm hoặc không phải số thì dùng mặc định 10, lớn hơn 50 thì cắt còn 50.
- `contains`: lọc trend theo chuỗi con (không phân biệt hoa thường) **trước** rồi mới cắt theo `limit`.
- Mỗi item có `rank`, `title`, `query` (để truyền tiếp cho `social_search`),
  `volume` (có thể `null`), `summary`, `url` (link X search), `source`, `section`.
  Các item này dùng thẳng được cho `format`.
- Không bao giờ raise: thiếu key, HTTP lỗi, mất mạng, JSON hỏng hay location không hợp lệ
  đều trả dict có `error` và `items=[]`.
