#!/bin/sh
# Chạy Bé Vào Lớp 1 trên Linux: sh start-linux.sh
cd "$(dirname "$0")"
echo "Bé Vào Lớp 1 đang chạy tại http://localhost:8686 (Ctrl+C để tắt)"
(sleep 1.5; xdg-open "http://localhost:8686" >/dev/null 2>&1) &
exec python3 -m http.server 8686 --bind 127.0.0.1
