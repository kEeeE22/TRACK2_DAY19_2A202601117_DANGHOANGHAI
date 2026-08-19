# Reflection — Lab 19

**Tên:** Đặng Hoàng Hải
**Cohort:** 2A202601117
**Path đã chạy:** lite

---

## Câu hỏi (≤ 200 chữ)

> Trên golden set 50 queries, mode nào thắng ở loại query nào (`exact` /
> `paraphrase` / `mixed`), và tại sao? Khi nào bạn **không** dùng hybrid
> (i.e. khi nào pure BM25 hoặc pure vector là lựa chọn đúng)?

Trên golden set 50 queries: **exact** — BM25 ngang Hybrid (96.7%), vì query chứa từ kỹ thuật verbatim nên BM25 match trực tiếp, RRF không thêm giá trị. **Paraphrase** — tất cả đều yếu (BM25 33%, Semantic 24%, Hybrid 32%); Semantic lẽ ra thắng nhưng `bge-small-en-v1.5` chỉ train tiếng Anh nên embedding tiếng Việt là nhiễu — Hybrid bị kéo xuống dưới cả BM25. **Mixed** — Hybrid thắng rõ (100% vs 97–98%), vì query người dùng thật vừa có keyword chính xác vừa có ý tưởng diễn đạt khác, RRF tổng hợp được cả hai tín hiệu.

Không dùng Hybrid khi: (1) latency budget < 10ms — keyword P99 = 5.4ms, hybrid 41.2ms; (2) embedding model sai ngôn ngữ/domain — semantic signal là nhiễu, fusion cho kết quả tệ hơn BM25; (3) corpus toàn exact-match (ID, SKU, mã lỗi) — BM25 alone đủ; (4) filter selectivity < 5% — cả Hybrid lẫn BM25 đều sụp recall về 0, phải dùng filtered-ANN.

---

## Điều ngạc nhiên nhất khi làm lab này

Post-filter với selectivity 3.8% trả về recall = 0 mà không có exception hay log lỗi nào — silent failure hoàn toàn. Và semantic cache threshold 0.75 (AWS khuyến nghị) vẫn để lọt 36% câu trả lời sai trên corpus này.

---

## Bonus challenge

- [ ] Đã làm bonus (xem `bonus/`)
- [ ] Pair work với: _<tên đồng đội nếu có>_
