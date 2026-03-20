#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Voice Typer 安装脚本
检查并安装所有依赖
"""

import subprocess
import sys
import os

def run_cmd(cmd, description):
    """运行命令并显示结果"""
    print(f"\n{'='*50}")
    print(f"📦 {description}")
    print(f"   命令: {cmd}")
    print('='*50)

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ 成功")
        if result.stdout.strip():
            print(result.stdout[:500])
    else:
        print(f"❌ 失败")
        if result.stderr.strip():
            print(result.stderr[:500])

    return result.returncode == 0

def main():
    print("=" * 50)
    print("🎤 Voice Typer 安装程序")
    print("=" * 50)

    # 1. 检查 Python 版本
    print(f"\n🐍 Python 版本: {sys.version}")

    if sys.version_info < (3, 8):
        print("❌ 需要 Python 3.8+")
        return False

    # 2. 安装 Python 依赖
    python_deps = [
        "sounddevice",
        "soundfile",
        "numpy",
        "keyboard",
        "pygame"
    ]

    print(f"\n📦 安装 Python 依赖: {', '.join(python_deps)}")
    success = run_cmd(
        f'pip install {" ".join(python_deps)}',
        "Python 依赖"
    )

    if not success:
        print("⚠️  部分 Python 依赖安装失败，尝试继续...")

    # 3. 检查 Node.js
    print("\n📦 检查 Node.js...")
    node_result = subprocess.run("node --version", shell=True, capture_output=True, text=True)

    if node_result.returncode != 0:
        print("❌ Node.js 未安装")
        print("   请先安装 Node.js: https://nodejs.org/")
        return False

    print(f"✅ Node.js 版本: {node_result.stdout.strip()}")

    # 4. 安装 coli
    print("\n📦 安装语音识别引擎 (coli)...")
    coli_success = run_cmd("npm install -g @marswave/coli", "coli 语音识别")

    if not coli_success:
        print("⚠️  coli 安装失败，请手动安装:")
        print("   npm install -g @marswave/coli")

    # 5. 验证安装
    print("\n" + "=" * 50)
    print("🔍 验证安装")
    print("=" * 50)

    # 检查 Python 模块
    modules_ok = True
    for mod in ["sounddevice", "soundfile", "numpy", "keyboard", "pygame"]:
        try:
            __import__(mod)
            print(f"  ✅ {mod}")
        except ImportError:
            print(f"  ❌ {mod}")
            modules_ok = False

    # 检查 coli
    coli_check = subprocess.run("coli --help", shell=True, capture_output=True)
    if coli_check.returncode == 0:
        print("  ✅ coli")
    else:
        print("  ❌ coli")
        modules_ok = False

    print("\n" + "=" * 50)
    if modules_ok:
        print("✅ 安装完成！")
        print("\n使用方法:")
        print("  python scripts/voice_typer.py")
        print("  或")
        print("  /voice-typer")
    else:
        print("⚠️  部分组件安装失败，请检查上面的错误信息")

    print("=" * 50)

    return modules_ok

if __name__ == "__main__":
    main()
