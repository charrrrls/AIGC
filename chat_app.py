#!/usr/bin/env python
# encoding: utf-8

import json
import time
import sys
import argparse
import re
import os
import shutil

from vivogpt_api import VivoGPT, process_stream_response
from vivogpt_draw import VivoArtAPI
from vivogpt_vision import VivoVisionAPI
from vivogpt_speech import VivoSpeechAPI
from chat_ui import (
    Color, clear_screen, print_welcome, 
    print_user_message, print_ai_message, 
    print_thinking, print_streaming_ai_message
)
from draw_ui import (
    print_drawing_welcome, print_drawing_header,
    print_drawing_prompt, print_styles, print_prompts,
    print_task_submitted, print_task_progress,
    print_task_canceled, print_image_saved,
    print_drawing_animation, print_drawing_settings,
    print_help_drawing
)
from vision_ui import (
    print_vision_welcome, print_vision_header,
    print_vision_prompt, print_models, print_examples,
    print_browse_images, print_analyzing_animation,
    print_image_info, print_analysis_result,
    print_streaming_analysis_result, print_help_vision,
    parse_analyze_command, parse_browse_command,
    parse_set_model_command
)
from speech_ui import (
    print_speech_welcome, print_speech_header,
    print_speech_prompt, print_recording_animation,
    print_recognizing_animation, print_speech_result,
    print_audio_files, print_save_result, print_help_speech,
    parse_record_command, parse_recognize_command,
    parse_save_command, ensure_audio_dir
)

# 默认配置
DEFAULT_APP_ID = "2025827557"
DEFAULT_APP_KEY = "kIFmdMYqpZHhbgap"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 2048
DEFAULT_STREAM = True

# 默认绘画设置
DEFAULT_DRAWING_SETTINGS = {
    'width': 1024,
    'height': 1024,
    'style_id': '4cbc9165bc615ea0815301116e7925a3',  # 通用v6.0
    'style_name': '通用v6.0',
    'cfg_scale': 7,
    'steps': 20,
    'output_dir': './images'
}

# 默认图片分析设置
DEFAULT_VISION_SETTINGS = {
    'model': 'BlueLM-Vision-prd',
    'default_prompt': '描述图片的内容',
    'use_stream': True
}

# 默认语音识别设置
DEFAULT_SPEECH_SETTINGS = {
    'duration': 5,
    'sample_rate': 16000,
    'chunk_size': 1024,
    'output_dir': './audio'
}

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='蓝心大模型聊天助手')
    parser.add_argument('--app_id', type=str, default=DEFAULT_APP_ID, help='应用ID')
    parser.add_argument('--app_key', type=str, default=DEFAULT_APP_KEY, help='应用密钥')
    parser.add_argument('--temperature', type=float, default=DEFAULT_TEMPERATURE, help='温度参数(0.1-1.0)')
    parser.add_argument('--max_tokens', type=int, default=DEFAULT_MAX_TOKENS, help='最大生成长度')
    parser.add_argument('--no_stream', action='store_true', help='不使用流式输出')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    parser.add_argument('--draw', action='store_true', help='直接进入绘画模式')
    parser.add_argument('--vision', action='store_true', help='直接进入图片分析模式')
    parser.add_argument('--speech', action='store_true', help='直接进入语音识别模式')
    return parser.parse_args()

def parse_draw_command(command):
    """解析绘图命令及参数"""
    # 解析主命令和参数
    command_pattern = r'^/draw\s+(.+?)(?:\s+--\w+|$)'
    param_pattern = r'--(\w+)\s+([^-][^-]*?)(?:\s+--|$)'
    
    command_match = re.search(command_pattern, command, re.DOTALL)
    if not command_match:
        return None, {}
    
    prompt = command_match.group(1).strip()
    
    # 提取参数
    params = {}
    for match in re.finditer(param_pattern, command + " ", re.DOTALL):
        param_name = match.group(1)
        param_value = match.group(2).strip()
        params[param_name] = param_value
    
    return prompt, params

def run_drawing_mode(args):
    """运行绘画模式"""
    # 初始化API客户端
    vivo_art = VivoArtAPI(args.app_id, args.app_key)
    vivo_art.set_debug_mode(args.debug)
    
    # 初始化绘画设置
    drawing_settings = DEFAULT_DRAWING_SETTINGS.copy()
    
    # 创建输出目录
    if not os.path.exists(drawing_settings['output_dir']):
        os.makedirs(drawing_settings['output_dir'])
    
    # 打印绘画模式欢迎信息
    clear_screen()
    print_drawing_welcome()
    
    # 绘画模式主循环
    active_tasks = {}  # 记录活跃任务，键为任务ID，值为任务信息
    
    try:
        while True:
            command = print_drawing_prompt()
            
            # 退出命令
            if command.lower() in ['exit', 'quit']:
                print(f"{Color.YELLOW}感谢使用蓝心绘画助手，再见！{Color.RESET}")
                sys.exit(0)
            
            # 返回聊天模式
            if command.lower() in ['back', '/back']:
                return
            
            # 空命令
            if not command.strip():
                continue
            
            # 帮助命令
            if command.lower() in ['help', '/help']:
                print_help_drawing()
                continue
            
            # 查看风格列表
            if command.lower() in ['styles', '/styles']:
                styles = vivo_art.get_styles()
                print_styles(styles)
                
                # 更新可用风格到设置中
                if styles and styles.get("code") == 200 and styles.get("result"):
                    for style in styles["result"]:
                        if style.get("style_id") == drawing_settings["style_id"]:
                            drawing_settings["style_name"] = style.get("style_name", "默认")
                
                continue
            
            # 查看推荐提示词
            if command.lower() in ['prompts', '/prompts']:
                prompts = vivo_art.get_prompts()
                print_prompts(prompts)
                continue
            
            # 查询任务状态
            if command.lower().startswith("status ") or command.lower().startswith("/status "):
                task_id = command.split(" ", 1)[1].strip()
                response = vivo_art.query_task_progress(task_id)
                finished, image_urls = print_task_progress(response)
                
                # 如果任务完成，保存图片
                if finished and image_urls:
                    print(f"\n{Color.CYAN}正在下载图片...{Color.RESET}")
                    for i, url in enumerate(image_urls):
                        filepath = vivo_art.download_image(
                            url, 
                            drawing_settings['output_dir'], 
                            f"drawing_{task_id}_{i}.jpg"
                        )
                        print_image_saved(filepath)
                
                continue
            
            # 取消任务
            if command.lower().startswith("cancel ") or command.lower().startswith("/cancel "):
                task_id = command.split(" ", 1)[1].strip()
                response = vivo_art.cancel_task(task_id)
                print_task_canceled(response)
                continue
            
            # 查看或修改设置
            if command.lower() in ['settings', '/settings']:
                print_drawing_settings(drawing_settings)
                
                # 询问是否修改设置
                print(f"{Color.YELLOW}是否修改设置? (y/n){Color.RESET}")
                if input().lower() == 'y':
                    print(f"{Color.CYAN}输入新的宽度 (像素)，当前: {drawing_settings['width']}{Color.RESET}")
                    width = input().strip()
                    if width and width.isdigit():
                        drawing_settings['width'] = int(width)
                    
                    print(f"{Color.CYAN}输入新的高度 (像素)，当前: {drawing_settings['height']}{Color.RESET}")
                    height = input().strip()
                    if height and height.isdigit():
                        drawing_settings['height'] = int(height)
                    
                    print(f"{Color.CYAN}输入新的文本相关度 (3-15)，当前: {drawing_settings['cfg_scale']}{Color.RESET}")
                    cfg = input().strip()
                    if cfg and cfg.replace('.', '', 1).isdigit():
                        drawing_settings['cfg_scale'] = float(cfg)
                    
                    print(f"{Color.CYAN}输入新的采样步数 (20-50)，当前: {drawing_settings['steps']}{Color.RESET}")
                    steps = input().strip()
                    if steps and steps.isdigit():
                        drawing_settings['steps'] = int(steps)
                    
                    print(f"{Color.GREEN}设置已更新!{Color.RESET}")
                    print_drawing_settings(drawing_settings)
                
                continue
            
            # 处理绘图命令
            if command.lower().startswith("draw ") or command.lower().startswith("/draw "):
                prompt, params = parse_draw_command(command)
                
                if not prompt:
                    print(f"{Color.RED}无效的绘图命令，请提供提示词!{Color.RESET}")
                    print(f"{Color.YELLOW}正确格式: /draw <提示词> [--参数 值]{Color.RESET}")
                    continue
                
                # 处理参数
                style = params.get('style', drawing_settings['style_id'])
                width = int(params.get('width', drawing_settings['width']))
                height = int(params.get('height', drawing_settings['height']))
                cfg_scale = float(params.get('cfg', drawing_settings['cfg_scale']))
                steps = int(params.get('steps', drawing_settings['steps']))
                seed = int(params.get('seed', -1))
                negative_prompt = params.get('negative', '')
                
                # 提交绘画任务
                print(f"\n{Color.CYAN}正在提交绘画任务...{Color.RESET}")
                response = vivo_art.submit_drawing_task(
                    prompt=prompt,
                    style_config=style,
                    height=height,
                    width=width,
                    seed=seed,
                    cfg_scale=cfg_scale,
                    steps=steps,
                    negative_prompt=negative_prompt
                )
                
                # 打印提交结果
                task_id = print_task_submitted(response)
                if task_id:
                    active_tasks[task_id] = {
                        'prompt': prompt,
                        'time': time.time()
                    }
                
                continue
            
            # 直接作为提示词处理
            if not command.startswith('/'):
                # 使用默认设置进行绘图
                print(f"\n{Color.CYAN}使用提示词: '{command}' 创建绘图任务...{Color.RESET}")
                
                response = vivo_art.submit_drawing_task(
                    prompt=command,
                    style_config=drawing_settings['style_id'],
                    height=drawing_settings['height'],
                    width=drawing_settings['width'],
                    cfg_scale=drawing_settings['cfg_scale'],
                    steps=drawing_settings['steps']
                )
                
                # 打印提交结果
                task_id = print_task_submitted(response)
                if task_id:
                    active_tasks[task_id] = {
                        'prompt': command,
                        'time': time.time()
                    }
                
                continue
            
            # 未识别的命令
            print(f"{Color.RED}未识别的命令: {command}{Color.RESET}")
            print(f"{Color.YELLOW}输入 '/help' 查看可用命令{Color.RESET}")
            
    except KeyboardInterrupt:
        print(f"{Color.YELLOW}\n返回聊天模式...{Color.RESET}")
        return

def run_vision_mode(args):
    """运行图片分析模式"""
    # 初始化API客户端
    vivo_vision = VivoVisionAPI(args.app_id, args.app_key)
    vivo_vision.set_debug_mode(args.debug)
    
    # 初始化图片分析设置
    vision_settings = DEFAULT_VISION_SETTINGS.copy()
    vivo_vision.set_model(vision_settings['model'])
    
    # 打印图片分析模式欢迎信息
    clear_screen()
    print_vision_welcome()
    
    # 图片分析模式主循环
    try:
        while True:
            command = print_vision_prompt()
            
            # 退出命令
            if command.lower() in ['exit', 'quit']:
                print(f"{Color.YELLOW}感谢使用蓝心图片分析助手，再见！{Color.RESET}")
                sys.exit(0)
            
            # 返回聊天模式
            if command.lower() in ['back', '/back']:
                return
            
            # 空命令
            if not command.strip():
                continue
            
            # 帮助命令
            if command.lower() in ['help', '/help']:
                print_help_vision()
                continue
            
            # 查看可用模型
            if command.lower() in ['models', '/models']:
                print_models()
                continue
            
            # 查看提示词示例
            if command.lower() in ['examples', '/examples']:
                print_examples()
                continue
            
            # 处理浏览图片命令
            if command.lower().startswith("browse") or command.lower().startswith("/browse"):
                directory = parse_browse_command(command)
                print_browse_images(directory)
                continue
            
            # 处理设置模型命令
            if command.lower().startswith("set model") or command.lower().startswith("/set model"):
                model = parse_set_model_command(command)
                if model:
                    try:
                        vivo_vision.set_model(model)
                        vision_settings['model'] = model
                        print(f"{Color.GREEN}已设置模型: {model}{Color.RESET}")
                    except Exception as e:
                        print(f"{Color.RED}设置模型失败: {str(e)}{Color.RESET}")
                else:
                    print(f"{Color.RED}无效的模型设置命令，请使用格式: /set model <模型名称>{Color.RESET}")
                continue
            
            # 处理分析图片命令
            if command.lower().startswith("analyze") or command.lower().startswith("/analyze"):
                image_path, prompt = parse_analyze_command(command)
                
                if not image_path:
                    print(f"{Color.RED}无效的分析命令，请提供图片路径!{Color.RESET}")
                    print(f"{Color.YELLOW}正确格式: /analyze <图片路径> [提示词]{Color.RESET}")
                    continue
                
                # 检查文件是否存在
                if not print_image_info(image_path):
                    continue
                
                # 分析图片
                print(f"{Color.CYAN}使用提示词: '{prompt}' 分析图片...{Color.RESET}")
                
                # 显示分析动画
                print_analyzing_animation(3)
                
                # 根据设置决定是否使用流式输出
                if vision_settings['use_stream']:
                    # 流式输出
                    try:
                        chunks = vivo_vision.analyze_image_stream(image_path, prompt)
                        result = print_streaming_analysis_result(chunks)
                    except Exception as e:
                        print(f"{Color.RED}图片分析失败: {str(e)}{Color.RESET}")
                else:
                    # 同步输出
                    try:
                        result = vivo_vision.analyze_image_sync(image_path, prompt)
                        print_analysis_result(result)
                    except Exception as e:
                        print(f"{Color.RED}图片分析失败: {str(e)}{Color.RESET}")
                
                continue
            
            # 未识别的命令，如果是图片路径，尝试直接分析
            if not command.startswith('/') and os.path.isfile(command):
                # 检查文件是否存在
                if not print_image_info(command):
                    continue
                
                # 分析图片
                prompt = vision_settings['default_prompt']
                print(f"{Color.CYAN}使用默认提示词: '{prompt}' 分析图片...{Color.RESET}")
                
                # 显示分析动画
                print_analyzing_animation(3)
                
                # 根据设置决定是否使用流式输出
                if vision_settings['use_stream']:
                    # 流式输出
                    try:
                        chunks = vivo_vision.analyze_image_stream(command, prompt)
                        result = print_streaming_analysis_result(chunks)
                    except Exception as e:
                        print(f"{Color.RED}图片分析失败: {str(e)}{Color.RESET}")
                else:
                    # 同步输出
                    try:
                        result = vivo_vision.analyze_image_sync(command, prompt)
                        print_analysis_result(result)
                    except Exception as e:
                        print(f"{Color.RED}图片分析失败: {str(e)}{Color.RESET}")
                
                continue
            
            # 未识别的命令
            print(f"{Color.RED}未识别的命令: {command}{Color.RESET}")
            print(f"{Color.YELLOW}输入 '/help' 查看可用命令{Color.RESET}")
            
    except KeyboardInterrupt:
        print(f"{Color.YELLOW}\n返回聊天模式...{Color.RESET}")
        return

def run_speech_mode(args):
    """运行语音识别模式"""
    # 初始化API客户端
    vivo_speech = VivoSpeechAPI(args.app_id, args.app_key)
    vivo_speech.set_debug_mode(args.debug)
    
    # 初始化语音识别设置
    speech_settings = DEFAULT_SPEECH_SETTINGS.copy()
    
    # 确保音频输出目录存在
    ensure_audio_dir(speech_settings['output_dir'])
    
    # 打印语音识别模式欢迎信息
    clear_screen()
    print_speech_welcome()
    
    # 尝试连接语音识别服务
    if not vivo_speech.connect():
        print(f"{Color.RED}无法连接到语音识别服务，请检查网络连接{Color.RESET}")
    
    # 语音识别模式主循环
    try:
        while True:
            command = print_speech_prompt()
            
            # 退出命令
            if command.lower() in ['exit', 'quit']:
                print(f"{Color.YELLOW}感谢使用蓝心语音识别助手，再见！{Color.RESET}")
                vivo_speech.disconnect()
                sys.exit(0)
            
            # 返回聊天模式
            if command.lower() in ['back', '/back']:
                vivo_speech.disconnect()
                return
            
            # 空命令
            if not command.strip():
                continue
            
            # 帮助命令
            if command.lower() in ['help', '/help']:
                print_help_speech()
                continue
            
            # 查看音频文件目录
            if command.lower() in ['files', '/files']:
                print_audio_files(speech_settings['output_dir'])
                continue
            
            # 处理录音并识别命令
            if command.lower().startswith("record") or command.lower().startswith("/record"):
                duration = parse_record_command(command)
                
                if duration is not None:
                    # 显示录音动画
                    print_recording_animation(duration)
                    
                    # 录音并识别
                    result = vivo_speech.record_and_recognize(
                        duration=duration,
                        sample_rate=speech_settings['sample_rate'],
                        chunk_size=speech_settings['chunk_size']
                    )
                    
                    # 显示识别结果
                    print_speech_result(result)
                else:
                    print(f"{Color.RED}无效的录音命令，请使用格式: /record [持续时间]{Color.RESET}")
                
                continue
            
            # 处理识别音频文件命令
            if command.lower().startswith("recognize") or command.lower().startswith("/recognize"):
                file_path = parse_recognize_command(command)
                
                if file_path:
                    # 检查文件是否存在
                    if not os.path.exists(file_path):
                        print(f"{Color.RED}文件不存在: {file_path}{Color.RESET}")
                        continue
                    
                    # 显示识别动画
                    print_recognizing_animation()
                    
                    # 识别音频文件
                    result = vivo_speech.recognize_wav_file(
                        file_path=file_path,
                        chunk_size=speech_settings['chunk_size']
                    )
                    
                    # 显示识别结果
                    print_speech_result(result)
                else:
                    print(f"{Color.RED}无效的识别命令，请使用格式: /recognize <文件路径>{Color.RESET}")
                
                continue
            
            # 处理录音并保存命令
            if command.lower().startswith("save") or command.lower().startswith("/save"):
                filename, duration = parse_save_command(command)
                
                if filename:
                    # 确保文件名正确
                    if not filename.lower().endswith(".wav"):
                        filename += ".wav"
                    
                    # 构建完整的文件路径
                    output_file = os.path.join(speech_settings['output_dir'], filename)
                    
                    # 显示录音动画
                    print_recording_animation(duration)
                    
                    # 录音并保存
                    success = vivo_speech.save_recording(
                        output_file=output_file,
                        duration=duration,
                        sample_rate=speech_settings['sample_rate'],
                        chunk_size=speech_settings['chunk_size']
                    )
                    
                    # 显示保存结果
                    print_save_result(success, output_file)
                else:
                    print(f"{Color.RED}无效的保存命令，请使用格式: /save <文件名> [持续时间]{Color.RESET}")
                
                continue
            
            # 未识别的命令
            print(f"{Color.RED}未识别的命令: {command}{Color.RESET}")
            print(f"{Color.YELLOW}输入 '/help' 查看可用命令{Color.RESET}")
            
    except KeyboardInterrupt:
        print(f"{Color.YELLOW}\n返回聊天模式...{Color.RESET}")
        vivo_speech.disconnect()
        return
    finally:
        # 确保断开连接
        vivo_speech.disconnect()

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 检查是否直接进入绘画模式
    if args.draw:
        run_drawing_mode(args)
    
    # 检查是否直接进入图片分析模式
    if args.vision:
        run_vision_mode(args)
    
    # 检查是否直接进入语音识别模式
    if args.speech:
        run_speech_mode(args)
    
    # 初始化API客户端
    vivo_gpt = VivoGPT(args.app_id, args.app_key)
    vivo_gpt.set_debug_mode(args.debug)
    
    # 初始化绘画API客户端
    vivo_art = VivoArtAPI(args.app_id, args.app_key)
    vivo_art.set_debug_mode(args.debug)
    
    # 初始化图片分析API客户端
    vivo_vision = VivoVisionAPI(args.app_id, args.app_key)
    vivo_vision.set_debug_mode(args.debug)
    
    # 是否使用流式输出
    use_stream = not args.no_stream
    
    # 打印欢迎信息
    print_welcome()
    
    # 保存对话历史
    messages = []
    
    try:
        while True:
            # 获取用户输入
            user_input = input(f"{Color.GREEN}{Color.BOLD}>>> {Color.RESET}")
            
            # 检查退出命令
            if user_input.lower() in ['exit', 'quit']:
                print(f"{Color.YELLOW}感谢使用蓝心大模型聊天助手，再见！{Color.RESET}")
                break
            
            # 检查空输入
            if not user_input.strip():
                continue
            
            # 检查绘画模式切换命令
            if user_input.lower() in ['draw', '/draw']:
                print(f"{Color.CYAN}切换到绘画模式...{Color.RESET}")
                run_drawing_mode(args)
                print(f"{Color.CYAN}返回聊天模式...{Color.RESET}")
                continue
            
            # 检查图片分析模式切换命令
            if user_input.lower() in ['vision', '/vision']:
                print(f"{Color.CYAN}切换到图片分析模式...{Color.RESET}")
                run_vision_mode(args)
                print(f"{Color.CYAN}返回聊天模式...{Color.RESET}")
                continue
            
            # 检查语音识别模式切换命令
            if user_input.lower() in ['speech', '/speech']:
                print(f"{Color.CYAN}切换到语音识别模式...{Color.RESET}")
                run_speech_mode(args)
                print(f"{Color.CYAN}返回聊天模式...{Color.RESET}")
                continue
            
            # 处理绘图命令，直接在聊天模式执行
            if user_input.lower().startswith("/draw "):
                prompt, params = parse_draw_command(user_input)
                
                if prompt:
                    print(f"{Color.CYAN}执行绘图命令: {prompt}{Color.RESET}")
                    
                    # 使用默认参数
                    style = params.get('style', DEFAULT_DRAWING_SETTINGS['style_id'])
                    width = int(params.get('width', DEFAULT_DRAWING_SETTINGS['width']))
                    height = int(params.get('height', DEFAULT_DRAWING_SETTINGS['height']))
                    cfg_scale = float(params.get('cfg', DEFAULT_DRAWING_SETTINGS['cfg_scale']))
                    steps = int(params.get('steps', DEFAULT_DRAWING_SETTINGS['steps']))
                    
                    # 提交绘画任务
                    print(f"{Color.CYAN}正在提交绘画任务...{Color.RESET}")
                    
                    # 显示绘画动画
                    print_drawing_animation(3)
                    
                    response = vivo_art.submit_drawing_task(
                        prompt=prompt,
                        style_config=style,
                        height=height,
                        width=width,
                        cfg_scale=cfg_scale,
                        steps=steps
                    )
                    
                    # 打印任务提交结果
                    task_id = print_task_submitted(response)
                    
                    if task_id:
                        # 询问是否等待结果
                        print(f"{Color.YELLOW}是否等待绘画结果? (y/n){Color.RESET}")
                        if input().lower() == 'y':
                            print(f"{Color.CYAN}等待绘画完成，可能需要一些时间...{Color.RESET}")
                            
                            # 每5秒查询一次进度
                            wait_time = 0
                            while wait_time < 300:  # 最多等待5分钟
                                progress_response = vivo_art.query_task_progress(task_id)
                                finished, image_urls = print_task_progress(progress_response)
                                
                                if finished:
                                    # 下载图片
                                    print(f"\n{Color.CYAN}正在下载图片...{Color.RESET}")
                                    for i, url in enumerate(image_urls):
                                        output_dir = DEFAULT_DRAWING_SETTINGS['output_dir']
                                        if not os.path.exists(output_dir):
                                            os.makedirs(output_dir)
                                        
                                        filepath = vivo_art.download_image(
                                            url, 
                                            output_dir, 
                                            f"drawing_{task_id}_{i}.jpg"
                                        )
                                        print_image_saved(filepath)
                                    break
                                
                                # 显示等待动画
                                print_drawing_animation(5)
                                wait_time += 5
                            
                            if wait_time >= 300:
                                print(f"{Color.YELLOW}等待超时，请稍后使用 '/draw status {task_id}' 查询任务状态{Color.RESET}")
                    
                    continue
            
            # 处理图片分析命令，直接在聊天模式执行
            if user_input.lower().startswith("/analyze "):
                image_path, prompt = parse_analyze_command(user_input)
                
                if image_path:
                    # 检查文件是否存在
                    if not print_image_info(image_path):
                        continue
                    
                    print(f"{Color.CYAN}执行图片分析命令: {prompt}{Color.RESET}")
                    
                    # 显示分析动画
                    print_analyzing_animation(3)
                    
                    # 使用同步方式分析图片
                    try:
                        result = vivo_vision.analyze_image_sync(image_path, prompt)
                        print_analysis_result(result)
                    except Exception as e:
                        print(f"{Color.RED}图片分析失败: {str(e)}{Color.RESET}")
                    
                    continue
            
            # 处理语音识别命令，直接在聊天模式执行
            if user_input.lower().startswith("/record"):
                duration = parse_record_command(user_input)
                
                if duration is not None:
                    print(f"{Color.CYAN}执行语音识别命令: 录音{duration}秒并识别{Color.RESET}")
                    
                    # 初始化语音识别API
                    vivo_speech = VivoSpeechAPI(args.app_id, args.app_key)
                    vivo_speech.set_debug_mode(args.debug)
                    
                    # 连接服务
                    if vivo_speech.connect():
                        # 显示录音动画
                        print_recording_animation(duration)
                        
                        # 录音并识别
                        result = vivo_speech.record_and_recognize(
                            duration=duration,
                            sample_rate=DEFAULT_SPEECH_SETTINGS['sample_rate'],
                            chunk_size=DEFAULT_SPEECH_SETTINGS['chunk_size']
                        )
                        
                        # 显示识别结果
                        print_speech_result(result)
                        
                        # 断开连接
                        vivo_speech.disconnect()
                    else:
                        print(f"{Color.RED}无法连接到语音识别服务{Color.RESET}")
                    
                    continue
            
            # 打印用户消息
            print_user_message(user_input)
            
            # 添加到对话历史
            messages.append({"role": "user", "content": user_input})
            
            # 处理单轮还是多轮对话
            try:
                print_thinking()
                
                if len(messages) > 1:
                    # 多轮对话
                    if use_stream:
                        # 流式输出
                        response = vivo_gpt.chat_with_history(messages, args.temperature, args.max_tokens, stream=True)
                        chunks = process_stream_response(response)
                        ai_reply = print_streaming_ai_message(chunks)
                        messages.append({"role": "assistant", "content": ai_reply})
                    else:
                        # 同步输出
                        response = vivo_gpt.chat_with_history(messages, args.temperature, args.max_tokens)
                        if response.get('code') == 0 and response.get('data'):
                            ai_reply = response['data']['content']
                            print_ai_message(ai_reply)
                            messages.append({"role": "assistant", "content": ai_reply})
                        else:
                            print(f"{Color.RED}错误：{json.dumps(response, ensure_ascii=False)}{Color.RESET}")
                else:
                    # 单轮对话
                    if use_stream:
                        # 流式输出
                        response = vivo_gpt.chat(user_input, args.temperature, args.max_tokens, stream=True)
                        chunks = process_stream_response(response)
                        ai_reply = print_streaming_ai_message(chunks)
                        messages.append({"role": "assistant", "content": ai_reply})
                    else:
                        # 同步输出
                        response = vivo_gpt.chat(user_input, args.temperature, args.max_tokens)
                        if response.get('code') == 0 and response.get('data'):
                            ai_reply = response['data']['content']
                            print_ai_message(ai_reply)
                            messages.append({"role": "assistant", "content": ai_reply})
                        else:
                            print(f"{Color.RED}错误：{json.dumps(response, ensure_ascii=False)}{Color.RESET}")
                
            except KeyboardInterrupt:
                print(f"{Color.YELLOW}\n中断当前生成{Color.RESET}")
                continue
            except Exception as e:
                print(f"{Color.RED}发生错误：{str(e)}{Color.RESET}")
                continue
    
    except KeyboardInterrupt:
        print(f"{Color.YELLOW}\n感谢使用蓝心大模型聊天助手，再见！{Color.RESET}")

if __name__ == "__main__":
    main() 