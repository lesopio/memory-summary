#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
启动脚本 - 用于运行 Python 后端和 Vite 前端
"""

import subprocess
import sys
import os
import platform
import time

def main():
    # 检查 Python 依赖
    print("🔍 检查 Python 依赖...")
    try:
        import flask
        import flask_cors
        import dotenv
        import requests
        print("✅ Python 依赖已安装")
    except ImportError:
        print("❌ Python 依赖缺失，正在安装...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        print("✅ Python 依赖安装完成")
    
    # 启动后端和前端
    print("\n🚀 启动应用...\n")
    
    # 确定命令
    if platform.system() == 'Windows':
        python_cmd = 'python'
        npm_cmd = 'npm'
    else:
        python_cmd = 'python3'
        npm_cmd = 'npm'
    
    # 启动后端
    print(f"📡 启动 Python Flask 后端...")
    backend_process = subprocess.Popen([python_cmd, 'server.py'])
    
    # 等待后端启动
    time.sleep(2)
    
    # 启动前端
    print(f"🎨 启动 Vite 前端...\n")
    frontend_process = subprocess.Popen([npm_cmd, 'run', 'dev'])
    
    try:
        # 等待进程
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\n\n⏹️  关闭应用...\n")
        backend_process.terminate()
        frontend_process.terminate()
        backend_process.wait(timeout=5)
        frontend_process.wait(timeout=5)
        sys.exit(0)

if __name__ == '__main__':
    main()
