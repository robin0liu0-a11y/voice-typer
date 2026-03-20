# Voice Typer

轻量级语音输入工具 - 按住快捷键说话，松开自动打字。

## 安装

### 1. 安装 Python 依赖

```bash
pip install sounddevice soundfile numpy keyboard pygame
```

### 2. 安装语音识别引擎

```bash
npm install -g @marswave/coli
```

首次使用会自动下载语音模型 (~60MB) 到 `~/.coli/models/`

### 3. 安装技能

```bash
# Claude Code
npx skills add <skill-directory>

# OpenClaw
clawhub add <skill-directory>
```

## 使用方法

### 启动语音输入

```bash
voice-typer
```

或使用 slash 命令：
```
/voice-typer
```

### 快捷键

| 按键 | 功能 |
|------|------|
| **按住左 Alt** | 开始录音 |
| **松开左 Alt** | 停止录音并识别 |
| **ESC** | 退出程序 |

### 后台运行

```bash
voice-typer --silent
```

无窗口后台运行，适合开机自启。

## 配置选项

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `--shortcut` | `left alt` | 录音快捷键 |
| `--font` | `KaiTi` | 显示字体 |
| `--style` | `glass` | 窗口风格 (glass/simple) |
| `--silent` | - | 后台静默运行 |

### 示例

```bash
# 使用 F7 快捷键
voice-typer --shortcut f7

# 使用黑体字体
voice-typer --font SimHei

# 简洁控制台模式
voice-typer --style simple

# 后台运行
voice-typer --silent
```

## 开机自启动

### Windows

1. 按 `Win + R`，输入 `shell:startup`
2. 将 `scripts/startup.vbs` 复制到打开的文件夹

### macOS

将 `scripts/voice-typer.plist` 复制到 `~/Library/LaunchAgents/`

## 支持的语言

| 语言 | 代码 |
|------|------|
| 中文 | zh |
| 英文 | en |
| 日语 | ja |
| 韩语 | ko |
| 粤语 | yue |

## 系统要求

- Windows 10/11, macOS 10.15+, Linux
- Python 3.8+
- 麦克风设备
- Node.js 16+ (用于 coli)

## 技术架构

```
voice-typer/
├── skill/
│   ├── SKILL.md           # 技能说明
│   ├── skill.json         # 技能配置
│   └── scripts/
│       ├── voice_typer.py     # 主程序
│       ├── install.py         # 安装脚本
│       └── startup.vbs        # Windows 开机启动
└── README.md
```

## 故障排除

### 录音无声音

检查麦克风权限和默认录音设备。

### 识别失败

1. 确认 `coli` 已安装: `coli asr --help`
2. 检查模型是否下载: `ls ~/.coli/models/`

### 快捷键无效

1. 确认程序在前台运行
2. 尝试其他快捷键: `--shortcut f7`

## 致谢

- 语音识别: [SenseVoice](https://github.com/FunAudioLLM/SenseVoice)
- CLI 工具: [@marswave/coli](https://listenhub.ai/docs/zh/skills/asr)

## License

MIT
