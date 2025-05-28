#!/usr/bin/env python
# encoding: utf-8

import os
import time
import sys
import re
from chat_ui import Color

# 语音识别ASCII艺术 - 现代简约风格
SPEECH_ASCII = """
    ┌─────┐
    │  ≡  │
    │ ≡≡≡ │
    │  ≡  │
    └─────┘
"""

def print_speech_welcome():
    """打印语音识别功能欢迎信息"""
    print(f"\n{Color.BG_GRAY}{Color.WHITE}{Color.BOLD}")
    print("┌" + "─" * 58 + "┐")
    print("│" + " " * 58 + "│")
    print("│" + "            蓝心AI语音识别助手            ".center(58) + "│")
    print("│" + " " * 58 + "│")
    print("└" + "─" * 58 + "┘")
    print(f"{Color.RESET}")
    print(f"{Color.GRAY}● 输入 'back' 返回聊天模式{Color.RESET}\n")
    print(f"{Color.BRIGHT_BLUE}支持命令: {Color.RESET}")
    print(f"  {Color.BRIGHT_CYAN}○ /record [持续时间] {Color.RESET}- 录音并识别")
    print(f"  {Color.BRIGHT_CYAN}○ /recognize <文件路径> {Color.RESET}- 识别音频文件")
    print(f"  {Color.BRIGHT_CYAN}○ /save <文件名> [持续时间] {Color.RESET}- 录音并保存")
    print(f"  {Color.BRIGHT_CYAN}○ /files {Color.RESET}- 列出音频文件目录\n")

def print_speech_header():
    """打印语音识别模式标题"""
    print(f"\n{Color.BRIGHT_CYAN}{Color.BOLD}┌─{' 语音识别模式 ':─^50}─┐{Color.RESET}")
    print(f"{Color.BRIGHT_CYAN}└{'─'*58}┘{Color.RESET}\n")

def print_speech_prompt():
    """打印语音识别提示符"""
    print(f"{Color.BRIGHT_BLUE}{Color.BOLD}语音>>> {Color.RESET}", end="", flush=True)
    return input()

def print_recording_animation(seconds):
    """打印录音过程的动画，持续指定的秒数"""
    frames = [
        "⚪⚪⚪⚪⚪",
        "⚫⚪⚪⚪⚪",
        "⚫⚫⚪⚪⚪",
        "⚫⚫⚫⚪⚪",
        "⚫⚫⚫⚫⚪",
        "⚫⚫⚫⚫⚫",
    ]
    
    start_time = time.time()
    frame_index = 0
    
    print(f"\n{Color.BRIGHT_BLUE}{Color.BOLD}┌─{' 开始录音 ':─^52}─┐{Color.RESET}")
    print(f"{Color.BRIGHT_BLUE}└{'─'*58}┘{Color.RESET}\n")
    
    while time.time() - start_time < seconds:
        sys.stdout.write(f"\r{Color.BRIGHT_BLUE}{Color.BOLD}录音中 {frames[frame_index]}{Color.RESET}")
        sys.stdout.flush()
        frame_index = (frame_index + 1) % len(frames)
        time.sleep(0.2)
    
    sys.stdout.write("\r" + " " * 50 + "\r")
    sys.stdout.flush()
    print(f"\n{Color.BRIGHT_BLUE}{Color.BOLD}┌─{' 录音结束，正在处理 ':─^46}─┐{Color.RESET}")
    print(f"{Color.BRIGHT_BLUE}└{'─'*58}┘{Color.RESET}\n")

def print_recognizing_animation():
    """打印识别过程的动画"""
    frames = [
        "⚪⚪⚪⚪⚪",
        "⚫⚪⚪⚪⚪",
        "⚫⚫⚪⚪⚪",
        "⚫⚫⚫⚪⚪",
        "⚫⚫⚫⚫⚪",
        "⚫⚫⚫⚫⚫",
    ]
    
    for i in range(10):  # 播放10帧动画
        sys.stdout.write(f"\r{Color.BRIGHT_BLUE}{Color.BOLD}识别中 {frames[i % len(frames)]}{Color.RESET}")
        sys.stdout.flush()
        time.sleep(0.2)
    
    sys.stdout.write("\r" + " " * 50 + "\r")
    sys.stdout.flush()

def print_speech_result(result_text):
    """打印语音识别结果"""
    if not result_text:
        print(f"\n{Color.BRIGHT_BLUE}{Color.BOLD}┌─{' 识别结果 ':─^52}─┐{Color.RESET}")
        print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {Color.RED}未能识别出文本内容{Color.RESET}")
        print(f"{Color.BRIGHT_BLUE}└{'─'*58}┘{Color.RESET}\n")
        return
    
    print(f"\n{Color.BRIGHT_BLUE}{Color.BOLD}┌─{' 识别结果 ':─^52}─┐{Color.RESET}")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {result_text}")
    print(f"{Color.BRIGHT_BLUE}└{'─'*58}┘{Color.RESET}\n")

def print_audio_files(directory="./audio"):
    """列出音频文件目录"""
    # 确保目录存在
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            print(f"{Color.BRIGHT_BLUE}{Color.BOLD}┌─{' 已创建音频目录 ':─^48}─┐{Color.RESET}")
            print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {directory}")
            print(f"{Color.BRIGHT_BLUE}└{'─'*58}┘{Color.RESET}\n")
        except Exception as e:
            print(f"{Color.RED}创建目录失败: {str(e)}{Color.RESET}")
            return
    
    # 支持的音频格式
    audio_extensions = ['.wav']
    
    print(f"\n{Color.BRIGHT_BLUE}{Color.BOLD}┌─{' 音频文件目录 ':─^50}─┐{Color.RESET}")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET} 目录: {os.path.abspath(directory)}")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {Color.GRAY}{'─'*56}{Color.RESET}")
    
    # 查找音频文件
    audio_files = []
    for file in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, file)) and any(file.lower().endswith(ext) for ext in audio_extensions):
            audio_files.append((file, os.path.getsize(os.path.join(directory, file))))
    
    if not audio_files:
        print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {Color.GRAY}未找到音频文件{Color.RESET}")
        print(f"{Color.BRIGHT_BLUE}└{'─'*58}┘{Color.RESET}\n")
        return
    
    # 按文件名排序
    audio_files.sort(key=lambda x: x[0])
    
    # 打印文件列表
    for i, (file, size) in enumerate(audio_files, 1):
        size_str = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f} MB"
        print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {i}. {file} ({size_str})")
    
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET}")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {Color.GRAY}要识别文件，请输入: /recognize {directory}/文件名{Color.RESET}")
    print(f"{Color.BRIGHT_BLUE}└{'─'*58}┘{Color.RESET}\n")

def print_save_result(success, output_file):
    """打印保存录音结果"""
    if success:
        print(f"\n{Color.BRIGHT_BLUE}{Color.BOLD}┌─{' 录音已保存 ':─^52}─┐{Color.RESET}")
        print(f"{Color.BRIGHT_BLUE}│{Color.RESET} 文件路径: {output_file}")
        print(f"{Color.BRIGHT_BLUE}└{'─'*58}┘{Color.RESET}\n")
    else:
        print(f"\n{Color.BRIGHT_BLUE}{Color.BOLD}┌─{' 录音保存失败 ':─^50}─┐{Color.RESET}")
        print(f"{Color.BRIGHT_BLUE}└{'─'*58}┘{Color.RESET}\n")

def print_help_speech():
    """打印语音识别帮助信息"""
    print(f"\n{Color.BRIGHT_BLUE}{Color.BOLD}┌─{' 语音识别命令帮助 ':─^48}─┐{Color.RESET}")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {Color.BRIGHT_CYAN}/record [持续时间] {Color.RESET}- 录音并识别")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET}   例如: /record 5")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET}   持续时间默认为5秒，可以指定1-60秒之间的值")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET}")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {Color.BRIGHT_CYAN}/recognize <文件路径> {Color.RESET}- 识别音频文件")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET}   例如: /recognize audio/test.wav")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET}   仅支持16k/16bit单声道PCM格式的WAV文件")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET}")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {Color.BRIGHT_CYAN}/save <文件名> [持续时间] {Color.RESET}- 录音并保存")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET}   例如: /save test.wav 10")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET}   文件将保存在audio目录下，持续时间默认为5秒")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET}")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {Color.BRIGHT_CYAN}/files {Color.RESET}- 列出音频文件目录")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {Color.BRIGHT_CYAN}/back {Color.RESET}- 返回聊天模式")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {Color.BRIGHT_CYAN}/help {Color.RESET}- 显示此帮助信息")
    print(f"{Color.BRIGHT_BLUE}└{'─'*58}┘{Color.RESET}\n")

def parse_record_command(command):
    """解析录音命令
    
    Args:
        command: 命令字符串
        
    Returns:
        录音持续时间（秒），默认为5秒
    """
    # 基本命令格式: /record [持续时间]
    pattern = r'^/record(?:\s+(\d+))?$'
    match = re.match(pattern, command)
    
    if not match:
        return None
    
    # 提取持续时间参数，默认为5秒
    duration_str = match.group(1)
    if duration_str:
        duration = int(duration_str)
        # 限制在1-60秒范围内
        duration = max(1, min(duration, 60))
    else:
        duration = 5
    
    return duration

def parse_recognize_command(command):
    """解析识别文件命令
    
    Args:
        command: 命令字符串
        
    Returns:
        文件路径，解析失败返回None
    """
    # 基本命令格式: /recognize <文件路径>
    pattern = r'^/recognize\s+(.+)$'
    match = re.match(pattern, command)
    
    if not match:
        return None
    
    file_path = match.group(1).strip()
    return file_path

def parse_save_command(command):
    """解析保存录音命令
    
    Args:
        command: 命令字符串
        
    Returns:
        (文件名, 持续时间) 元组，解析失败返回 (None, None)
    """
    # 基本命令格式: /save <文件名> [持续时间]
    pattern = r'^/save\s+([^\s]+)(?:\s+(\d+))?$'
    match = re.match(pattern, command)
    
    if not match:
        return None, None
    
    filename = match.group(1)
    
    # 提取持续时间参数，默认为5秒
    duration_str = match.group(2)
    if duration_str:
        duration = int(duration_str)
        # 限制在1-60秒范围内
        duration = max(1, min(duration, 60))
    else:
        duration = 5
    
    return filename, duration

def ensure_audio_dir(directory="./audio"):
    """确保音频目录存在
    
    Args:
        directory: 目录路径
        
    Returns:
        目录是否存在或成功创建
    """
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            return True
        except Exception as e:
            print(f"{Color.RED}创建目录失败: {str(e)}{Color.RESET}")
            return False
    return True

# 测试功能
if __name__ == "__main__":
    print_speech_welcome()
    print_speech_header()
    print_help_speech()