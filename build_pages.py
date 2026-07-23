#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_pages.py - 偏度套利监控 → GitHub Pages 静态版构建脚本

功能：
  从本地运行的偏度监控系统 (http://127.0.0.1:18080) 拉取全量数据快照，
  生成自包含静态页面 (index.html + data.json) 供 GitHub Pages 托管。

设计：
  - 原 templates/index.html 依赖本地 /api/* 后端；本脚本将其改造为读取
    同目录下的 data.json（window.SKEW_DATA），使其可在纯静态 Pages 上运行。
  - 每天由 Windows 任务计划程序调用本脚本 + git push，实现"动态更新"。

注意：
  - 本脚本只访问本地 API，不需要任何 GitHub 凭证。
  - ECharts 已本地化 (./echarts.min.js)，无外部 CDN 依赖。
"""
import json
import os
import urllib.request
import urllib.error
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
SRC_HTML = r"C:\Users\DELL\WorkBuddy\偏度套利\templates\index.html"
OUT_HTML = os.path.join(BASE, "index.html")
OUT_JSON = os.path.join(BASE, "data.json")
API = "http://127.0.0.1:18080"


def api_get(path):
    url = API + path
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def transform_html(src):
    """将依赖本地 API 的 index.html 改造为读取 data.json 的静态版。"""
    # 1. 注入 ensureData 数据加载函数
    src = src.replace(
        "// ── 数据获取 ──\n",
        """// ── 数据获取 (GitHub Pages 静态版: 从 data.json 加载) ──
let __dataLoaded = false;
async function ensureData() {
  if (__dataLoaded && window.SKEW_DATA) return;
  const resp = await fetch('./data.json');
  if (!resp.ok) throw new Error('data.json 加载失败: ' + resp.status);
  window.SKEW_DATA = await resp.json();
  __dataLoaded = true;
}
""",
        1,
    )
    # 2. fetchOverview: status + overview 改为读 SKEW_DATA
    src = src.replace(
        """    // 获取系统状态
    const sResp = await fetch('/api/status');
    if (sResp.ok) {
      const status = await sResp.json();
      updateStatusBar(status);
    }

    // 获取偏度总览数据
    const r = await fetch('/api/skew/overview');
    if (!r.ok) throw new Error('API error: ' + r.status);
    const data = await r.json();""",
        """    await ensureData();
    const status = window.SKEW_DATA.status;
    updateStatusBar(status);
    const data = window.SKEW_DATA.overview;""",
        1,
    )
    # 3. openPanel: detail 改为读 SKEW_DATA.details[product]
    src = src.replace(
        """    const r = await fetch(`/api/skew/detail?symbol=${product}`);
    if (!r.ok) throw new Error('API error');
    currentDetail = await r.json();""",
        """    await ensureData();
    currentDetail = window.SKEW_DATA.details[product];
    if (!currentDetail) throw new Error('该品种暂无数据');""",
        1,
    )
    # 4. manualRefresh: 静态版无后端刷新，改为提示
    src = src.replace(
        """async function manualRefresh() {
  try {
    await fetch('/api/refresh', { method: 'POST' });
    document.getElementById('statusText').textContent = '刷新已触发...';
    setTimeout(fetchOverview, 3000);
  } catch(e) {
    console.error('刷新失败:', e);
  }
}""",
        """async function manualRefresh() {
  document.getElementById('statusText').textContent = '静态版数据每日自动更新';
}""",
        1,
    )
    # 5. ECharts CDN → 本地文件
    src = src.replace(
        '<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>',
        '<script src="./echarts.min.js"></script>',
        1,
    )
    return src


def main():
    print(f"[{datetime.now():%H:%M:%S}] 拉取偏度监控数据...")
    status = api_get("/api/status")
    overview = api_get("/api/skew/overview")
    products = overview.get("products", [])
    ready = [p for p in products if p.get("status") == "ready"]
    details = {}
    print(f"  共 {len(products)} 品种, {len(ready)} 个 ready, 拉取详情中...")
    for i, p in enumerate(ready, 1):
        sym = p.get("product")
        try:
            details[sym] = api_get(f"/api/skew/detail?symbol={sym}")
        except Exception as e:
            print(f"  [跳过] {sym} 详情拉取失败: {e}")
        if i % 15 == 0:
            print(f"  进度 {i}/{len(ready)}")
    # 合并信号计数到 overview（前端 fetchOverview 读取）
    overview["signal_count"] = status.get("signal_count", 0)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "overview": overview,
        "details": details,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    with open(SRC_HTML, "r", encoding="utf-8") as f:
        html = f.read()
    html = transform_html(html)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(
        f"  生成 index.html ({len(html)//1024}KB), "
        f"data.json ({len(details)} 品种详情, {os.path.getsize(OUT_JSON)//1024}KB)"
    )
    print("构建完成。")


if __name__ == "__main__":
    main()
