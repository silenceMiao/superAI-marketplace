# superAI Marketplace

`superAI-marketplace` 是面向 Claude Code 与 Codex 的插件目录仓库，用于声明、分发和版本化可安装插件；它不是插件开发源码仓库。

当前已收录一个插件：[`superlooper`](plugins/superlooper/README.md)。该插件把工程需求组织为可审核、可追溯的多 agent 开发流程，并同时提供 Claude Code 与 Codex 入口。

## 当前目录结构

```text
superAI-marketplace/
├── README.md
├── .claude-plugin/
│   └── marketplace.json        # Claude Code Marketplace 元数据
├── .agents/
│   └── plugins/
│       └── marketplace.json    # Codex Marketplace 元数据
├── .superlooper-marketplace-sync.json
└── plugins/
    └── superlooper/            # 当前唯一的可安装插件
```

两个 Marketplace manifest 都通过相对路径 `./plugins/superlooper` 指向同一个 Superlooper 插件目录。各平台的安装、使用、升级和卸载方式请参阅 [Superlooper README](plugins/superlooper/README.md)。

## 当前目录

| 插件 | 版本 | 说明 |
| --- | --- | --- |
| [superlooper](plugins/superlooper/) | 1.1.1 | Claude Code 与 Codex 双平台的 AI 并行编排工作流。 |

## 扩展边界

后续新增插件时，在 `plugins/<plugin-id>/` 创建独立的安装闭包，并同步将插件条目加入 Claude Code 与 Codex 的 Marketplace manifest。插件所需的 skills、agents、scripts、schemas 和运行时约束随所属插件发布，不在 Marketplace 根目录建立全局 skill 注册中心。

MCP 属于插件级或宿主级集成边界。未来插件可以声明或说明自身需要的 MCP 配置；Marketplace 根目录只负责插件发现与定位，不承担全局 MCP 路由、共享密钥、跨插件权限或运行协议。

## 发布边界

不要将以下内容纳入 `plugins/<plugin-id>/`：

- `.superlooper/` 运行时产物；
- `.claude/` 本地开发上下文；
- `__pycache__/`、`dist/` 和本地验证缓存；
- 用户配置、认证文件、令牌、密码或其他密钥。

每个插件必须保持自身 manifest、安装闭包和发布验证一致。
