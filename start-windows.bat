@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PY=
where python >nul 2>nul && set PY=python
if not defined PY (where py >nul 2>nul && set PY=py)
if not defined PY (
  echo Khong tim thay Python. Mo truc tiep file index.html - phan thu giong co the bi chan.
  start "" "index.html"
  pause
  goto :eof
)
echo Be Vao Lop 1 dang chay tai http://localhost:8686  (dong cua so nay de tat)
start "" cmd /c "timeout /t 2 >nul & start http://localhost:8686"
%PY% -m http.server 8686 --bind 127.0.0.1
