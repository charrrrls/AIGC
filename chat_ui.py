#!/usr/bin/env python
# encoding: utf-8

import os
import time
import sys

# ANSI转义码-颜色常量
class Color:
    # 前景色(文字颜色)
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # 背景色
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    
    # 样式
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    ITALIC = '\033[3m'
    
    # 复位
    RESET = '\033[0m'

# 卡通头像ASCII字符
USER_AVATAR = """
    ,---.
   /    |
  |     |
   \    /
    `---'
"""

ROBOT_AVATAR = """
    .---. 
   /     \\
  | o . o |
   \ \_/ /
    '---'
"""

def clear_screen():
    """清屏"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_welcome():
    """打印欢迎信息"""
    clear_screen()
    print(f"{Color.CYAN}{Color.BOLD}")
    print("="*60)
    print("                蓝心大模型聊天助手                ")
    print("="*60)
    print(f"{Color.RESET}")
    print(f"{Color.YELLOW}输入 'exit' 或 'quit' 退出对话{Color.RESET}\n")

def print_user_message(message):
    """打印用户消息，带颜色和头像"""
    print(f"\n{Color.GREEN}{USER_AVATAR}{Color.RESET}")
    print(f"{Color.GREEN}{Color.BOLD}您: {Color.RESET}{Color.GREEN}{message}{Color.RESET}\n")

def print_ai_message(message):
    """打印AI消息，带颜色和头像"""
    print(f"\n{Color.BLUE}{ROBOT_AVATAR}{Color.RESET}")
    print(f"{Color.BLUE}{Color.BOLD}蓝心: {Color.RESET}{Color.CYAN}{message}{Color.RESET}\n")

def print_thinking():
    """打印思考动画"""
    print(f"{Color.BLUE}{Color.BOLD}蓝心正在思考", end="", flush=True)
    for _ in range(3):
        time.sleep(0.3)
        print(".", end="", flush=True)
    print(f"{Color.RESET}")

def print_streaming_ai_message(chunks):
    """打印流式响应的AI消息，带颜色和头像"""
    print(f"\n{Color.BLUE}{ROBOT_AVATAR}{Color.RESET}")
    print(f"{Color.BLUE}{Color.BOLD}蓝心: {Color.RESET}", end="", flush=True)
    
    full_text = ""
    for chunk in chunks:
        print(f"{Color.CYAN}{chunk}{Color.RESET}", end="", flush=True)
        full_text += chunk
        time.sleep(0.01)  # 控制显示速度
    
    print("\n")
    return full_text

# 测试颜色功能
def test_color():
    """测试终端颜色显示"""
    print(f"{Color.RED}这是红色文字{Color.RESET}")
    print(f"{Color.GREEN}这是绿色文字{Color.RESET}")
    print(f"{Color.BLUE}这是蓝色文字{Color.RESET}")
    print(f"{Color.YELLOW}这是黄色文字{Color.RESET}")
    print(f"{Color.MAGENTA}这是洋红色文字{Color.RESET}")
    print(f"{Color.CYAN}这是青色文字{Color.RESET}")
    print(f"{Color.BOLD}这是粗体文字{Color.RESET}")
    print(f"{Color.UNDERLINE}这是下划线文字{Color.RESET}")
    print(f"{Color.BG_RED}这是红色背景文字{Color.RESET}")

# 如果是主程序，则运行测试
if __name__ == "__main__":
    test_color()
    print_welcome()
    print_user_message("你好，我想问一个问题。")
    print_thinking()
    print_ai_message("你好！我是蓝心助手，请问有什么可以帮助你的？") 