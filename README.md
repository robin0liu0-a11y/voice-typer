# Voice Typer

一个轻量级的语音输入工具，按住快捷键说话，松开自动识别并输入文字。

![Voice Typer](promo_image.png)

## 特性

- 🎤 **语音识别** - 基于 SenseVoice，支持中英日韩粤多语言
- 🪟 **玻璃窗口** - 半透明圆角窗口，美观不打扰
- ⌨️ **快捷输入** - 按住左 Alt 说话，松开自动打字
- 🔇 **静默运行** - 可后台运行，无窗口干扰
- 📦 **完全本地** - 无需 API Key，数据不上传
- 🔌 **Skill 支持** - 支持 Claude Code / OpenClaw 集成

## 安装

### 方式一：直接安装

```bash
# 1. 安装 Python 依赖
pip install sounddevice soundfile numpy keyboard pygame

# 2. 安装语音识别引擎
npm install -g @marswave/coli

# 3. 运行
python voice_typer_glass.py
```

### 方式二：作为 Skill 安装 (Claude Code / OpenClaw)

```bash
# Claude Code
npx skills add https://github.com/robin0liu0-a11y/voice-typer

# OpenClaw
clawhub add https://github.com/robin0liu0-a11y/voice-typer
```

安装后可通过命令启动：
```
/voice-typer
```

## 使用方法

| 操作 | 功能 |
|------|------|
| **按住左 Alt** | 开始录音 |
| **松开左 Alt** | 停止录音并识别 |
| **ESC** | 退出程序 |

## CLI 命令

```bash
# 基本启动
voice-typer

# 自定义快捷键
voice-typer --shortcut f7

# 后台静默运行
voice-typer --silent

# 安装依赖
voice-typer --install
```

## 开机自启动

### Windows

1. 按 `Win + R`，输入 `shell:startup`
2. 将 `skill/scripts/startup.vbs` 复制到打开的文件夹

### macOS

将 `skill/scripts/voice-typer.plist` 复制到 `~/Library/LaunchAgents/`

## 自定义

### 修改快捷键

编辑 `voice_typer_glass.py`，找到：

```python
current_state = keyboard.is_pressed('left alt')
```

改为其他键：`'f7'`、`'ctrl'`、`'space'` 等。

### 修改字体

```python
font = pygame.freetype.SysFont("KaiTi", 18)
```

可选：`Microsoft YaHei`、`SimHei`、`SimSun` 等。

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
- Node.js 16+ (用于 coli)
- 麦克风设备

## 故障排除

### 录音无声音

检查麦克风权限和默认录音设备设置。

### 识别失败

1. 确认 `coli` 已安装: `coli asr --help`
2. 检查模型: `ls ~/.coli/models/`
3. 首次使用会自动下载模型 (~60MB)

### 快捷键无效

1. 确认程序正在运行
2. 尝试其他快捷键: `--shortcut f7`

## 项目结构

```
voice-typer/
├── skill/                      # Skill 集成
│   ├── SKILL.md               # 技能说明
│   ├── skill.json             # 技能配置
│   └── scripts/
│       ├── voice_typer.py     # 主程序
│       ├── voice-typer        # CLI 入口
│       ├── voice-typer.bat    # Windows 启动
│       ├── install.py         # 安装脚本
│       └── startup.vbs        # 开机启动
├── voice_typer_glass.py       # 玻璃版 (推荐)
├── voice_typer_simple.py      # 简洁版
├── README.md
└── LICENSE
```

## 致谢

- 语音识别：[SenseVoice](https://github.com/FunAudioLLM/SenseVoice)
- CLI 工具：[@marswave/coli](https://listenhub.ai/docs/zh/skills/asr)

## License

MIT
