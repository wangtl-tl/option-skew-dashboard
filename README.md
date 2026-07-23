# 期权偏度信号仪表盘 (GitHub Pages 静态版)

基于本地「商品期权偏度套利实时监控系统」每日导出的**静态数据快照**，托管于 GitHub Pages，提供固定的外网访问链接。

## 数据来源
- 本地偏度监控系统 (TqSdk 天勤量化) 持续运行，端口 `18080`
- `build_pages.py` 每日从本地 API 拉取全市场约 60 个期权品种的偏度信号快照
- 数据含 15 分钟延时（天勤免费版）

## 文件说明
- `index.html` — 仪表盘页面（数据源自 `data.json`）
- `data.json` — 每日数据快照（由 `build_pages.py` 生成）
- `echarts.min.js` — 本地化的图表库（无外部 CDN 依赖）
- `build_pages.py` — 构建脚本（拉取本地 API → 生成静态页）
- `daily_push.bat` — 每日自动构建+推送脚本（由 Windows 任务计划程序调用）

## 动态更新机制
GitHub Pages 为纯静态托管，无法直接访问本地数据源。更新流程：
1. Windows 任务计划程序每日定时（收盘后）运行 `daily_push.bat`
2. 脚本调用 `build_pages.py` 从本地监控系统拉取最新数据 → 生成 `index.html` + `data.json`
3. `git commit && git push` 推送到本仓库
4. GitHub Pages 自动发布，外网链接内容每日刷新

## 本地手动更新
```
cd C:\Users\DELL\WorkBuddy\option-skew-pages
python build_pages.py
git add -A && git commit -m "manual update" && git push
```

## 安全说明
- 本仓库仅含公开的品种偏度信号数据，**不含任何账户、持仓或交易凭证**
- 构建脚本只访问本地 API，不接触 GitHub 凭证
