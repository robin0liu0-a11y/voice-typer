#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Voice Typer v3.1 - 简洁版
按住左 Alt 说话，松开自动打字
使用控制台显示状态
"""

import os
import sys
import subprocess
import threading
import time
import tempfile
from pathlib import Path

# 修复 Windows 控制台编码
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 配置
SAMPLE_RATE = 16000
CHANNELS = 1
TEMP_AUDIO = Path(tempfile.gettempdir()) / "voice_typer.wav"

# 状态
class State:
    is_recording = False
    audio_data = []
    stream = None
    last_key_state = False
    record_start_time = None
    running = True
    processing = False  # 防止重复处理

state = State()


def play_beep(freq, duration):
    try:
        import winsound
        winsound.Beep(freq, duration)
    except:
        pass


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
        print("\n[REC] 正在收听... (松开左 Alt 停止)", end="", flush=True)

    except Exception as e:
        print(f"\n[ERR] 录音失败: {e}")
        state.is_recording = False


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
            print("\n[WARN] 无音频数据")
            return None

        import numpy as np
        import soundfile as sf

        audio = np.concatenate(state.audio_data, axis=0)
        duration = len(audio) / SAMPLE_RATE

        if duration < 0.3:
            print(f"\n[WARN] 录音太短: {duration:.1f}s")
            play_beep(400, 200)
            return None

        sf.write(str(TEMP_AUDIO), audio, SAMPLE_RATE)

        play_beep(1000, 80)
        play_beep(600, 120)
        print(f"\n[OK] 录音完成: {duration:.1f}s, 正在识别...")

        return str(TEMP_AUDIO)

    except Exception as e:
        print(f"\n[ERR] 停止录音失败: {e}")
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
            print(f"\n[ERR] 识别失败: {result.stderr}")
            return ""

        output = result.stdout.strip()
        for line in reversed(output.split("\n")):
            line = line.strip()
            if line and not line.startswith("[") and not line.startswith("Processing"):
                return line
        return output

    except Exception as e:
        print(f"\n[ERR] 识别错误: {e}")
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
        time.sleep(0.2)  # 等待按键释放
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
            type_text(text)
        else:
            print("\n[ERR] 识别失败")
            play_beep(400, 200)
    finally:
        state.processing = False


def main():
    print("=" * 50)
    print("Voice Typer v3.1 (简洁版)")
    print("=" * 50)
    print()
    print("快捷键: 按住 左Alt 说话，松开识别")
    print("按 ESC 退出")
    print()

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
