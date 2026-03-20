#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Voice Typer v3.2 - 玻璃透明版
按住左 Alt 说话，松开自动打字
玻璃半透明窗口 + 圆角 + 黑色文字
"""

import os
import sys
import subprocess
import threading
import time
import ctypes
import tempfile
from pathlib import Path
from ctypes import windll, c_int, byref, sizeof, c_ulong

# 修复 Windows 控制台编码
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 配置
SAMPLE_RATE = 16000
CHANNELS = 1
TEMP_AUDIO = Path(tempfile.gettempdir()) / "voice_typer.wav"
WINDOW_WIDTH = 300
WINDOW_HEIGHT = 50

# 状态
class State:
    is_recording = False
    audio_data = []
    stream = None
    last_key_state = False
    record_start_time = None
    running = True
    status_text = ""
    status_color = (50, 50, 50)  # 深灰色文字
    window_visible = False
    hwnd = None
    processing = False

state = State()


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
    """pygame 窗口线程"""
    import pygame
    import pygame.freetype

    pygame.init()
    pygame.display.set_caption("Voice Typer")

    # 获取屏幕尺寸
    info = pygame.display.Info()
    screen_width = info.current_w
    x = (screen_width - WINDOW_WIDTH) // 2
    y = 80

    # 创建窗口
    window = pygame.display.set_mode(
        (WINDOW_WIDTH, WINDOW_HEIGHT),
        pygame.NOFRAME
    )

    # 获取窗口句柄并设置样式
    state.hwnd = pygame.display.get_wm_info()['window']

    # 设置窗口位置和置顶
    HWND_TOPMOST = -1
    SWP_NOSIZE = 0x0001
    SWP_NOMOVE = 0x0002
    SWP_SHOWWINDOW = 0x0040

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
    except:
        try:
            font = pygame.freetype.SysFont("楷体", 18)
        except:
            font = pygame.freetype.SysFont("Microsoft YaHei UI", 16)

    clock = pygame.time.Clock()
    bg_color = (255, 255, 255, 200)  # 白色半透明背景

    while state.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                state.running = False
                return

        if state.window_visible and state.status_text:
            # 绘制
            window.fill(bg_color[:3])  # pygame 不支持 alpha 填充

            # 绘制文字 (黑色)
            text_rect = font.get_rect(state.status_text)
            text_x = (WINDOW_WIDTH - text_rect.width) // 2
            text_y = (WINDOW_HEIGHT - text_rect.height) // 2
            font.render_to(window, (text_x, text_y), state.status_text, state.status_color)

            pygame.display.flip()

        clock.tick(30)

    pygame.quit()


def show_status(message, color=(50, 50, 50)):
    """显示状态"""
    state.status_text = message
    state.status_color = color
    state.window_visible = True
    if state.hwnd:
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
    except:
        pass


# ========== 录音模块 ==========

def start_recording():
    if state.is_recording or state.processing:
        return

    try:
        import sounddevice as sd

        state.is_recording = True
        state.audio_data = []
        state.record_start_time = time.time()

        def callback(indata, frames, time_info, status):
            if status:
                print(f"[WARN] {status}")
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
        print("\n[REC] 正在收听...")

        def update_timer():
            while state.is_recording:
                elapsed = time.time() - state.record_start_time
                show_status(f"🎤 收听中 {elapsed:.1f}s", (80, 80, 80))
                time.sleep(0.1)

        threading.Thread(target=update_timer, daemon=True).start()

    except Exception as e:
        print(f"[ERR] 录音失败: {e}")
        state.is_recording = False
        hide_status()


def stop_recording():
    if not state.is_recording:
        return None

    state.is_recording = False

    try:
        if state.stream:
            state.stream.stop()
            state.stream.close()
            state.stream = None

        if not state.audio_data:
            print("[WARN] 无音频数据")
            hide_status()
            return None

        import numpy as np
        import soundfile as sf

        audio = np.concatenate(state.audio_data, axis=0)
        duration = len(audio) / SAMPLE_RATE

        if duration < 0.3:
            print(f"[WARN] 录音太短: {duration:.1f}s")
            play_beep(400, 200)
            show_status("❌ 太短", (200, 50, 50))
            time.sleep(1)
            hide_status()
            return None

        sf.write(str(TEMP_AUDIO), audio, SAMPLE_RATE)

        play_beep(1000, 80)
        play_beep(600, 120)
        show_status("🔄 识别中...", (100, 100, 100))
        print(f"[OK] 录音完成: {duration:.1f}s")

        return str(TEMP_AUDIO)

    except Exception as e:
        print(f"[ERR] 停止录音失败: {e}")
        hide_status()
        return None


def recognize(audio_path):
    try:
        result = subprocess.run(
            f'coli asr "{audio_path}"',
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
            encoding="utf-8"
        )

        if result.returncode != 0:
            print(f"[ERR] 识别失败: {result.stderr}")
            return ""

        output = result.stdout.strip()
        for line in reversed(output.split("\n")):
            line = line.strip()
            if line and not line.startswith("[") and not line.startswith("Processing"):
                return line
        return output

    except Exception as e:
        print(f"[ERR] 识别错误: {e}")
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
    if not text:
        return
    try:
        import keyboard
        time.sleep(0.2)
        keyboard.write(text, delay=0.02)
        print(f"[OK] 已输入: {text}")
        play_beep(1000, 50)
        play_beep(1200, 80)
    except Exception as e:
        print(f"[ERR] 输入失败: {e}")


def process_audio(audio_path):
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


def main():
    print("=" * 50)
    print("Voice Typer v3.2 (玻璃透明版)")
    print("=" * 50)
    print()
    print("快捷键: 按住 左Alt 说话，松开识别")
    print("按 ESC 退出")
    print()

    # 启动 pygame 窗口线程
    pygame_thread = threading.Thread(target=pygame_window_thread, daemon=True)
    pygame_thread.start()

    # 等待 pygame 初始化
    time.sleep(0.5)

    print("[OK] 玻璃窗口已启动")
    print("[OK] 快捷键监听已启动 (左Alt)")

    import keyboard

    while state.running:
        try:
            current_state = keyboard.is_pressed('left alt')

            if current_state and not state.last_key_state:
                start_recording()
            elif not current_state and state.last_key_state:
                audio_path = stop_recording()
                if audio_path:
                    threading.Thread(target=process_audio, args=(audio_path,), daemon=True).start()

            state.last_key_state = current_state

            if keyboard.is_pressed('esc'):
                print("\n[EXIT] 退出...")
                state.running = False
                os._exit(0)

            time.sleep(0.02)

        except Exception as e:
            print(f"[ERR] {e}")
            time.sleep(0.1)


if __name__ == "__main__":
    main()
