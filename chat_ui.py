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
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_CYAN = '\033[96m'
    GRAY = '\033[90m'
    
    # 背景色
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    BG_GRAY = '\033[100m'
    
    # 样式
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    ITALIC = '\033[3m'
    DIM = '\033[2m'
    
    # 复位
    RESET = '\033[0m'

# 现代简约风格的ASCII头像
USER_AVATAR = """
    ┌─────┐
    │     │
    │  ◆  │
    │     │
    └─────┘
"""

ROBOT_AVATAR = """
    ┌─────┐
    │  ⊙  │
    │  ▒  │
    │  ▓  │
    └─────┘
"""

def clear_screen():
    """清屏"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_welcome():
    """打印欢迎信息"""
    clear_screen()
    print(f"{Color.BG_GRAY}{Color.WHITE}{Color.BOLD}")
    print("┌" + "─" * 58 + "┐")
    print("│" + " " * 58 + "│")
    print("│" + "            蓝心大模型聊天助手            ".center(58) + "│")
    print("│" + " " * 58 + "│")
    print("└" + "─" * 58 + "┘")
    print(f"{Color.RESET}")
    print(f"{Color.GRAY}● 输入 'exit' 或 'quit' 退出对话{Color.RESET}")
    print(f"{Color.GRAY}● 输入 '/draw' 进入绘画模式{Color.RESET}")
    print(f"{Color.GRAY}● 输入 '/vision' 进入图片分析模式{Color.RESET}")
    print(f"{Color.GRAY}● 输入 '/speech' 进入语音识别模式{Color.RESET}\n")

def print_user_message(message):
    """打印用户消息，带颜色和头像"""
    print(f"\n{Color.BRIGHT_BLUE}{USER_AVATAR}{Color.RESET}")
    print(f"{Color.BRIGHT_BLUE}┌─{' 您 ':─^56}─┐{Color.RESET}")
    print(f"{Color.BRIGHT_BLUE}│{Color.RESET} {message}")
    print(f"{Color.BRIGHT_BLUE}└{'─'*58}┘{Color.RESET}\n")

def print_ai_message(message):
    """打印AI消息，带颜色和头像"""
    print(f"\n{Color.BRIGHT_CYAN}{ROBOT_AVATAR}{Color.RESET}")
    print(f"{Color.BRIGHT_CYAN}┌─{' 蓝心 ':─^54}─┐{Color.RESET}")
    print(f"{Color.BRIGHT_CYAN}│{Color.RESET} {message}")
    print(f"{Color.BRIGHT_CYAN}└{'─'*58}┘{Color.RESET}\n")

def print_thinking():
    """打印思考动画"""
    print(f"{Color.BRIGHT_CYAN}蓝心思考中", end="", flush=True)
    for _ in range(3):
        time.sleep(0.3)
        print("●", end="", flush=True)
    print(f"{Color.RESET}")

def print_streaming_ai_message(chunks):
    """打印流式响应的AI消息，带颜色和头像"""
    print(f"\n{Color.BRIGHT_CYAN}{ROBOT_AVATAR}{Color.RESET}")
    print(f"{Color.BRIGHT_CYAN}┌─{' 蓝心 ':─^54}─┐{Color.RESET}")
    print(f"{Color.BRIGHT_CYAN}│{Color.RESET} ", end="", flush=True)
    
    full_text = ""
    for chunk in chunks:
        print(f"{chunk}", end="", flush=True)
        full_text += chunk
        time.sleep(0.01)  # 控制显示速度
    
    print(f"\n{Color.BRIGHT_CYAN}└{'─'*58}┘{Color.RESET}\n")
    return full_text

# 测试颜色功能
def test_color():
    """测试终端颜色显示"""
    print(f"{Color.RED}这是红色文字{Color.RESET}")
    print(f"{Color.GREEN}这是绿色文字{Color.RESET}")
    print(f"{Color.BLUE}这是蓝色文字{Color.RESET}")
    print(f"{Color.BRIGHT_BLUE}这是亮蓝色文字{Color.RESET}")
    print(f"{Color.YELLOW}这是黄色文字{Color.RESET}")
    print(f"{Color.MAGENTA}这是洋红色文字{Color.RESET}")
    print(f"{Color.CYAN}这是青色文字{Color.RESET}")
    print(f"{Color.BRIGHT_CYAN}这是亮青色文字{Color.RESET}")
    print(f"{Color.BOLD}这是粗体文字{Color.RESET}")
    print(f"{Color.UNDERLINE}这是下划线文字{Color.RESET}")
    print(f"{Color.BG_GRAY}{Color.WHITE}这是灰色背景白色文字{Color.RESET}")

# 如果是主程序，则运行测试
if __name__ == "__main__":
    test_color()
    print_welcome()
    print_user_message("你好，我想问一个问题。")
    print_thinking()
    print_ai_message("您好！我是蓝心助手，很高兴为您服务。请问有什么可以帮助您的？") 