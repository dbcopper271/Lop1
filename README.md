# Bé Vào Lớp 1

Ứng dụng học mà chơi cho bé chuẩn bị vào lớp 1: bé luyện chữ cái, đánh vần, làm toán và tập tô để có **sức mạnh**, rồi vượt 40 màn thử thách ở 5 vùng đất để **giải cứu Công chúa Chữ** khỏi Quái vật Tẩy.

Chạy trên trình duyệt của máy tính, iPad, điện thoại Android và iPhone (cài được như ứng dụng). Không cần mạng để học; có mạng thì tự đồng bộ lên Supabase nếu cha mẹ đăng nhập.

## Nội dung

**Tiếng Việt**
- 29 chữ cái (12 nguyên âm, 17 phụ âm) và 11 chữ ghép (ch, gh, gi, kh, ng, ngh, nh, ph, qu, th, tr), mỗi chữ có tranh, từ mẫu và ghi chú phát âm.
- 6 thanh (ma – mà – má – mả – mã – mạ), nhận biết dấu thanh bằng tai.
- 67 vần theo nhóm (vần kết thúc bằng i/y/o/u, m, n, ng/nh, c/ch, t, p), mỗi vần có tiếng mẫu và cách đánh vần.
- Đánh vần 72 tiếng theo 4 mức: tiếng dễ, có vần, vần có âm cuối, âm đầu là chữ ghép. Cách đánh vần theo sách lớp 1: *bờ – a – ba – huyền – bà*; c đọc là “cờ”, k đọc là “ca” (có tùy chọn đọc “cờ” cho trường dạy Công nghệ giáo dục).
- Quy tắc chính tả c/k, g/gh, ng/ngh; tìm vần của tiếng; đọc câu ngắn rồi chọn tranh.

**Toán (trong phạm vi 10)**
- Đếm, đọc số 0–10; so sánh nhiều – ít; so sánh số và điền dấu >, <, =; số liền trước, liền sau; tìm số còn thiếu.
- Tách số (“5 gồm 2 và mấy?”); phép cộng, trừ (cả với số 0); chọn phép tính đúng với tranh; bảng cộng, bảng trừ.
- Hình tròn, vuông, tam giác, chữ nhật; khối lập phương, khối hộp chữ nhật; dài – ngắn, cao – thấp; xem giờ đúng.

**Viết**: tô chữ cái, chữ ghép, số và tiếng trên nền ô li; phải tô đủ cả nét (dấu, râu ơ/ư, mũ â/ê/ô, gạch đ) mới qua.

**Cho cha mẹ**: nhiều bé trên một máy, lịch sử từng buổi học, thống kê đúng/sai theo từng chữ và dạng bài, thu giọng bé đánh vần để nghe lại, mã PIN cho Góc cha mẹ, thu giọng người thật thay cho âm nào giọng máy đọc chưa chuẩn.

## Chạy trên máy tính

Cần Python 3 (Windows: cài từ python.org; Mac: có sẵn sau khi cài Command Line Tools).

- **Windows**: bấm đúp `start-windows.bat`
- **Mac**: bấm đúp `start-mac.command` (lần đầu: chuột phải → Open)
- **Linux**: `sh start-linux.sh`

App mở ở `http://localhost:8686`. Có thể mở thẳng `index.html` bằng trình duyệt, nhưng khi đó một số trình duyệt chặn micrô và chế độ cài như ứng dụng.

## Cài lên iPhone, iPad, Android

Micrô và chế độ cài đặt cần địa chỉ **https**. Cách đơn giản nhất là bật GitHub Pages cho repo này:

1. GitHub → repo → **Settings → Pages** → Source: *Deploy from a branch* → Branch: `main`, thư mục `/ (root)` → Save.
2. Mở địa chỉ Pages trên máy của bé:
   - iPhone/iPad (Safari): nút Chia sẻ → **Thêm vào MH chính**.
   - Android (Chrome): menu ⋮ → **Cài đặt ứng dụng**.

Lưu ý iPhone: tắt chế độ Im lặng và tăng âm lượng để nghe cô đọc.

## Đồng bộ bằng Supabase (không bắt buộc)

Mỗi gia đình dùng **một tài khoản** (email + mật khẩu). Các bé, màn đã qua, sao, sức mạnh, cài đặt, lịch sử buổi học và thống kê đúng/sai được đồng bộ giữa các máy. App vẫn lưu trên máy trước nên bé học được cả khi mất mạng; có mạng lại thì tự đồng bộ. Bản thu giọng và mã PIN chỉ lưu trên từng máy.

1. Tạo dự án tại [supabase.com](https://supabase.com).
2. **SQL Editor** → dán toàn bộ `supabase/schema.sql` → Run. File tạo 4 bảng (`children`, `progress`, `sessions`, `item_stats`) và bật Row Level Security: mỗi tài khoản chỉ đọc/ghi được dữ liệu của mình.
3. **Authentication → Sign In / Providers → Email**: giữ bật. Nếu muốn đăng ký xong dùng ngay, tắt *Confirm email*; nếu để bật, cha mẹ bấm liên kết trong email rồi đăng nhập. Ở **Authentication → URL Configuration**, đặt *Site URL* là địa chỉ app (ví dụ địa chỉ GitHub Pages).
4. **Project Settings → API**: chép *Project URL* và khóa *anon public* vào `config.js`:
   ```js
   window.BVL1_CONFIG = { supabaseUrl: 'https://xxxx.supabase.co', supabaseAnonKey: 'eyJ...' };
   ```
   Khóa anon được phép công khai; dữ liệu được bảo vệ bởi Row Level Security. Không bao giờ đặt khóa `service_role` vào app.
   Nếu không sửa `config.js`, cha mẹ có thể nhập hai thông tin này ngay trong app.
5. Trong app: màn chọn bé → nút **Đồng bộ** (hoặc Góc cha mẹ) → Tạo tài khoản / Đăng nhập. Máy khác đăng nhập cùng tài khoản sẽ thấy đủ các bé và học tiếp.

Cách gộp khi hai máy cùng học: màn đã qua lấy hợp của hai máy (số sao cao hơn), sao và sức mạnh lấy số lớn hơn, cài đặt theo máy sửa sau cùng; “Chơi lại từ đầu” hoặc “Xóa sao” ở một máy sẽ áp dụng cho mọi máy.

## Cấu trúc

| Đường dẫn | Nội dung |
|---|---|
| `src/app.html` | Mã nguồn app (HTML, CSS, JavaScript trong một file) |
| `index.html`, `voice.js`, `sw.js` | Bản chạy, dựng bằng `python3 tools/build.py` |
| `voice.json` | Giọng cô giáo tạo sẵn (1.200+ câu) |
| `config.js` | Cấu hình Supabase |
| `supabase/schema.sql` | Bảng và chính sách bảo mật Supabase |
| `vendor/supabase.js` | Thư viện supabase-js v2 (bản UMD) để chạy không cần CDN |
| `tools/tts/` | Công cụ tạo giọng đọc (xem README trong thư mục) |
| `tests/` | Kiểm thử tự động bằng Playwright |

Sửa app: sửa `src/app.html` → `python3 tools/build.py` → mở lại trang.

Kiểm thử: `python3 -m http.server 8686` ở thư mục gốc, rồi ở cửa sổ khác chạy `python3 tests/contenttest.py`, `tests/booktest.py`, `tests/cloudtest.py` (đồng bộ dùng Supabase giả lập), `tests/tracetest.py`, `tests/vptest.py` (chụp màn hình nhiều cỡ máy vào `tests/out/`). Cần `pip install playwright` và `playwright install chromium`.

## Về độ chính xác của nội dung

- Tên và âm đọc của chữ, cách đánh vần theo quy ước dạy lớp 1 hiện hành (tham chiếu Quyết định 16/2006/QĐ-BGDĐT và sách giáo khoa Tiếng Việt 1 chương trình 2018). Điểm khác nhau giữa các bộ sách (chữ k đọc “ca” hay “cờ”, tên chữ q) có tùy chọn hoặc ghi chú cho cha mẹ.
- Giọng đọc là giọng máy theo phát âm Hà Nội, chưa phân biệt r/d/gi, s/x, ch/tr. App không bao giờ bắt bé chọn giữa các cặp này bằng tai; cha mẹ nên đọc mẫu hoặc thu giọng thật trong **Duyệt giọng**.
- Phần tập tô dùng chữ in để bé nhận mặt chữ; chữ viết tay ở trường theo mẫu chữ viết của Bộ GD&ĐT có nét khác.
