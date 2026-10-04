#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地定制补丁：在「生成资产清单」之前，改 assets/web/main/index.js。

为什么要单独一步：`assets/web/` 是从上游 DeepWrite 桌面端构建出来的渲染层 +
主进程 bundle（见 tools/fetch-runtime.sh 的 WEB_OUT）。这个仓库只放 Android 外壳，
所以任何行为改动都得在**拷进来之后、生成 manifest.json 之前**落到 bundle 上 ——
manifest 按文件字节数登记，改晚了指纹就对不上，RuntimeInstaller 会拒绝解压。

补的两处（都是移植版在真机上跑不通的地方）：

① 去掉 electronDavFetch 第三参
   移植版的 electron 兼容层（assets/web/node_modules/electron/index.js）只实现了
   `net.fetch` / `net.isOnline`，**没有 `net.request`**；而 main bundle 里的
   `electronDavFetch` 第一句就是 `electron.net.request({...})`
   → 一连网盘就抛 `TypeError: electron.net.request is not a function`，
   界面报「连接网盘失败。」

   `WebDavSyncTransport` 的构造函数签名是 `(config, password, request = fetch)`，
   **默认值就是标准 fetch**，而传输层内部本来就按 fetch 语义调用它
   （`redirect: "manual"`，再自己读 status / location 跟跳转）。
   Node/undici 的 fetch 配 `redirect:"manual"` 会原样返回 3xx，语义完全对得上。

② 允许 http 端点
   上游 schema 强制 `url.protocol === "https:"`（本意是要求公网带合法证书的地址）。
   局域网自建 WebDAV 是 http（如 http://192.168.0.59:8765），所以要放开。

用法：
    python3 tools/apply-customizations.py <APK_ROOT>
    # <APK_ROOT> 即 build/apk（内含 assets/）
"""
import os
import sys

TARGET = "assets/web/main/index.js"

PATCHES = [
    {
        "name": "去掉 electronDavFetch 第三参（修「双端同步」传输层）",
        "old": "new WebDavSyncTransport(config, password, electronDavFetch)",
        "new": "new WebDavSyncTransport(config, password)",
    },
    {
        "name": "允许 http 端点（局域网直连）",
        "old": 'url.protocol === "https:"',
        "new": '(url.protocol === "https:" || url.protocol === "http:")',
    },
]


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    apkroot = sys.argv[1]
    path = os.path.join(apkroot, TARGET)
    if not os.path.isfile(path):
        print(f"❌ 找不到 {path}（先跑 tools/fetch-runtime.sh 的第 ④ 步）")
        return 1

    raw = open(path, encoding="utf-8").read()
    text = raw
    for patch in PATCHES:
        name, old, new = patch["name"], patch["old"], patch["new"]
        if new in text:
            print(f"   [=] 已是新版，跳过：{name}")
            continue
        hits = text.count(old)
        if hits != 1:
            print(f"   ❌ 锚点不唯一（{hits} 处），bundle 版本对不上：{name}")
            return 1
        text = text.replace(old, new)
        print(f"   [+] {name}")

    if text == raw:
        print("   [=] 无改动")
        return 0

    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print(f"   定制完成：{TARGET} {len(raw)} -> {len(text)} 字符（{len(text)-len(raw):+d}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
