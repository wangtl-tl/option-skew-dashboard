@echo off
chcp 65001 >nul
cd /d C:\Users\DELL\WorkBuddy\option-skew-pages

echo [%date% %time%] 开始构建并推送偏度监控静态页...
"C:\Users\DELL\WorkBuddy\偏度套利\.venv\Scripts\python.exe" build_pages.py
if errorlevel 1 (
  echo 构建失败，跳过推送
  exit /b 1
)

git add -A
git commit -m "daily update %date% %time%" >nul 2>&1
if errorlevel 1 (
  echo 无变更，无需提交
) else (
  git push
  echo 已推送到 GitHub Pages
)
echo 完成。
