<p align="center"><a href="README.md">🇺🇸 English</a> | <a href="README.zh.md">🇨🇳 中文</a></p>

<h1 align="center">SciRate CLI</h1>

<p align="center"><img alt="Python 3.11 及以上" src="https://img.shields.io/badge/python-3.11%2B-blue"> <img alt="AGPL-3.0" src="https://img.shields.io/badge/license-AGPL--3.0-blue"></p>

![SciRate 命令行框架中的论文](assets/scirate-cli-banner.png)

## 引言

这是 [SciRate](https://scirate.com) 与 arXiv 的非官方客户端，运行时不依赖第三方包。通过 JSON 读取论文、分类列表、评论与点赞者，并通过标准输入输出 MCP 提供同一组读取能力。在 macOS 上可以借用 Chrome 或 Safari 的现有会话执行明确指定的互动，不导出 Cookie。

0.3.0 是首次测试版。SciRate 网页接口不是稳定的公开 API；Cloudflare 可能阻止直接读取，客户端会报告而不会绕过。浏览器互动要求已经登录；离线测试通过不代表真实账号互动已经验证。

## 安装

需要 Python 3.11 或更高版本。可安装发布页的 wheel 或执行：

```sh
pipx install git+https://github.com/JunkaiWang-TheoPhy/SciRate-CLI.git@v0.3.0
scirate --version
scirate --help
```

也可克隆仓库，在虚拟环境中执行 `python -m pip install .`。GitHub 发布不代表已经发布到 PyPI。

## 命令

```sh
scirate paper 1509.01147
scirate community 1509.01147
scirate feed quant-ph
scirate scites USERNAME --page 1
scirate import saved-page.html --source-url https://scirate.com/arxiv/quant-ph
scirate auth-status --browser Chrome
scirate browser-read --browser Chrome
scirate act scite 1509.01147
scirate act unscite 1509.01147
scirate act subscribe quant-ph
scirate act unsubscribe quant-ph
scirate act comment 1509.01147 --content '经过思考的评论'
scirate act reply COMMENT_ID --content '回复内容'
scirate receipt TICKET
```

成功时标准输出为 `{"ok":true,"data":...}`；失败时标准错误输出为 `{"ok":false,"error":...}`，状态码为 1，语法错误返回 2。互动返回的是待处理票据，不是成功证明。应在同一标签页查询回执，刷新后确认最终状态。未知票据可能意味着换了标签页、刷新页面或票据无效，不要直接重发不确定的评论。

浏览器桥接仅支持 macOS。在 Chrome 的 **macOS 顶部菜单栏** 中启用 **显示 > 开发者 > 允许 Apple 事件中的 JavaScript**，不是在设置页面搜索。Safari 的开发菜单有对应选项。自行打开 SciRate、完成正常网页验证并登录。建议只保留目标标签页，桥接会使用第一个匹配的标签页。这项权限范围较大，用完可关闭。

## MCP

```json
{"mcpServers":{"scirate":{"command":"scirate","args":["mcp"]}}}
```

提供六个只读工具：`paper`、`community`、`feed`、`scites`、`browser_read`、`auth_status`。写操作仅通过 CLI 执行。使用标准输入输出逐行 JSON-RPC，不启动 HTTP 服务。宿主 PATH 受限时填写已安装命令的绝对路径。

## 存储与证据

HTTP 缓存一小时。可通过 `SCIRATE_DATA_DIR` 指定本地目录，默认兼容旧版的 `~/.local/share/scirate-tools/data`。文件原子写入并仅允许所有者读写。导入页面可能含私人会话信息，不要提交缓存或 HTML 归档。

缺失字段保持未知，隐藏或删除的评论不暴露正文。参见[来源记录](docs/sources.md)、[验证记录](docs/verification.md)和[安全说明](SECURITY.md)。尚未实现自动登录、评论编辑删除、管理功能和 TUI。

## 开发

```sh
python -m unittest discover -s tests -v
python -m compileall -q scirate.py community.py browser.py
python -m pip install build
python -m build
```

测试使用模拟上游结构的网页和网络、浏览器响应，不发布公开内容。CI 检查 Python 3.11、3.12、3.13。参见[贡献说明](docs/contributing.md)。

## 目录

- `docs/`：接口调研与命令设计
- `scirate.py`、`community.py`、`browser.py`：客户端、解析和浏览器桥接
- `tests/`：回归测试
- `assets/`：视觉资料

## 许可证

采用 GNU AGPL-3.0-only，详见 [LICENSE](LICENSE)。与 SciRate、arXiv 无官方关联，没有复制上游实现代码。
