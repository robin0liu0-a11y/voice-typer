# Voice Typer

一个轻量级的语音输入工具，按住快捷键说话，松开自动识别并输入文字。

## 特性

- 🎤 **语音识别** - 基于 SenseVoice，支持中英日韩粤多语言
- 🪟 **玻璃窗口** - 半透明圆角窗口，美观不打扰
- ⌨️ **快捷输入** - 按住左 Alt 说话，松开自动打字
- 🔇 **静默运行** - 可后台运行，无窗口干扰
- 📦 **完全本地** - 无需 API Key，数据不上传

## 安装

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 安装语音识别引擎

```bash
npm install -g @marswave/coli
```

首次使用会自动下载语音模型 (~60MB) 到 `~/.coli/models/`

### 3. 运行

```bash
python voice_typer_glass.py
```

或双击 `start_glass.bat`

## 使用方法

| 操作 | 功能 |
|------|------|
| **按住左 Alt** | 开始录音 |
| **松开左 Alt** | 停止录音并识别 |
| **ESC** | 退出程序 |

## 开机自启动

1. 按 `Win + R`，输入 `shell:startup`
2. 将 `voice_typer_silent.vbs` 复制到打开的文件夹

## 版本说明

| 文件 | 说明 |
|------|------|
| `voice_typer_glass.py` | 玻璃透明窗口版 (推荐) |
| `voice_typer_simple.py` | 简洁控制台版 |
| `voice_typer_pygame.py` | Pygame 窗口版 |

## 自定义

### 修改快捷键

编辑 `voice_typer_glass.py`，找到：

```python
current_state = keyboard.is_pressed('left alt')
```

将 `'left alt'` 改为其他键，如 `'f7'`、`'ctrl'` 等。

### 修改字体

编辑文件中的字体设置：

```python
font = pygame.freetype.SysFont("KaiTi", 18)
```

可选字体：`Microsoft YaHei`、`SimHei`、`SimSun`、`KaiTi` 等。

## 系统要求

- Windows 10/11
- Python 3.8+
- 麦克风

## 致谢

- 语音识别：[SenseVoice](https://github.com/FunAudioLLM/SenseVoice)
- CLI 工具：[@marswave/coli](https://listenhub.ai/docs/zh/skills/asr)

## License

MIT
