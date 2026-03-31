#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Voice Typer v3.6 - 玻璃透明版 + Get笔记 + 系统托盘
按住 Alt+C 说话，松开自动打字
按住 Alt+V 说话，松开保存到 Get笔记
右键托盘图标退出
"""

import os
import sys
import subprocess
import shutil
import threading
import time
import ctypes
import tempfile
import json
import logging
import urllib.request
import urllib.error
from pathlib import Path
from ctypes import windll, c_int, byref, sizeof

# ========== 日志配置 ==========
LOG_FILE = Path(tempfile.gettempdir()) / "voice_typer.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
    ]
)
log = logging.getLogger(__name__)

# ========== 单实例检查 ==========
def check_single_instance():
    """确保只有一个实例运行"""
    import socket
    lock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        lock_socket.bind(('127.0.0.1', 51234))
        return lock_socket
    except OSError:
        log.error("已有 Voice Typer 在运行")
        sys.exit(1)

# 单实例锁
_instance_lock = check_single_instance()

# Windows 虚拟键码
VK_LMENU = 0xA4  # 左 Alt
VK_RMENU = 0xA5  # 右 Alt
VK_V = 0x56      # V 键
VK_C = 0x43      # C 键

# Get笔记 API 配置 (从 .env 文件或环境变量读取)
def load_getnote_config():
    """加载 Get笔记 API 配置"""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key in ("GETNOTE_API_KEY", "GETNOTE_CLIENT_ID"):
                os.environ[key] = value

    return (
        os.environ.get("GETNOTE_API_KEY", ""),
        os.environ.get("GETNOTE_CLIENT_ID", "")
    )

GETNOTE_API_KEY, GETNOTE_CLIENT_ID = load_getnote_config()
GETNOTE_API_URL = "https://openapi.biji.com"

# 配置
SAMPLE_RATE = 16000
CHANNELS = 1
WINDOW_WIDTH = 300
WINDOW_HEIGHT = 50

# 状态
_state_lock = threading.Lock()

class State:
    is_recording = False
    audio_data = []
    stream = None
    last_key_state = False
    last_alt_v_state = False
    record_start_time = None
    running = True
    status_text = ""
    status_color = (50, 50, 50)
    window_visible = False
    hwnd = None
    processing = False
    hwnd_set = False
    note_mode = False

state = State()


# ========== 按键检测 (Windows API) ==========
def is_left_alt_pressed():
    """使用 Windows API 精确检测左 Alt 键状态"""
    result = windll.user32.GetAsyncKeyState(VK_LMENU)
    return result & 0x8000 != 0

def is_right_alt_pressed():
    """检测右 Alt 键状态"""
    result = windll.user32.GetAsyncKeyState(VK_RMENU)
    return result & 0x8000 != 0

def is_v_pressed():
    """检测 V 键状态"""
    result = windll.user32.GetAsyncKeyState(VK_V)
    return result & 0x8000 != 0

def is_alt_v_pressed():
    """检测 Alt + V 组合键"""
    return is_left_alt_pressed() and not is_right_alt_pressed() and is_v_pressed()

def is_c_pressed():
    """检测 C 键状态"""
    result = windll.user32.GetAsyncKeyState(VK_C)
    return result & 0x8000 != 0

def is_alt_c_pressed():
    """检测 Alt + C 组合键"""
    return is_left_alt_pressed() and not is_right_alt_pressed() and is_c_pressed()


# ========== 小龙虾绘制 ==========
def draw_crayfish(surface, x, y, scale=1.0):
    """绘制一只可爱的小龙虾"""
    import pygame

    # 颜色
    red = (220, 80, 60)
    dark_red = (180, 50, 40)
    orange = (255, 140, 0)
    white = (255, 255, 255)
    black = (30, 30, 30)

    s = scale
    px = int(x * s) if scale != 1.0 else x

    # 身体 (椭圆形)
    body_rect = pygame.Rect(px - 12, y - 6, 24, 12)
    pygame.draw.ellipse(surface, red, body_rect)
    pygame.draw.ellipse(surface, dark_red, body_rect, 1)

    # 头部
    head_rect = pygame.Rect(px - 18, y - 5, 12, 10)
    pygame.draw.ellipse(surface, red, head_rect)

    # 眼睛 (在触角柄上)
    pygame.draw.circle(surface, white, (px - 14, y - 10), 3)
    pygame.draw.circle(surface, black, (px - 14, y - 10), 1.5)
    pygame.draw.circle(surface, white, (px - 8, y - 10), 3)
    pygame.draw.circle(surface, black, (px - 8, y - 10), 1.5)

    # 触角
    pygame.draw.line(surface, dark_red, (px - 16, y - 8), (px - 20, y - 15), 1)
    pygame.draw.line(surface, dark_red, (px - 10, y - 8), (px - 8, y - 15), 1)

    # 大钳子 (左边)
    claw_points_left = [
        (px - 22, y + 2),
        (px - 28, y - 2),
        (px - 30, y - 6),
        (px - 26, y - 4),
        (px - 22, y - 2)
    ]
    pygame.draw.polygon(surface, red, claw_points_left)
    pygame.draw.polygon(surface, dark_red, claw_points_left, 1)

    # 大钳子 (右边)
    claw_points_right = [
        (px + 10, y + 2),
        (px + 16, y - 2),
        (px + 18, y - 6),
        (px + 14, y - 4),
        (px + 10, y - 2)
    ]
    pygame.draw.polygon(surface, red, claw_points_right)
    pygame.draw.polygon(surface, dark_red, claw_points_right, 1)

    # 尾巴扇形
    tail_points = [
        (px + 10, y),
        (px + 18, y - 4),
        (px + 22, y),
        (px + 18, y + 4)
    ]
    pygame.draw.polygon(surface, orange, tail_points)
    pygame.draw.polygon(surface, dark_red, tail_points, 1)

    # 腿 (简化)
    for i in range(3):
        leg_x = px - 6 + i * 6
        pygame.draw.line(surface, dark_red, (leg_x, y + 4), (leg_x - 2, y + 8), 1)
        pygame.draw.line(surface, dark_red, (leg_x, y + 4), (leg_x + 2, y + 8), 1)


# ========== Windows API 设置圆角和透明 ==========
def setup_window(hwnd):
    """设置窗口圆角和透明效果"""
    # 设置圆角 (Win11)
    DWMWA_WINDOW_CORNER_PREFERENCE = 33
    DWMWCP_ROUND = 2

    windll.dwmapi.DwmSetWindowAttribute(
        hwnd,
        DWMWA_WINDOW_CORNER_PREFERENCE,
        byref(c_int(DWMWCP_ROUND)),
        sizeof(c_int)
    )

    # 设置窗口透明度
    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x00080000
    LWA_ALPHA = 0x00000002

    ex_style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style | WS_EX_LAYERED)
    windll.user32.SetLayeredWindowAttributes(hwnd, 0, 220, LWA_ALPHA)  # 220/255 透明度


# ========== Pygame 状态窗口 ==========

def pygame_window_thread():
    """pygame 窗口线程 - 仅在主显示器显示"""
    try:
        import pygame
        import pygame.freetype

        pygame.init()
        pygame.display.set_caption("Voice Typer")

        # 获取主显示器尺寸 (使用 Windows API，仅主显示器)
        SM_CXSCREEN = 0  # 主显示器宽度
        SM_CYSCREEN = 1  # 主显示器高度
        screen_width = windll.user32.GetSystemMetrics(SM_CXSCREEN)
        x = (screen_width - WINDOW_WIDTH) // 2
        y = 80

        # 创建窗口 - 指定在主显示器上
        window = pygame.display.set_mode(
            (WINDOW_WIDTH, WINDOW_HEIGHT),
            pygame.NOFRAME
        )

        # 获取窗口句柄并设置样式
        state.hwnd = pygame.display.get_wm_info()['window']
        state.hwnd_set = True

        # 设置窗口位置和置顶 (确保在主显示器)
        HWND_TOPMOST = -1
        SWP_NOSIZE = 0x0001
        SWP_NOMOVE = 0x0002
        SWP_SHOWWINDOW = 0x0040

        # 立即设置位置，确保在主显示器
        windll.user32.SetWindowPos(
            state.hwnd,
            HWND_TOPMOST,
            x, y, WINDOW_WIDTH, WINDOW_HEIGHT,
            SWP_SHOWWINDOW
        )

        # 设置圆角和透明
        setup_window(state.hwnd)

        # 初始隐藏
        windll.user32.ShowWindow(state.hwnd, 0)

        # 字体 - 楷体
        try:
            font = pygame.freetype.SysFont("KaiTi", 18)
        except Exception:
            try:
                font = pygame.freetype.SysFont("楷体", 18)
            except Exception:
                font = pygame.freetype.SysFont("Microsoft YaHei UI", 16)

        clock = pygame.time.Clock()
        bg_color = (255, 255, 255, 200)  # 白色半透明背景

        while state.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return  # 不设置 running=False，让主循环决定

            if state.window_visible and state.status_text:
                # 绘制背景
                window.fill(bg_color[:3])  # pygame 不支持 alpha 填充

                # 绘制小龙虾 (趴在右下角)
                draw_crayfish(window, WINDOW_WIDTH - 25, WINDOW_HEIGHT - 12, 1.0)

                # 绘制文字 (黑色)
                text_rect = font.get_rect(state.status_text)
                text_x = (WINDOW_WIDTH - text_rect.width) // 2
                text_y = (WINDOW_HEIGHT - text_rect.height) // 2
                font.render_to(window, (text_x, text_y), state.status_text, state.status_color)

                pygame.display.flip()

            clock.tick(30)

        pygame.quit()
    except Exception as e:
        log.error(f"pygame 线程异常: {e}", exc_info=True)
        state.hwnd = None


def show_status(message, color=(50, 50, 50)):
    """显示状态 - 确保只在主显示器显示"""
    state.status_text = message
    state.status_color = color
    state.window_visible = True
    if state.hwnd:
        # 每次显示时重新定位到主显示器中心
        SM_CXSCREEN = 0
        screen_width = windll.user32.GetSystemMetrics(SM_CXSCREEN)
        x = (screen_width - WINDOW_WIDTH) // 2
        y = 80

        HWND_TOPMOST = -1
        SWP_NOSIZE = 0x0001
        SWP_NOZORDER = 0x0004
        SWP_SHOWWINDOW = 0x0040

        windll.user32.SetWindowPos(
            state.hwnd,
            HWND_TOPMOST,
            x, y, 0, 0,
            SWP_NOSIZE | SWP_NOZORDER | SWP_SHOWWINDOW
        )
        windll.user32.ShowWindow(state.hwnd, 5)  # SW_SHOW


def hide_status():
    """隐藏状态"""
    state.window_visible = False
    state.status_text = ""
    if state.hwnd:
        windll.user32.ShowWindow(state.hwnd, 0)


# ========== 声音反馈 ==========

def play_beep(freq, duration):
    try:
        import winsound
        winsound.Beep(freq, duration)
    except Exception:
        pass


# ========== 录音模块 ==========

def start_recording():
    with _state_lock:
        if state.is_recording or state.processing:
            return

    try:
        import sounddevice as sd

        with _state_lock:
            state.is_recording = True
            state.audio_data = []
            state.record_start_time = time.time()

        def callback(indata, frames, time_info, cb_status):
            if cb_status:
                log.warning(str(cb_status))
            with _state_lock:
                state.audio_data.append(indata.copy())

        state.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype='int16',
            callback=callback
        )
        state.stream.start()

        play_beep(800, 80)
        play_beep(1000, 80)
        show_status("🎤 正在收听...", (80, 80, 80))
        log.info("正在收听...")

        def update_timer():
            while state.is_recording:
                elapsed = time.time() - state.record_start_time
                show_status(f"🎤 收听中 {elapsed:.1f}s", (80, 80, 80))
                time.sleep(0.1)

        threading.Thread(target=update_timer, daemon=True).start()

    except Exception as e:
        log.error(f"录音失败: {e}", exc_info=True)
        state.is_recording = False
        hide_status()


def stop_recording():
    with _state_lock:
        if not state.is_recording:
            return None
        state.is_recording = False

    try:
        if state.stream:
            state.stream.stop()
            state.stream.close()
            state.stream = None

        if not state.audio_data:
            log.warning("无音频数据")
            hide_status()
            return None

        import numpy as np
        import soundfile as sf

        audio = np.concatenate(state.audio_data, axis=0)
        duration = len(audio) / SAMPLE_RATE

        if duration < 0.3:
            log.warning(f"录音太短: {duration:.1f}s")
            play_beep(400, 200)
            show_status("❌ 太短", (200, 50, 50))
            time.sleep(1)
            hide_status()
            return None

        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()
        sf.write(tmp.name, audio, SAMPLE_RATE)

        play_beep(1000, 80)
        play_beep(600, 120)
        show_status("🔄 识别中...", (100, 100, 100))
        log.info(f"录音完成: {duration:.1f}s")

        return tmp.name

    except Exception as e:
        log.error(f"停止录音失败: {e}", exc_info=True)
        hide_status()
        return None


def find_coli():
    """查找 coli 可执行文件路径"""
    # 优先从 PATH 查找
    coli_path = shutil.which("coli")
    if coli_path:
        return coli_path
    # 常见路径 fallback
    npm_coli = Path(os.environ.get("APPDATA", "")) / "npm" / "coli.cmd"
    if npm_coli.exists():
        return str(npm_coli)
    return "coli"


def recognize(audio_path):
    try:
        result = subprocess.run(
            f'"{find_coli()}" asr "{audio_path}"',
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            shell=True
        )

        if result.returncode != 0:
            log.error(f"识别失败: {result.stderr}")
            return ""

        output = result.stdout.strip()
        for line in reversed(output.split("\n")):
            line = line.strip()
            if line and not line.startswith("[") and not line.startswith("Processing"):
                return line
        return output

    except Exception as e:
        log.error(f"识别错误: {e}", exc_info=True)
        return ""


def add_punctuation(text):
    if not text:
        return text
    text = text.strip()
    if text and text[-1] not in "。！？，、；：":
        if any(w in text for w in ["吗", "呢", "什么", "怎么", "为什么"]):
            text += "？"
        else:
            text += "。"
    return text


def type_text(text):
    """通过剪贴板粘贴输入文字"""
    if not text:
        return
    try:
        import win32clipboard
        import win32con

        # 写入剪贴板
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
        win32clipboard.CloseClipboard()

        # 模拟 Ctrl+V 粘贴
        time.sleep(0.15)
        KEYEVENTF_KEYUP = 0x0002
        windll.user32.keybd_event(0x11, 0, 0, 0)  # VK_CONTROL
        windll.user32.keybd_event(0x56, 0, 0, 0)  # VK_V
        windll.user32.keybd_event(0x56, 0, KEYEVENTF_KEYUP, 0)
        windll.user32.keybd_event(0x11, 0, KEYEVENTF_KEYUP, 0)

        log.info(f"已输入: ({len(text)}字)")
        play_beep(1000, 50)
        play_beep(1200, 80)
    except Exception as e:
        log.error(f"输入失败: {e}", exc_info=True)


def process_audio(audio_path):
    """普通模式：识别后打字"""
    with _state_lock:
        if state.processing:
            return
        state.processing = True
    try:
        text = recognize(audio_path)
        if text:
            text = add_punctuation(text)
            display = text[:20] + "..." if len(text) > 20 else text
            show_status(f"✅ {display}", (50, 150, 50))
            play_beep(1000, 50)
            play_beep(1200, 80)
            type_text(text)
            time.sleep(1.5)
            hide_status()
        else:
            show_status("❌ 识别失败", (200, 50, 50))
            play_beep(400, 200)
            time.sleep(1)
            hide_status()
    finally:
        state.processing = False
        try:
            Path(audio_path).unlink(missing_ok=True)
        except Exception:
            pass


# ========== Get笔记 API ==========
# 语音笔记知识库 ID (可在 Get笔记 App 中查看)
VOICE_NOTE_TOPIC_ID = "EJXjKbqY"  # "语音笔记" 知识库

def save_to_getnote(text):
    """保存文字到 Get笔记"""
    if not GETNOTE_API_KEY or not GETNOTE_CLIENT_ID:
        log.warning("Get笔记 API 未配置")
        return False, "API未配置"

    try:
        # 生成标题（取前20字）
        title = text[:20] + "..." if len(text) > 20 else text
        title = title.replace("\n", " ").strip()

        # 提取标签（#开头的词）
        tags = []
        import re
        tag_matches = re.findall(r'#(\S+)', text)
        if tag_matches:
            tags = tag_matches[:5]  # 最多5个标签

        data = {
            "title": title,
            "content": text,
            "note_type": "plain_text",
            "tags": tags
        }

        req = urllib.request.Request(
            f"{GETNOTE_API_URL}/open/api/v1/resource/note/save",
            data=json.dumps(data).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": GETNOTE_API_KEY,
                "X-Client-ID": GETNOTE_CLIENT_ID
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            raw_data = response.read().decode("utf-8")
            result = json.loads(raw_data)

            if result.get("success"):
                log.info(f"已保存到 Get笔记: {title}")

                # 获取 note_id (64位整数，用正则提取避免精度丢失)
                # API 返回的字段可能是 "id" 或 "note_id"
                note_id_match = re.search(r'"(?:note_)?id"\s*:\s*(\d+)', raw_data)
                note_id = int(note_id_match.group(1)) if note_id_match else None

                log.debug(f"note_id: {note_id}")

                # 添加到知识库
                if note_id and VOICE_NOTE_TOPIC_ID:
                    add_note_to_topic(note_id, VOICE_NOTE_TOPIC_ID)

                return True, title
            else:
                error = result.get("error", {})
                log.error(f"Get笔记保存失败: {error.get('message', 'unknown')}")
                return False, error.get("message", "保存失败")

    except Exception as e:
        log.error(f"Get笔记 API 错误: {e}")
        return False, str(e)


def add_note_to_topic(note_id, topic_id):
    """将笔记添加到知识库"""
    try:
        data = {
            "topic_id": topic_id,
            "note_ids": [int(note_id)]
        }

        req = urllib.request.Request(
            f"{GETNOTE_API_URL}/open/api/v1/resource/knowledge/note/batch-add",
            data=json.dumps(data).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": GETNOTE_API_KEY,
                "X-Client-ID": GETNOTE_CLIENT_ID
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
            if result.get("success"):
                log.info("已添加到知识库")
            else:
                log.warning(f"添加到知识库失败: {result.get('error', {}).get('message', '')}")

    except Exception as e:
        log.warning(f"添加到知识库异常: {e}")


def process_audio_for_note(audio_path):
    """笔记模式：识别后保存到 Get笔记"""
    with _state_lock:
        if state.processing:
            return
        state.processing = True
    try:
        text = recognize(audio_path)
        if text:
            text = add_punctuation(text)
            display = text[:15] + "..." if len(text) > 15 else text
            show_status(f"📝 {display}", (100, 100, 200))
            play_beep(800, 80)

            # 保存到 Get笔记
            success, msg = save_to_getnote(text)

            if success:
                show_status(f"✅ 笔记已保存", (50, 150, 50))
                play_beep(1000, 50)
                play_beep(1200, 80)
            else:
                show_status(f"❌ {msg[:10]}", (200, 50, 50))
                play_beep(400, 200)

            time.sleep(1.5)
            hide_status()
        else:
            show_status("❌ 识别失败", (200, 50, 50))
            play_beep(400, 200)
            time.sleep(1)
            hide_status()
    finally:
        state.processing = False
        state.note_mode = False
        try:
            Path(audio_path).unlink(missing_ok=True)
        except Exception:
            pass


# ========== 系统托盘 ==========

def create_tray_icon():
    """加载项目图标作为托盘图标"""
    from PIL import Image
    icon_path = Path(__file__).parent / "assets" / "icon.png"
    if icon_path.exists():
        image = Image.open(icon_path)
        return image.resize((64, 64), Image.LANCZOS)
    # fallback: 红色圆点
    from PIL import ImageDraw
    image = Image.new('RGB', (64, 64), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.ellipse([8, 8, 56, 56], fill=(220, 80, 60))
    return image

def on_tray_quit(icon, item):
    """托盘退出"""
    state.running = False
    icon.stop()

def tray_thread():
    """系统托盘线程"""
    try:
        import pystray
        icon = pystray.Icon(
            "Voice Typer",
            create_tray_icon(),
            "Voice Typer v3.6",
            menu=pystray.Menu(
                pystray.MenuItem("Voice Typer v3.6", None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("退出", on_tray_quit),
            )
        )
        icon.run()
    except Exception as e:
        log.error(f"托盘线程异常: {e}", exc_info=True)


def main():
    log.info("=" * 50)
    log.info("Voice Typer v3.6 (玻璃透明版 + Get笔记 + 系统托盘)")
    log.info("=" * 50)
    log.info("快捷键: Alt+C=打字, Alt+V=笔记, 托盘退出")
    log.info(f"日志文件: {LOG_FILE}")

    # 检查 Get笔记配置
    if GETNOTE_API_KEY:
        log.info("Get笔记 API 已配置")
    else:
        log.warning("Get笔记 API 未配置")

    # 启动系统托盘
    threading.Thread(target=tray_thread, daemon=True).start()
    log.info("系统托盘已启动")

    # 启动 pygame 窗口线程
    threading.Thread(target=pygame_window_thread, daemon=True).start()

    # 等待 pygame 初始化
    time.sleep(0.5)

    log.info("快捷键监听已启动")

    # 主循环
    while state.running:
        try:
            # 检测 Alt + V (笔记模式) - 优先检测
            alt_v = is_alt_v_pressed()
            alt_c = is_alt_c_pressed()

            if alt_v:
                if not state.last_alt_v_state:
                    state.last_alt_v_state = True
                    state.note_mode = True
                    start_recording()
            else:
                if state.last_alt_v_state:
                    state.last_alt_v_state = False
                    audio_path = stop_recording()
                    if audio_path:
                        threading.Thread(target=process_audio_for_note, args=(audio_path,), daemon=True).start()
                # Alt + C (打字模式)
                elif alt_c:
                    if not state.last_key_state:
                        state.last_key_state = True
                        state.note_mode = False
                        start_recording()
                else:
                    if state.last_key_state and not state.note_mode:
                        state.last_key_state = False
                        audio_path = stop_recording()
                        if audio_path:
                            threading.Thread(target=process_audio, args=(audio_path,), daemon=True).start()

            time.sleep(0.02)  # 50Hz 检测频率

        except Exception as e:
            log.error(f"主循环异常: {e}", exc_info=True)
            time.sleep(0.5)

    # 优雅退出：关闭单实例锁
    global _instance_lock
    if _instance_lock:
        _instance_lock.close()
    log.info("Voice Typer 已退出")
    sys.exit(0)


if __name__ == "__main__":
    main()
