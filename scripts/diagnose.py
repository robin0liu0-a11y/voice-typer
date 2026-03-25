#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Voice Typer 诊断工具
检查启动问题
"""

import sys
import os
import subprocess
import socket

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 50)
print("Voice Typer Diagnostic Tool v1.0")
print("=" * 50)
print()

# 1. 检查 Python 版本
print("[1] Python 版本检查:")
print(f"    Python {sys.version}")
print()

# 2. 检查依赖库
print("[2] 依赖库检查:")
deps = [
    ('pygame', 'pygame'),
    ('pynput', 'pynput'),
    ('requests', 'requests'),
]

all_ok = True
for module, name in deps:
    try:
        __import__(module)
        print(f"    [OK] {name}")
    except ImportError as e:
        print(f"    [ERR] {name} - Missing: {e}")
        all_ok = False
print()

# 3. 检查 coli ASR
print("[3] Coli ASR 检查:")
try:
    result = subprocess.run(['coli', '--help'], 
                          capture_output=True, text=True, timeout=5)
    if result.returncode == 0 or 'Usage' in result.stdout:
        print("    [OK] coli installed")
    else:
        print(f"    [ERR] coli error: {result.stderr}")
        all_ok = False
except FileNotFoundError:
    print("    [ERR] coli not found. Run: npm install -g coli")
    all_ok = False
except Exception as e:
    print(f"    [ERR] coli check failed: {e}")
    all_ok = False
print()

# 4. 检查单实例锁
print("[4] 单实例锁检查 (端口 51234):")
try:
    test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    test_socket.bind(('127.0.0.1', 51234))
    test_socket.close()
    print("    [OK] Port 51234 available")
except:
    print("    [WARN] Port 51234 in use")
print()

# 5. 检查 .env 文件
print("[5] 配置文件检查:")
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    print(f"    ✓ .env 文件存在")
    with open(env_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if 'GETNOTE' in line and '=' in line:
                key = line.split('=')[0]
                print(f"    [OK] {key} configured")
else:
    print(f"    [ERR] .env file missing")
print()

# 6. 检查工作目录
print("[6] 工作目录检查:")
print(f"    当前目录: {os.getcwd()}")
script_dir = os.path.dirname(os.path.abspath(__file__))
print(f"    脚本目录: {script_dir}")
print()

# 总结
print("=" * 50)
if all_ok:
    print("Result: All checks passed!")
    print()
    print("Try: python voice_typer_glass.py")
else:
    print("Result: Issues found, please fix first")
print("=" * 50)

input("\nPress Enter to exit...")
