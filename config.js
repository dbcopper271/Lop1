// Cấu hình đồng bộ Supabase (không bắt buộc).
// Lấy ở Supabase Dashboard → Project Settings → API: "Project URL" và khóa "anon public".
// Khóa anon được phép để công khai: dữ liệu mỗi gia đình được bảo vệ bằng Row Level Security (xem supabase/schema.sql).
// Để trống thì cha mẹ vẫn có thể nhập trong app: màn chọn bé → nút "Đồng bộ".
window.BVL1_CONFIG = {
  supabaseUrl: '',
  supabaseAnonKey: ''
};
