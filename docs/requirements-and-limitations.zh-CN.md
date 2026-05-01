# 依赖与限制

Video Subtitle Parser 是一个本地 CLI。它依赖平台页面、`yt-dlp`、本地媒体工具和可选 ASR，把视频链接变成 AI Agent 可以读取的本地素材包。它不是绕过平台规则、登录墙、版权限制或网络限制的工具。

## 运行依赖

| 依赖 | 是否必需 | 用途 |
| --- | --- | --- |
| Python 3.9+ | 必需 | CLI 运行和包安装 |
| `requests` | 必需 | 抖音移动分享页解析和媒体下载 |
| `yt-dlp` | 必需 | YouTube / Bilibili 元数据、字幕、音频和视频下载 |
| `imageio-ffmpeg` | 必需 | 提供 `ffmpeg`，用于音频抽取 |
| `opencc-python-reimplemented` | 必需 | 繁简转换和中文清理 |
| `mlx-whisper` | 可选 | 字幕不可用时的本地 ASR 兜底 |

检查环境：

```bash
video-subtitle-parser --check
```

如果只看到 `mlx-whisper` optional missing，是可以接受的。它只有在需要本地 ASR 兜底时才必须安装。

## 系统要求

- 本地需要足够磁盘空间保存文字稿、metadata、音频和可选 MP4。
- ASR 会消耗时间和内存。默认模型是 `mlx-community/whisper-large-v3-turbo`。
- `mlx-whisper` 主要面向 Apple Silicon 环境。其他 ASR 后端在路线图中，但第一版没有暴露。
- 工具会在 `out-dir/bin/ffmpeg` 创建指向 `imageio-ffmpeg` 的软链接，并把该目录临时加入当前进程的 `PATH`。
- 元数据、字幕和媒体下载都需要网络访问。

## 浏览器、Chrome 与远程调试

当前稳定版不控制 Chrome，也不使用 Chrome 远程调试。

这意味着：

- 不需要浏览器自动化；
- 不读取 Chrome Profile；
- 不复用浏览器登录态；
- 不打开 Chrome remote debugging 端口；
- 需要浏览器登录态才能访问的视频可能失败。

cookie / 浏览器会话交接以后可能会做，但不属于当前稳定契约。

## 登录态与私密内容

当前稳定 CLI 不接收 cookie、账号密码或浏览器 Profile。

因此：

- 默认输入应该是公开视频；
- 私密、好友可见、年龄限制、地区限制、会员专属、登录后可见的视频可能失败；
- B 站有时页面能看，但字幕不可用或需要登录态；
- YouTube 字幕和元数据可能受地区、账号、年龄状态、网络环境影响；
- 抖音分享页结构可能变化，也可能阻断请求。

不要把账号凭据、cookie、私密 token 放进 issue 或公开日志。

## 网络与请求频率

平台接口可能限流、阻断、重定向，或只返回部分数据。

常见情况：

- YouTube subtitle/timedtext 接口在重复访问后可能返回 HTTP 429；
- `yt-dlp` extractor 可能因为平台页面/API 变化而短期失效；
- B 站可能能拿到 metadata，但拿不到字幕；
- 抖音移动分享页可能没有预期的 router data 或媒体 URL；
- 媒体下载可能失败，但字幕生成的文字稿仍然成功。

建议：

- 不要在字幕接口失败后高频重试；
- 被限流时稍后重试，或换干净网络；
- 合法且合适时使用 ASR 兜底；
- 保留 metadata，方便后续审计失败原因。

## 平台限制

### 抖音

- 使用 `https://www.iesdouyin.com/share/video/<id>/` 和移动端 UA。
- 解析 `window._ROUTER_DATA`，页面结构变化可能导致失败。
- 如果分享页给出 `/playwm/`，会优先尝试 `/play/`，但不保证一定无水印。
- 抖音路径会下载视频并抽取音频，再进行 ASR。
- 不使用浏览器登录、cookie 或 Chrome Profile。

### YouTube

- 使用 `yt-dlp` 获取 metadata、人工字幕、自动字幕、音频和可选视频。
- 优先字幕，失败后才走 ASR。
- 字幕可能被关闭、不可用、自动生成错误、翻译不准、被限流，或受地区/账号影响。
- `--download-video` 是可选项；不加时通常只保留文字稿素材。
- 重复访问字幕接口可能触发限流，遇到 HTTP 429 不要循环请求。

### Bilibili

- 使用 `yt-dlp --ignore-config`。
- 部分视频没有字幕、字幕为空、字幕需要登录态，或 metadata 受地区/账号影响。
- 字幕失败且 ASR 可用时，会下载音频并走本地 ASR。
- `--download-video` 是可选项，视频下载失败不一定影响已生成的文字稿。

## 媒体、截图与水印

下载 MP4 只是为了复查和截帧工作流，不代表所有帧都可以直接发布。

发布截图前必须人工检查：

- 平台 UI；
- 内嵌字幕；
- 作者标记；
- 水印；
- 被裁掉一半的 logo；
- 私密或敏感内容。

如果拿不到干净可用帧，应该生成原创概念图，或使用其他合法来源。

## 准确性限制

- ASR 可能听错人名、数字、语言和领域术语。
- 自动字幕可能错误或不完整。
- `--term-file` 只做字面 `wrong=>right` 替换，不是完整校稿器。
- `--initial-prompt` 可以改善 ASR 识别，但不能保证正确。
- 发布或引用前，必须人工复查清理稿。

## 文件与隐私限制

- 生成的文字稿可能包含版权、私密、个人或敏感内容。
- 不要把 MP4、MP3、文字稿、字幕、metadata 提交到公开仓库，除非项目明确把它们作为 fixtures。
- `.gitignore` 默认排除了常见媒体和文字稿产物。
- 建议把输出放在项目内 `materials/` 或 `runs/` 目录，方便后续 Agent 审计来源。

## 已规划但未稳定开放

以下内容属于路线图，不是当前稳定功能：

- TikTok 支持；
- 快手/Kwai 支持；
- cookie / 浏览器会话交接；
- Chrome 远程调试集成；
- 批量队列；
- `mlx-whisper` 之外的 ASR 后端；
- JSONL 分段导出。
