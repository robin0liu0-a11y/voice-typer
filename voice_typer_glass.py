#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Voice Typer v3.7 - LLM纠错 + 波形动画 + 剪贴板恢复
按住 Alt+C 说话，松开自动打字
按住 Alt+V 说话，松开保存到 Get笔记
右键托盘图标退出 / 切换LLM纠错
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
import random
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

# ========== API 配置 ==========
def load_config():
    """加载所有配置"""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key in ("GETNOTE_API_KEY", "GETNOTE_CLIENT_ID",
                       "LLM_API_BASE_URL", "LLM_API_KEY", "LLM_MODEL"):
                os.environ[key] = value

load_config()

GETNOTE_API_KEY = os.environ.get("GETNOTE_API_KEY", "")
GETNOTE_CLIENT_ID = os.environ.get("GETNOTE_CLIENT_ID", "")
GETNOTE_API_URL = "https://openapi.biji.com"

LLM_API_BASE_URL = os.environ.get("LLM_API_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "glm-4-flash")

# 配置
SAMPLE_RATE = 16000
CHANNELS = 1
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 56

# 波形参数
BAR_COUNT = 5
BAR_WIDTH = 6
BAR_GAP = 4
BAR_WEIGHTS = [0.5, 0.8, 1.0, 0.75, 0.55]
BAR_MAX_HEIGHT = 32
BAR_AREA_X = 16
BAR_AREA_Y_CENTER = WINDOW_HEIGHT // 2
RMS_SCALE = 500  # RMS 归一化缩放因子

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
    # 波形
    current_rms = 0.0
    rms_smooth = 0.0
    # LLM
    llm_enabled = False

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
    windll.user32.SetLayeredWindowAttributes(hwnd, 0, 220, LWA_ALPHA)


# ========== Pygame 状态窗口 ==========
def pygame_window_thread():
    """pygame 窗口线程 - 波形动画 + 状态文字"""
    try:
        import pygame
        import pygame.freetype
        import numpy as np

        pygame.init()
        pygame.display.set_caption("Voice Typer")

        # 获取主显示器尺寸
        SM_CXSCREEN = 0
        screen_width = windll.user32.GetSystemMetrics(SM_CXSCREEN)
        x = (screen_width - WINDOW_WIDTH) // 2
        y = 80

        window = pygame.display.set_mode(
            (WINDOW_WIDTH, WINDOW_HEIGHT),
            pygame.NOFRAME
        )

        state.hwnd = pygame.display.get_wm_info()['window']
        state.hwnd_set = True

        HWND_TOPMOST = -1
        SWP_SHOWWINDOW = 0x0040

        windll.user32.SetWindowPos(
            state.hwnd, HWND_TOPMOST,
            x, y, WINDOW_WIDTH, WINDOW_HEIGHT,
            SWP_SHOWWINDOW
        )

        setup_window(state.hwnd)
        windll.user32.ShowWindow(state.hwnd, 0)

        # 字体
        try:
            font = pygame.freetype.SysFont("KaiTi", 16)
        except Exception:
            try:
                font = pygame.freetype.SysFont("楷体", 16)
            except Exception:
                font = pygame.freetype.SysFont("Microsoft YaHei UI", 14)

        clock = pygame.time.Clock()
        bg_color = (255, 255, 255)
        bar_color = (100, 140, 220)  # 蓝色波形条

        while state.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return

            if state.window_visible:
                window.fill(bg_color)

                if state.is_recording:
                    # --- 波形动画 ---
                    with _state_lock:
                        current_rms = state.current_rms

                    target = min(current_rms * RMS_SCALE, 1.0)
                    attack = 0.4
                    release = 0.15
                    if target > state.rms_smooth:
                        state.rms_smooth += (target - state.rms_smooth) * attack
                    else:
                        state.rms_smooth += (target - state.rms_smooth) * release

                    smoothed = state.rms_smooth
                    for i, w in enumerate(BAR_WEIGHTS):
                        jitter = random.uniform(-0.04, 0.04)
                        bar_h = max(3, int(smoothed * w * (1 + jitter) * BAR_MAX_HEIGHT))
                        bar_x = BAR_AREA_X + i * (BAR_WIDTH + BAR_GAP)
                        bar_y = BAR_AREA_Y_CENTER - bar_h // 2
                        pygame.draw.rect(window, bar_color,
                                         (bar_x, bar_y, BAR_WIDTH, bar_h),
                                         border_radius=3)

                    # 右侧文字
                    elapsed = time.time() - state.record_start_time if state.record_start_time else 0
                    text = f"收听中 {elapsed:.1f}s"
                    text_rect = font.get_rect(text)
                    text_x = BAR_AREA_X + BAR_COUNT * (BAR_WIDTH + BAR_GAP) + 12
                    text_y = (WINDOW_HEIGHT - text_rect.height) // 2
                    font.render_to(window, (text_x, text_y), text, (80, 80, 80))
                else:
                    # --- 普通状态文字 ---
                    text = state.status_text
                    if text:
                        text_rect = font.get_rect(text)
                        text_x = (WINDOW_WIDTH - text_rect.width) // 2
                        text_y = (WINDOW_HEIGHT - text_rect.height) // 2
                        font.render_to(window, (text_x, text_y), text, state.status_color)

                pygame.display.flip()

            clock.tick(30)

        pygame.quit()
    except Exception as e:
        log.error(f"pygame 线程异常: {e}", exc_info=True)
        state.hwnd = None


def show_status(message, color=(50, 50, 50)):
    """显示状态"""
    state.status_text = message
    state.status_color = color
    state.window_visible = True
    if state.hwnd:
        SM_CXSCREEN = 0
        screen_width = windll.user32.GetSystemMetrics(SM_CXSCREEN)
        x = (screen_width - WINDOW_WIDTH) // 2

        HWND_TOPMOST = -1
        SWP_NOZORDER = 0x0004
        SWP_SHOWWINDOW = 0x0040

        windll.user32.SetWindowPos(
            state.hwnd, HWND_TOPMOST,
            x, 80, 0, 0,
            0x0001 | SWP_NOZORDER | SWP_SHOWWINDOW
        )
        windll.user32.ShowWindow(state.hwnd, 5)


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
        import numpy as np

        with _state_lock:
            state.is_recording = True
            state.audio_data = []
            state.record_start_time = time.time()
            state.current_rms = 0.0
            state.rms_smooth = 0.0

        def callback(indata, frames, time_info, cb_status):
            if cb_status:
                log.warning(str(cb_status))
            with _state_lock:
                state.audio_data.append(indata.copy())
                rms = float(np.sqrt(np.mean(indata.astype(np.float32) ** 2)))
                state.current_rms = rms

        state.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype='int16',
            callback=callback
        )
        state.stream.start()

        play_beep(800, 80)
        play_beep(1000, 80)
        show_status("正在收听...", (80, 80, 80))
        log.info("正在收听...")

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
            show_status("太短了", (200, 50, 50))
            time.sleep(1)
            hide_status()
            return None

        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()
        sf.write(tmp.name, audio, SAMPLE_RATE)

        play_beep(1000, 80)
        play_beep(600, 120)
        show_status("识别中...", (100, 100, 100))
        log.info(f"录音完成: {duration:.1f}s")

        return tmp.name

    except Exception as e:
        log.error(f"停止录音失败: {e}", exc_info=True)
        hide_status()
        return None


def find_coli():
    """查找 coli 可执行文件路径"""
    coli_path = shutil.which("coli")
    if coli_path:
        return coli_path
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


# ========== LLM 纠错 ==========
LLM_SYSTEM_PROMPT = """你是一个语音识别纠错助手。请非常保守地纠错：
- 只修复明显的语音识别错误（如中文谐音错误、英文技术术语被错转中文如"配森"→"Python"、"杰森"→"JSON"）
- 绝对不要改写、润色或删除任何看起来正确的内容
- 如果输入看起来正确，原样返回
- 只返回纠错后的文本，不要任何解释"""


def refine_with_llm(text):
    """调用 LLM 纠正语音识别错误"""
    if not LLM_API_KEY or not text:
        return text

    try:
        url = f"{LLM_API_BASE_URL.rstrip('/')}/chat/completions"
        data = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": LLM_SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            "temperature": 0.1,
            "max_tokens": len(text) * 2
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {LLM_API_KEY}"
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
            refined = result["choices"][0]["message"]["content"].strip()
            if refined:
                log.info(f"LLM 纠错: '{text}' -> '{refined}'")
                return refined
            return text

    except Exception as e:
        log.warning(f"LLM 纠错失败，使用原文: {e}")
        return text


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


# ========== 剪贴板管理 ==========
def save_clipboard():
    """保存当前剪贴板内容"""
    try:
        import win32clipboard
        import win32con

        win32clipboard.OpenClipboard()
        try:
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                text = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                return text
        finally:
            win32clipboard.CloseClipboard()
    except Exception:
        pass
    return None


def restore_clipboard(text):
    """恢复剪贴板内容"""
    if text is None:
        return
    try:
        import win32clipboard
        import win32con

        time.sleep(0.3)  # 等粘贴完成
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
        finally:
            win32clipboard.CloseClipboard()
    except Exception as e:
        log.warning(f"恢复剪贴板失败: {e}")


# ========== 文字注入 ==========
def type_text(text):
    """通过剪贴板粘贴输入文字（含剪贴板恢复 + IME 处理）"""
    if not text:
        return
    try:
        import win32clipboard
        import win32con

        # 保存原剪贴板
        saved_clip = save_clipboard()

        # 发 Escape 取消可能存在的 IME 组字状态
        KEYEVENTF_KEYUP = 0x0002
        windll.user32.keybd_event(0x1B, 0, 0, 0)  # VK_ESCAPE
        windll.user32.keybd_event(0x1B, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.05)

        # 写入剪贴板
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
        win32clipboard.CloseClipboard()

        # 模拟 Ctrl+V 粘贴
        time.sleep(0.1)
        windll.user32.keybd_event(0x11, 0, 0, 0)  # VK_CONTROL
        windll.user32.keybd_event(0x56, 0, 0, 0)  # VK_V
        windll.user32.keybd_event(0x56, 0, KEYEVENTF_KEYUP, 0)
        windll.user32.keybd_event(0x11, 0, KEYEVENTF_KEYUP, 0)

        log.info(f"已输入: ({len(text)}字)")
        play_beep(1000, 50)
        play_beep(1200, 80)

        # 恢复原剪贴板
        restore_clipboard(saved_clip)

    except Exception as e:
        log.error(f"输入失败: {e}", exc_info=True)


def process_audio(audio_path):
    """普通模式：识别 → LLM纠错 → 打字"""
    with _state_lock:
        if state.processing:
            return
        state.processing = True
    try:
        text = recognize(audio_path)
        if text:
            # LLM 纠错
            if state.llm_enabled and LLM_API_KEY:
                show_status("AI 纠错中...", (100, 100, 200))
                text = refine_with_llm(text)

            text = add_punctuation(text)
            display = text[:20] + "..." if len(text) > 20 else text
            show_status(f"OK {display}", (50, 150, 50))
            play_beep(1000, 50)
            play_beep(1200, 80)
            type_text(text)
            time.sleep(1.5)
            hide_status()
        else:
            show_status("识别失败", (200, 50, 50))
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
VOICE_NOTE_TOPIC_ID = "EJXjKbqY"

def save_to_getnote(text):
    """保存文字到 Get笔记"""
    if not GETNOTE_API_KEY or not GETNOTE_CLIENT_ID:
        log.warning("Get笔记 API 未配置")
        return False, "API未配置"

    try:
        title = text[:20] + "..." if len(text) > 20 else text
        title = title.replace("\n", " ").strip()

        import re
        tags = re.findall(r'#(\S+)', text)[:5]

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
                import re
                note_id_match = re.search(r'"(?:note_)?id"\s*:\s*(\d+)', raw_data)
                note_id = int(note_id_match.group(1)) if note_id_match else None
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
    except Exception as e:
        log.warning(f"添加到知识库异常: {e}")


def process_audio_for_note(audio_path):
    """笔记模式：识别 → LLM纠错 → 保存到 Get笔记"""
    with _state_lock:
        if state.processing:
            return
        state.processing = True
    try:
        text = recognize(audio_path)
        if text:
            # LLM 纠错
            if state.llm_enabled and LLM_API_KEY:
                show_status("AI 纠错中...", (100, 100, 200))
                text = refine_with_llm(text)

            text = add_punctuation(text)
            display = text[:15] + "..." if len(text) > 15 else text
            show_status(f"Note {display}", (100, 100, 200))
            play_beep(800, 80)

            success, msg = save_to_getnote(text)
            if success:
                show_status("笔记已保存", (50, 150, 50))
                play_beep(1000, 50)
                play_beep(1200, 80)
            else:
                show_status(f"失败 {msg[:10]}", (200, 50, 50))
                play_beep(400, 200)

            time.sleep(1.5)
            hide_status()
        else:
            show_status("识别失败", (200, 50, 50))
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
    from PIL import ImageDraw
    image = Image.new('RGB', (64, 64), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.ellipse([8, 8, 56, 56], fill=(220, 80, 60))
    return image


def on_tray_quit(icon, item):
    state.running = False
    icon.stop()


def on_toggle_llm(icon, item):
    state.llm_enabled = not state.llm_enabled
    icon.notify(f"LLM 纠错已{'开启' if state.llm_enabled else '关闭'}")


def tray_thread():
    """系统托盘线程"""
    try:
        import pystray

        llm_status = "已配置" if LLM_API_KEY else "未配置API Key"
        icon = pystray.Icon(
            "Voice Typer",
            create_tray_icon(),
            "Voice Typer v3.7",
            menu=pystray.Menu(
                pystray.MenuItem("Voice Typer v3.7", None, enabled=False),
                pystray.MenuItem(f"LLM纠错 ({llm_status})", None, enabled=False),
                pystray.MenuItem(
                    "启用 LLM 纠错",
                    on_toggle_llm,
                    checked=lambda item: state.llm_enabled
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("退出", on_tray_quit),
            )
        )
        icon.run()
    except Exception as e:
        log.error(f"托盘线程异常: {e}", exc_info=True)


def main():
    log.info("=" * 50)
    log.info("Voice Typer v3.7 (LLM纠错 + 波形动画 + 剪贴板恢复)")
    log.info("=" * 50)
    log.info("快捷键: Alt+C=打字, Alt+V=笔记, 托盘退出")
    log.info(f"日志文件: {LOG_FILE}")

    if GETNOTE_API_KEY:
        log.info("Get笔记 API 已配置")
    else:
        log.warning("Get笔记 API 未配置")

    if LLM_API_KEY:
        log.info(f"LLM 纠错已配置: {LLM_API_BASE_URL} / {LLM_MODEL}")
    else:
        log.warning("LLM API Key 未配置，纠错功能不可用")

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

            time.sleep(0.02)

        except Exception as e:
            log.error(f"主循环异常: {e}", exc_info=True)
            time.sleep(0.5)

    # 优雅退出
    global _instance_lock
    if _instance_lock:
        _instance_lock.close()
    log.info("Voice Typer 已退出")
    sys.exit(0)


if __name__ == "__main__":
    main()
