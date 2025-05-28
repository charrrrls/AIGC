#!/usr/bin/env python
# encoding: utf-8

import os
import time
import sys
from chat_ui import Color

# 绘画ASCII艺术
DRAWING_ASCII = """
   .---. 
  /     \\
 | O   O |
  \\ \\|/ /
   '---'
     |
    /|\\
    / \\
"""

def print_drawing_welcome():
    """打印绘画功能欢迎信息"""
    print(f"\n{Color.CYAN}{Color.BOLD}")
    print("="*60)
    print("                蓝心AI绘画助手                ")
    print("="*60)
    print(f"{Color.RESET}")
    print(f"{Color.YELLOW}输入 'back' 返回聊天模式{Color.RESET}\n")
    print(f"{Color.CYAN}支持命令: {Color.RESET}")
    print(f"  {Color.GREEN}/draw <提示词> {Color.RESET}- 创建新的绘图")
    print(f"  {Color.GREEN}/styles {Color.RESET}- 显示可用绘画风格")
    print(f"  {Color.GREEN}/prompts {Color.RESET}- 显示绘画提示词推荐")
    print(f"  {Color.GREEN}/status <任务ID> {Color.RESET}- 查询任务状态")
    print(f"  {Color.GREEN}/cancel <任务ID> {Color.RESET}- 取消绘画任务")
    print(f"  {Color.GREEN}/settings {Color.RESET}- 查看或修改绘画设置\n")

def print_drawing_header():
    """打印绘画模式标题"""
    print(f"\n{Color.CYAN}{Color.BOLD}[绘画模式]{Color.RESET}\n")

def print_drawing_prompt():
    """打印绘画提示符"""
    print(f"{Color.MAGENTA}{Color.BOLD}绘画>>> {Color.RESET}", end="", flush=True)
    return input()

def print_styles(styles):
    """打印可用的绘画风格"""
    if not styles or "result" not in styles or not styles["result"]:
        print(f"{Color.RED}获取风格列表失败!{Color.RESET}")
        return
    
    print(f"\n{Color.CYAN}{Color.BOLD}可用绘画风格列表:{Color.RESET}")
    print(f"{Color.YELLOW}{'风格ID':<40} | {'风格名称':<15} | {'推荐参数'}{Color.RESET}")
    print("-" * 80)
    
    for style in styles["result"]:
        style_id = style.get("style_id", "")
        style_name = style.get("style_name", "")
        
        params = []
        if "cfg_scale" in style:
            params.append(f"文本相关度:{style['cfg_scale']}")
        if "denoising_strength" in style:
            params.append(f"图片相关度:{style['denoising_strength']}")
        if "ctrl_net_strength" in style:
            params.append(f"控制强度:{style['ctrl_net_strength']}")
        if "steps" in style:
            params.append(f"采样步数:{style['steps']}")
        
        params_str = ", ".join(params)
        print(f"{style_id:<40} | {style_name:<15} | {params_str}")
    
    print("\n")

def print_prompts(prompts):
    """打印推荐提示词"""
    if not prompts or "result" not in prompts or not prompts["result"]:
        print(f"{Color.RED}获取推荐提示词失败!{Color.RESET}")
        return
    
    print(f"\n{Color.CYAN}{Color.BOLD}绘画推荐提示词:{Color.RESET}")
    print("-" * 80)
    
    for i, prompt in enumerate(prompts["result"], 1):
        short_text = prompt.get("short_text", "")
        long_text = prompt.get("long_text", "")
        
        print(f"{Color.YELLOW}{i}.{Color.RESET} {short_text}")
        if long_text and long_text != short_text:
            print(f"   {Color.CYAN}{long_text}{Color.RESET}")
        print("")
    
    print("\n")

def print_task_submitted(response):
    """打印任务提交成功信息"""
    if not response or response.get("code") != 200:
        error_msg = response.get("msg", "未知错误") if response else "请求失败"
        print(f"{Color.RED}任务提交失败: {error_msg}{Color.RESET}")
        return None
    
    task_id = response["result"]["task_id"]
    task_type = response["result"].get("task_type", "")
    model = response["result"].get("model", "")
    
    print(f"\n{Color.GREEN}{Color.BOLD}绘画任务已提交!{Color.RESET}")
    print(f"{Color.YELLOW}任务ID: {Color.RESET}{task_id}")
    print(f"{Color.YELLOW}任务类型: {Color.RESET}{task_type}")
    print(f"{Color.YELLOW}模型版本: {Color.RESET}{model}")
    print(f"\n{Color.CYAN}使用 '/status {task_id}' 查询任务状态{Color.RESET}")
    print(f"{Color.CYAN}使用 '/cancel {task_id}' 取消任务{Color.RESET}\n")
    
    return task_id

def print_task_progress(response):
    """打印任务进度"""
    if not response or response.get("code") != 200:
        error_msg = response.get("msg", "未知错误") if response else "请求失败"
        print(f"{Color.RED}查询任务状态失败: {error_msg}{Color.RESET}")
        return False, None
    
    result = response["result"]
    task_id = result.get("task_id", "")
    status = result.get("status", -1)
    finished = result.get("finished", False)
    queue_ahead = result.get("queue_ahead", 0)
    task_eta = result.get("task_eta", 0)
    
    status_text = "未知"
    if status == 0:
        status_text = f"{Color.YELLOW}队列中{Color.RESET}"
    elif status == 1:
        status_text = f"{Color.CYAN}处理中{Color.RESET}"
    elif status == 2:
        status_text = f"{Color.GREEN}已完成{Color.RESET}"
    elif status == 3:
        status_text = f"{Color.RED}处理失败{Color.RESET}"
    elif status == 4:
        status_text = f"{Color.YELLOW}已取消{Color.RESET}"
    
    print(f"\n{Color.BOLD}任务状态:{Color.RESET}")
    print(f"{Color.YELLOW}任务ID: {Color.RESET}{task_id}")
    print(f"{Color.YELLOW}状态: {Color.RESET}{status_text}")
    
    if status == 0:
        print(f"{Color.YELLOW}排队位置: {Color.RESET}{queue_ahead}")
        print(f"{Color.YELLOW}预计等待时间: {Color.RESET}{task_eta}秒")
    
    if finished and status == 2:
        images_url = result.get("images_url", [])
        if images_url:
            print(f"\n{Color.GREEN}{Color.BOLD}绘画完成! 图片URL:{Color.RESET}")
            for i, url in enumerate(images_url, 1):
                print(f"{i}. {url}")
            return True, images_url
    
    return finished, None

def print_task_canceled(response):
    """打印取消任务结果"""
    if not response or response.get("code") != 200:
        error_msg = response.get("msg", "未知错误") if response else "请求失败"
        print(f"{Color.RED}取消任务失败: {error_msg}{Color.RESET}")
        return False
    
    print(f"\n{Color.GREEN}任务已取消!{Color.RESET}")
    return True

def print_image_saved(filepath):
    """打印图片保存成功的消息"""
    if not filepath:
        print(f"{Color.RED}图片下载失败!{Color.RESET}")
        return
    
    print(f"\n{Color.GREEN}图片已保存至: {Color.RESET}{filepath}")

def print_drawing_progress(wait_message="绘画中"):
    """打印绘画进度动画"""
    sys.stdout.write(f"\r{Color.CYAN}{wait_message}")
    for i in range(3):
        time.sleep(0.3)
        sys.stdout.write(".")
    sys.stdout.flush()
    
def print_drawing_animation(seconds=5):
    """打印绘画过程的动画，持续指定的秒数"""
    frames = [
        "🖌️  .     ",
        "🖌️  ..    ",
        "🖌️  ...   ",
        "🖌️  ....  ",
        "🖌️  ..... ",
        "🖌️  ......",
    ]
    
    start_time = time.time()
    frame_index = 0
    
    while time.time() - start_time < seconds:
        sys.stdout.write(f"\r{Color.CYAN}{Color.BOLD}AI绘画中 {frames[frame_index]}{Color.RESET}")
        sys.stdout.flush()
        frame_index = (frame_index + 1) % len(frames)
        time.sleep(0.2)
    
    sys.stdout.write("\r" + " " * 50 + "\r")
    sys.stdout.flush()

def print_drawing_settings(settings):
    """打印绘画设置"""
    print(f"\n{Color.CYAN}{Color.BOLD}当前绘画设置:{Color.RESET}")
    print(f"{Color.YELLOW}图像尺寸: {Color.RESET}{settings.get('width')}x{settings.get('height')}")
    print(f"{Color.YELLOW}风格模板: {Color.RESET}{settings.get('style_name', '默认')}")
    print(f"{Color.YELLOW}文本相关度: {Color.RESET}{settings.get('cfg_scale')}")
    print(f"{Color.YELLOW}采样步数: {Color.RESET}{settings.get('steps')}")
    print("\n")

def print_help_drawing():
    """打印绘画帮助信息"""
    print(f"\n{Color.CYAN}{Color.BOLD}绘画命令帮助:{Color.RESET}")
    print(f"  {Color.GREEN}/draw <提示词> {Color.RESET}- 创建新的绘图")
    print(f"    例如: /draw 一只可爱的小猫")
    print(f"    支持参数:")
    print(f"      --style <风格ID> : 指定绘画风格")
    print(f"      --width <宽> : 设置宽度(像素)")
    print(f"      --height <高> : 设置高度(像素)")
    print(f"      --cfg <数值> : 设置文本相关度(3-15)")
    print(f"      --steps <数值> : 设置采样步数(20-50)")
    print(f"      --seed <数值> : 设置随机种子")
    print(f"      --negative <文本> : 设置反向提示词")
    
    print(f"\n  {Color.GREEN}/styles {Color.RESET}- 显示可用绘画风格")
    print(f"  {Color.GREEN}/prompts {Color.RESET}- 显示绘画提示词推荐")
    print(f"  {Color.GREEN}/status <任务ID> {Color.RESET}- 查询任务状态")
    print(f"  {Color.GREEN}/cancel <任务ID> {Color.RESET}- 取消绘画任务")
    print(f"  {Color.GREEN}/settings {Color.RESET}- 查看或修改绘画设置")
    print(f"  {Color.GREEN}/back {Color.RESET}- 返回聊天模式")
    print(f"  {Color.GREEN}/help {Color.RESET}- 显示此帮助信息\n")

# 测试功能
if __name__ == "__main__":
    print_drawing_welcome()
    print_drawing_header()
    print_drawing_animation(3)
    print_help_drawing() 