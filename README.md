# DeepWrite Android

自带 Node 运行时的 DeepWrite Android 客户端。APK 里装着运行时与应用本体，
装到手机上就能用，**不依赖任何外部服务**。

> ⚠️ **这不是 DeepWrite 官方发布。**
> 渲染层取自 DeepWrite **官方原版 1.5.0**（上游 [swjybky/deepwrite](https://github.com/swjybky/deepwrite)，Apache-2.0），
> 应用图标提取自官方原版 APK。DeepWrite 的版权归其官方原作者所有。

## 下载

到 [Releases](https://github.com/133563825as-ai/deepwrite-android/releases/latest) 下
`DeepWrite-Android-*.apk`。最新版见页面上的 `Latest` 标记。

## 装之前先看这 5 条（都是硬门槛）

| # | 条件 | 说明 |
| --- | --- | --- |
| 1 | **必须是 arm64 手机** | APK 里只有 `lib/arm64-v8a/`，x86 模拟器与 32 位机器**装不上** |
| 2 | Android 7.0 及以上 | `minSdk 24` |
| 3 | 允许「安装未知应用」 | 自签名包、非应用商店渠道，Play Protect 可能弹提示 |
| 4 | **手动授予「所有文件访问」** | Android 11+ 不能在弹窗里给：设置 → 应用 → 特殊应用权限 → 所有文件访问。**不授权，作品落不到 `/sdcard/Download/DeepWrite`** |
| 5 | **自己准备模型 API key** | 密钥不随包分发，装上后在应用里填。不配就跑不了智能体 |

首次启动要解压约 5,700 个文件 / 约 103 MB，会明显卡一下，之后正常。
APK 约 50 MB，装完占空间 200 MB 上下。

## 功能

功能来自 DeepWrite 官方原版 1.5.0，手机端在其上做了界面重排。主要几条：

- **写作工作台**：作品、阶段、人设、剧情结构，短篇与长篇
- **智能体对话**：接自己的模型 Provider（DeepSeek / OpenAI / Anthropic 等），
  也可以配置自定义服务
- 输入框上方那张卡片可以直接**切换作品**与**切换阶段**
- **「朱雀检测」交给系统浏览器打开**
- 手机端界面按手机重排（顶栏 / 抽屉 / 单栏）

## 数据放在哪

| 用途 | 路径 |
| --- | --- |
| 作品（文件管理器可见可改） | `/sdcard/Download/DeepWrite` |
| 配置 / 密钥 | 应用私有目录（卸载会一起清掉） |

作品放公共存储是为了文件管理器能直接看、直接改。代价是需要「所有文件访问」权限，
因此**无法上架 Google Play**，只能这样侧载。

## 已知问题

- 「朱雀检测」跳系统浏览器这一步**没有在真机上验证过**
- 小窗（最近任务）图标在部分定制 ROM 上可能显示系统默认图标
- 导出 / 分享到文件的功能未真机验证
- 应用图标来自官方原版 APK，**版权归原作者**（已获原作者同意二次修改与分发）

## 来源与许可

| 部分 | 来源 | 许可 |
| --- | --- | --- |
| 渲染层（应用本体） | DeepWrite 官方原版 1.5.0 · [swjybky/deepwrite](https://github.com/swjybky/deepwrite) | Apache-2.0 |
| 应用图标 | 提取自官方原版 APK（`DeepWrite 1.1.3`） | 版权归原作者 |
| Node 运行时 | Termux 官方仓库 aarch64 Node 26.4.0 + 18 个依赖库 | 见各上游项目 |
| Android 外壳（本仓库） | 本项目 | MIT |

逐项归属与再分发义务见 [`THIRD-PARTY.md`](THIRD-PARTY.md)；
许可证全文见 [`LICENSE`](LICENSE)（MIT）与
[`LICENSE-APACHE-2.0.txt`](LICENSE-APACHE-2.0.txt)（上游渲染层）。
这两份也随 APK 一起分发，在包内 `assets/web/` 下。

---

本仓库只放 **Android 外壳**与打包定义，**不含 DeepWrite 本体源码**。

---

# 本地定制（fisher-FI fork）

> 本 fork 在原版基础上加了两处**行为补丁**，目标是让「双端同步」在**局域网自建 WebDAV**
> 上真正跑通。补丁由 `tools/apply-customizations.py` 在打包流程中自动应用。

## 为什么需要

原版手机端有两条路都走不通（详见 `DeepWrite-Android-1.5.19_安装说明.md`）：

| 问题 | 现象 | 根因 |
| --- | --- | --- |
| 传输层断链 | 点「连接网盘」报「连接网盘失败。」 | 移植版 electron 兼容层只有 `net.fetch`，**没有 `net.request`**；而 main bundle 传的 `electronDavFetch` 第一句就是 `electron.net.request({...})` |
| 只认 https | 填 `http://…` 报「请填写有效的 HTTPS 地址…」 | schema 强制 `url.protocol === "https:"`，局域网地址是 http |

## 补了什么

`tools/apply-customizations.py`，作用在 `assets/web/main/index.js`：

```diff
- new WebDavSyncTransport(config, password, electronDavFetch)
+ new WebDavSyncTransport(config, password)
```

`WebDavSyncTransport` 的构造函数签名是 `(config, password, request = fetch)`——**默认就是标准 fetch**，传输层内部本来就按 fetch 语义调用它（`redirect: "manual"` 后自己读 status / location 跟跳转）。Node/undici 的 fetch 配 `redirect:"manual"` 会原样返回 3xx，语义完全对得上。

```diff
- url.protocol === "https:"
+ (url.protocol === "https:" || url.protocol === "http:")
```

放开 http，用于局域网自建 WebDAV。

## 接入点

补丁在 `tools/fetch-runtime.sh` 的 **④a3** 步执行，位置很关键：

```
④  拷贝 Web 产物到 assets/web/
④a 补齐依赖闭包
④a2 校验 utility
④a3 应用本地定制补丁   ← 在这里
④b 生成资产清单         ← 必须在这之前
```

`assets/manifest.json` 按**文件字节数**登记每个文件，`RuntimeInstaller` 靠它解压。
改晚了指纹就对不上，文件永远落不到设备上。所以补丁必须卡在清单生成之前。

## 构建

```bash
bash tools/fetch-runtime.sh     # 拉运行时 + 组织 assets（含定制补丁）
ANDROID_SDK_ROOT=/path/to/sdk bash build.sh
```

> ⚠️ 仍然需要一份上游 DeepWrite 的 **Web 产物**（`out-web`：renderer + main + server*.mjs + node_modules）。
> 本仓库不含它——那是上游桌面端构建出来的东西。

## 配套：局域网自建 WebDAV

手机连电脑的完整做法见 `docs/局域网同步.md`。

