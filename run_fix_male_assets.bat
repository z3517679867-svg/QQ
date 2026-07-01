@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo Fix male assets for QQ show website
echo ========================================
echo.

where node >nul 2>nul
if errorlevel 1 (
  echo 没有检测到 Node.js。
  echo 请先确认 cmd 里可以运行：node -v
  echo.
  pause
  exit /b 1
)

node fix_male_assets.js

echo.
echo 处理结束。
echo 如果成功，请上传新的 index.html 和 items.js 到 GitHub。
echo.
pause
