#!/usr/bin/env python
# encoding: utf-8

import os
import time
import sys
import re
from chat_ui import Color

# 图片分析ASCII艺术 - 现代简约风格
VISION_ASCII = """
    ┌─────┐
    │ ◈◈◈ │
    │ ─┼─ │
    │ ◈◈◈ │
    └─────┘
"""

def print_vision_welcome():
    """打印图片分析功能欢迎信息"""
    print(f"\n{Color.BG_GRAY}{Color.WHITE}{Color.BOLD}")
    print("┌" + "─" * 58 + "┐")
    print("│" + " " * 58 + "│")
    print("│" + "            蓝心AI图片分析助手            ".center(58) + "│")
    print("│" + " " * 58 + "│")
    print("└" + "─" * 58 + "┘")
    print(f"{Color.RESET}")
    print(f"{Color.GRAY}● 输入 'back' 返回聊天模式{Color.RESET}\n")
    print(f"{Color.BRIGHT_BLUE}支持命令: {Color.RESET}")
    print(f"  {Color.BRIGHT_CYAN}○ /analyze <图片路径> [提示词] {Color.RESET}- 分析图片")
    print(f"  {Color.BRIGHT_CYAN}○ /browse {Color.RESET}- 浏览图片目录")
    print(f"  {Color.BRIGHT_CYAN}○ /models {Color.RESET}- 显示可用模型")
    print(f"  {Color.BRIGHT_CYAN}○ /set model <模型名称> {Color.RESET}- 设置使用的模型")
    print(f"  {Color.BRIGHT_CYAN}○ /examples {Color.RESET}- 显示分析提示词示例\n")

def print_vision_header():
    """打印图片分析模式标题"""
    print(f"\n{Color.BRIGHT_CYAN}{Color.BOLD}┌─{' 图片分析模式 ':─^50}─┐{Color.RESET}")
    print(f"{Color.BRIGHT_CYAN}└{'─'*58}┘{Color.RESET}\n")

def print_vision_prompt():
    """打印图片分析提示符"""
    print(f"{Color.BRIGHT_BLUE}{Color.BOLD}分析>>> {Color.RESET}", end="", flush=True)
    return input()

def print_models():
    """打印可用的图片分析模型"""
    print(f"\n{Color.BRIGHT_BLUE}{Color.BOLD}┌─{' 可用的图片分析模型 ':─^48}─┐{Color.RESET}")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {Color.GRAY}{'模型名称':<20} | {'说明'}{Color.RESET}")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {Color.GRAY}{'─'*56}{Color.RESET}")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET} BlueLM-Vision-prd    | 图片理解、文本创作、文本提取，上下文4096")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET} vivo-BlueLM-V-2.0    | 文本提取，输入+输出 2048token")
    print(f"{Color.BRIGHT_BLUE}└{'─'*58}┘{Color.RESET}\n")

def print_examples():
    """打印图片分析提示词示例"""
    print(f"\n{Color.BRIGHT_BLUE}{Color.BOLD}┌─{' 图片分析提示词示例 ':─^48}─┐{Color.RESET}")
    
    examples = [
        ("描述图片的内容", "获取图片的基本描述"),
        ("这张图片里有什么？", "简单识别图片内容"),
        ("详细描述这张图片中的人物、场景和活动", "获取图片的详细描述"),
        ("这张照片是在什么地方拍摄的？", "分析图片可能的拍摄地点"),
        ("图片中的文字是什么？", "识别图片中的文字"),
        ("这张图片的主题是什么？", "分析图片的主题或意图"),
        ("描述图片中人物的表情和情绪", "情感分析"),
        ("这是什么品种的狗/猫？", "识别宠物品种"),
        ("这张图片中的建筑是什么风格？", "建筑风格分析"),
        ("图片中有哪些植物？", "植物识别")
    ]
    
    for i, (prompt, desc) in enumerate(examples, 1):
        print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {i}. {prompt}")
        print(f"{Color.BRIGHT_BLUE}│{Color.RESET}    {Color.GRAY}{desc}{Color.RESET}")
    
    print(f"{Color.BRIGHT_BLUE}└{'─'*58}┘{Color.RESET}\n")

def print_browse_images(directory="./"):
    """浏览指定目录中的图片"""
    supported_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".gif"]
    
    print(f"\n{Color.BRIGHT_BLUE}{Color.BOLD}┌─{' 图片目录浏览 ':─^50}─┐{Color.RESET}")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET} 当前目录: {os.path.abspath(directory)}")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {Color.GRAY}{'─'*56}{Color.RESET}")
    
    image_files = []
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path) and os.path.splitext(file)[1].lower() in supported_extensions:
            image_files.append((file, os.path.getsize(file_path)))
    
    if not image_files:
        print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {Color.RED}未找到图片文件!{Color.RESET}")
        print(f"{Color.BRIGHT_BLUE}└{'─'*58}┘{Color.RESET}\n")
        return
    
    # 按文件名排序
    image_files.sort(key=lambda x: x[0])
    
    # 打印图片列表
    for i, (file, size) in enumerate(image_files, 1):
        size_str = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f} MB"
        print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {i}. {file} ({size_str})")
    
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET}")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {Color.GRAY}要分析图片，请输入: /analyze <文件名> [提示词]{Color.RESET}")
    print(f"{Color.BRIGHT_BLUE}└{'─'*58}┘{Color.RESET}\n")

def print_analyzing_animation(seconds=3):
    """打印分析过程的动画，持续指定的秒数"""
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
    
    while time.time() - start_time < seconds:
        sys.stdout.write(f"\r{Color.BRIGHT_BLUE}{Color.BOLD}图片分析中 {frames[frame_index]}{Color.RESET}")
        sys.stdout.flush()
        frame_index = (frame_index + 1) % len(frames)
        time.sleep(0.2)
    
    sys.stdout.write("\r" + " " * 50 + "\r")
    sys.stdout.flush()

def print_image_info(image_path):
    """打印图片信息"""
    try:
        if not os.path.exists(image_path):
            print(f"{Color.RED}图片文件不存在: {image_path}{Color.RESET}")
            return False
        
        size = os.path.getsize(image_path)
        size_str = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f} MB"
        
        print(f"\n{Color.BRIGHT_BLUE}{Color.BOLD}┌─{' 图片信息 ':─^52}─┐{Color.RESET}")
        print(f"{Color.BRIGHT_BLUE}│{Color.RESET} 路径: {os.path.abspath(image_path)}")
        print(f"{Color.BRIGHT_BLUE}│{Color.RESET} 大小: {size_str}")
        print(f"{Color.BRIGHT_BLUE}└{'─'*58}┘{Color.RESET}\n")
        return True
    except Exception as e:
        print(f"{Color.RED}读取图片信息失败: {str(e)}{Color.RESET}")
        return False

def print_analysis_result(result):
    """打印图片分析结果"""
    print(f"\n{Color.BRIGHT_BLUE}{Color.BOLD}┌─{' 分析结果 ':─^52}─┐{Color.RESET}")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {result}")
    print(f"{Color.BRIGHT_BLUE}└{'─'*58}┘{Color.RESET}\n")

def print_streaming_analysis_result(chunk_generator):
    """打印流式分析结果"""
    print(f"\n{Color.BRIGHT_BLUE}{Color.BOLD}┌─{' 分析结果 ':─^52}─┐{Color.RESET}")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET} ", end="", flush=True)
    
    full_response = ""
    for chunk in chunk_generator:
        print(chunk, end="", flush=True)
        full_response += chunk
    
    print(f"\n{Color.BRIGHT_BLUE}└{'─'*58}┘{Color.RESET}\n")
    return full_response

def print_help_vision():
    """打印图片分析帮助信息"""
    print(f"\n{Color.BRIGHT_BLUE}{Color.BOLD}┌─{' 图片分析命令帮助 ':─^48}─┐{Color.RESET}")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {Color.BRIGHT_CYAN}/analyze <图片路径> [提示词] {Color.RESET}- 分析图片")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET}   例如: /analyze test.jpg 描述图片的内容")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET}   如果不提供提示词，将使用默认提示词'描述图片的内容'")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET}")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {Color.BRIGHT_CYAN}/browse [目录路径] {Color.RESET}- 浏览指定目录中的图片")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET}   例如: /browse ./images")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET}   如果不提供目录路径，将浏览当前目录")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET}")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {Color.BRIGHT_CYAN}/models {Color.RESET}- 显示可用的图片分析模型")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {Color.BRIGHT_CYAN}/set model <模型名称> {Color.RESET}- 设置使用的模型")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET}   例如: /set model BlueLM-Vision-prd")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET}")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {Color.BRIGHT_CYAN}/examples {Color.RESET}- 显示分析提示词示例")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {Color.BRIGHT_CYAN}/back {Color.RESET}- 返回聊天模式")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {Color.BRIGHT_CYAN}/help {Color.RESET}- 显示此帮助信息")
    print(f"{Color.BRIGHT_BLUE}└{'─'*58}┘{Color.RESET}\n")

def parse_analyze_command(command):
    """解析图片分析命令及参数
    
    Args:
        command: 命令字符串
        
    Returns:
        (image_path, prompt) 元组，如果解析失败返回 (None, None)
    """
    # 基本命令格式: /analyze <图片路径> [提示词]
    pattern = r'^/analyze\s+([^\s]+)(?:\s+(.+))?$'
    match = re.match(pattern, command)
    
    if not match:
        return None, None
    
    image_path = match.group(1)
    prompt = match.group(2) if match.group(2) else "描述图片的内容"
    
    return image_path, prompt

def parse_browse_command(command):
    """解析浏览图片目录命令及参数
    
    Args:
        command: 命令字符串
        
    Returns:
        目录路径，如果未指定则返回 "./"
    """
    # 基本命令格式: /browse [目录路径]
    pattern = r'^/browse(?:\s+(.+))?$'
    match = re.match(pattern, command)
    
    if not match:
        return "./"
    
    directory = match.group(1) if match.group(1) else "./"
    return directory

def parse_set_model_command(command):
    """解析设置模型命令及参数
    
    Args:
        command: 命令字符串
        
    Returns:
        模型名称，如果解析失败返回 None
    """
    # 基本命令格式: /set model <模型名称>
    pattern = r'^/set\s+model\s+(.+)$'
    match = re.match(pattern, command)
    
    if not match:
        return None
    
    model = match.group(1)
    return model

# 测试功能
if __name__ == "__main__":
    print_vision_welcome()
    print_vision_header()
    print_help_vision()
    print_models()
    print_examples() 