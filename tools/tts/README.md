# Giọng cô giáo (tạo sẵn, chạy offline)

Mọi câu cô giáo nói trong app được tạo sẵn thành file âm thanh (`voice.json` ở thư mục gốc) để app đọc được cả khi không có mạng và trên iPhone bật chế độ im lặng.

Quy trình (đã dùng để tạo bản hiện tại):

1. Lấy danh sách câu: mở app, chạy trong Console `copy(JSON.stringify(__phrases()))` rồi dán vào `phrases.json` (hoặc chạy `python3 tests/booktest.py`, file này tự ghi `phrases.json`).
2. Tải hai mô hình của dự án [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx/releases) vào thư mục này:
   - `vits-piper-vi_VN-vais1000-medium` (tts-models) — đọc tiếng Việt,
   - `sherpa-onnx-zipformer-vi-int8-2025-04-20` (asr-models) — nghe lại để kiểm tra.
3. `pip install sherpa-onnx numpy` và cài `ffmpeg`.
4. `python3 gen_final.py --newonly` — chỉ tạo các câu mới; bỏ `--newonly` để tạo lại cả các âm chưa được máy nghe xác nhận.

Cách làm cho đúng dấu thanh:
- Âm, tiếng ngắn (bờ, ba, huyền, bà…) được đọc trong câu mang "Bây giờ cô đọc … (nhé)." rồi cắt đúng chỗ theo mốc thời gian của bộ nhận dạng, vì đọc riêng một tiếng thì mô hình hay nuốt âm hoặc hạ giọng.
- Câu dài được đọc sau lời dẫn "Rồi, cô đọc:" rồi cắt bỏ lời dẫn.
- Mỗi câu được bộ nhận dạng nghe lại; chỉ giữ bản nghe ra đúng từng chữ, đúng dấu. Kết quả ghi trong `voice_report.json`.

Giới hạn: giọng máy theo phát âm Hà Nội, chưa phân biệt r/d/gi, s/x, ch/tr. App không bắt bé phân biệt các cặp này bằng tai; cha mẹ có thể thu giọng thật thay cho từng âm trong Góc cha mẹ → Duyệt giọng.
