#!/bin/sh
# Bấm đúp để mở Bé Vào Lớp 1 trên máy Mac (cần Python 3, có sẵn khi cài Xcode Command Line Tools)
cd "$(dirname "$0")"
echo "Bé Vào Lớp 1 đang chạy tại http://localhost:8686 (đóng cửa sổ này để tắt)"
(sleep 1.5; open "http://localhost:8686") &
exec python3 -m http.server 8686 --bind 127.0.0.1
