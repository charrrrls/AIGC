#!/usr/bin/env python
# encoding: utf-8

import websocket
import json
import uuid
import time
import os
import threading
import pyaudio
import wave
import base64
import queue
import random
import string
from auth_utils import gen_sign_headers, gen_canonical_query_string
import ssl

class VivoSpeechAPI:
    """蓝心大模型语音识别API客户端"""
    
    def __init__(self, app_id, app_key):
        """初始化API客户端
        
        Args:
            app_id: 应用ID
            app_key: 应用密钥
        """
        self.app_id = app_id
        self.app_key = app_key
        self.base_url = "api-ai.vivo.com.cn"
        self.debug_mode = False
        self.ws = None
        self.is_connected = False
        self.result_queue = queue.Queue()  # 存储识别结果的队列
        self.session_id = None  # WebSocket会话ID
    
    def set_debug_mode(self, mode):
        """设置调试模式"""
        self.debug_mode = mode
    
    def _generate_ws_url(self):
        """生成WebSocket连接URL
        
        Returns:
            完整的WebSocket URL
        """
        # 生成URL参数
        query_params = {
            "client_version": "1.0.0",
            "package": "unknown",
            "sdk_version": "1.0.0",
            "user_id": uuid.uuid4().hex,  # 32位用户ID
            "android_version": "unknown",
            "system_time": str(int(time.time() * 1000)),  # 毫秒级时间戳
            "net_type": "1",  # WiFi
            "engineid": "shortasrinput"  # 短语音通用模型
        }
        
        # 转换为URL查询字符串
        query_string = gen_canonical_query_string(query_params)
        
        # 生成签名
        uri = f"/asr/v2?{query_string}"
        headers = gen_sign_headers(self.app_id, self.app_key, "GET", uri, query_params)
        
        # 构建URL
        url = f"wss://{self.base_url}{uri}"
        
        # 调试输出
        if self.debug_mode:
            print("\n调试信息 - WebSocket URL:")
            print(f"URL: {url}")
            print(f"Headers: {json.dumps(headers, ensure_ascii=False, indent=2)}")
        
        return url, headers
    
    def _on_message(self, ws, message):
        """WebSocket消息回调
        
        Args:
            ws: WebSocket连接
            message: 收到的消息
        """
        if self.debug_mode:
            print(f"\n收到消息: {message}")
        
        try:
            result = json.loads(message)
            
            # 握手成功
            if result.get("action") == "started":
                self.session_id = result.get("sid")
                self.is_connected = True
                if self.debug_mode:
                    print(f"WebSocket连接成功，会话ID: {self.session_id}")
            
            # 识别结果
            elif result.get("action") == "result" and result.get("type") == "asr":
                asr_text = result.get("data", {}).get("text", "")
                is_last = result.get("data", {}).get("is_last", False)
                is_finish = result.get("is_finish", False)
                
                # 将结果放入队列
                self.result_queue.put({
                    "text": asr_text,
                    "is_last": is_last,
                    "is_finish": is_finish
                })
                
                if self.debug_mode:
                    print(f"识别结果: {asr_text}")
                    print(f"是否为最后一条: {is_last}")
                    print(f"是否完成: {is_finish}")
            
            # 错误信息
            elif result.get("action") == "error":
                error_code = result.get("code")
                error_desc = result.get("desc")
                
                if self.debug_mode:
                    print(f"错误: {error_desc} (代码: {error_code})")
                
                # 将错误信息放入队列
                self.result_queue.put({
                    "error": error_desc,
                    "code": error_code
                })
        
        except json.JSONDecodeError:
            if self.debug_mode:
                print(f"无效的JSON响应: {message}")
            
            # 将错误信息放入队列
            self.result_queue.put({
                "error": "无效的JSON响应",
                "raw": message
            })
    
    def _on_error(self, ws, error):
        """WebSocket错误回调
        
        Args:
            ws: WebSocket连接
            error: 错误信息
        """
        if self.debug_mode:
            print(f"\n连接错误: {error}")
        
        # 将错误信息放入队列
        self.result_queue.put({
            "error": f"WebSocket错误: {str(error)}"
        })
    
    def _on_close(self, ws, close_status_code, close_msg):
        """WebSocket关闭回调
        
        Args:
            ws: WebSocket连接
            close_status_code: 关闭状态码
            close_msg: 关闭消息
        """
        if self.debug_mode:
            print(f"\n连接已关闭: 状态码={close_status_code}, 消息={close_msg}")
        
        self.is_connected = False
        
        # 将关闭信息放入队列
        self.result_queue.put({
            "closed": True,
            "code": close_status_code,
            "message": close_msg
        })
    
    def _on_open(self, ws):
        """WebSocket打开回调
        
        Args:
            ws: WebSocket连接
        """
        if self.debug_mode:
            print("\n连接已建立")
        
        # 发送初始化消息
        def send_init():
            # 生成请求ID
            request_id = str(uuid.uuid4())
            
            # 构建初始化消息
            start_message = {
                "type": "started",
                "request_id": request_id,
                "asr_info": {
                    "end_vad_time": 5000,  # 后端检测时间，单位毫秒
                    "audio_type": "pcm",   # 音频类型
                    "chinese2digital": 0,  # 不开启汉字转数字
                    "punctuation": 1       # 开启标点符号
                }
            }
            
            # 发送文本初始化消息
            ws.send(json.dumps(start_message))
            
            if self.debug_mode:
                print(f"已发送初始化消息: {json.dumps(start_message)}")
        
        # 启动线程发送初始化消息
        threading.Thread(target=send_init).start()
    
    def connect(self):
        """创建WebSocket连接
        
        Returns:
            成功连接返回True，否则返回False
        """
        try:
            # 生成WebSocket URL和头信息
            url, headers = self._generate_ws_url()
            
            # 创建WebSocket连接
            websocket.enableTrace(self.debug_mode)
            
            # SSL选项 - 禁用证书验证以解决可能的SSL问题
            ssl_options = {"cert_reqs": ssl.CERT_NONE}
            
            self.ws = websocket.WebSocketApp(
                url,
                header=headers,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            # 启动WebSocket连接线程，传入SSL选项
            self.ws_thread = threading.Thread(
                target=lambda: self.ws.run_forever(sslopt=ssl_options)
            )
            self.ws_thread.daemon = True
            self.ws_thread.start()
            
            # 等待连接建立
            start_time = time.time()
            while not self.is_connected and time.time() - start_time < 15.0:  # 增加等待时间到15秒
                time.sleep(0.1)
                if self.debug_mode and (time.time() - start_time) % 2 < 0.1:
                    print(f"等待连接... {int(time.time() - start_time)}秒")
            
            # 检查是否成功连接
            if not self.is_connected:
                if self.debug_mode:
                    print("连接超时 - 可能原因：")
                    print("1. 网络连接问题")
                    print("2. 应用ID或密钥无效")
                    print("3. 服务器端未响应")
                    print("4. SSL/证书问题")
                return False
            
            return True
        
        except Exception as e:
            if self.debug_mode:
                print(f"创建连接失败: {str(e)}")
                print(f"异常类型: {type(e).__name__}")
                
                # 特别处理SSL错误
                if isinstance(e, ssl.SSLError):
                    print("SSL验证失败，这可能是由于证书问题导致的")
                
                # 特别处理连接错误
                if isinstance(e, ConnectionRefusedError):
                    print("连接被拒绝，服务器可能未运行或不接受连接")
                
            return False
    
    def disconnect(self):
        """断开WebSocket连接"""
        if self.ws and self.is_connected:
            try:
                # 发送关闭命令
                self.ws.send("--close--", websocket.ABNF.OPCODE_BINARY)
                
                # 关闭连接
                self.ws.close()
                
                # 等待线程结束
                if hasattr(self, 'ws_thread') and self.ws_thread.is_alive():
                    self.ws_thread.join(2.0)
                
                if self.debug_mode:
                    print("已断开连接")
                
                return True
            
            except Exception as e:
                if self.debug_mode:
                    print(f"断开连接失败: {str(e)}")
                return False
        
        return True
    
    def send_audio_data(self, audio_data):
        """发送音频数据
        
        Args:
            audio_data: 音频数据，bytes格式
            
        Returns:
            发送成功返回True，否则返回False
        """
        if not self.ws or not self.is_connected:
            if self.debug_mode:
                print("发送失败：未连接")
            return False
        
        try:
            # 发送音频数据
            self.ws.send(audio_data, websocket.ABNF.OPCODE_BINARY)
            return True
        
        except Exception as e:
            if self.debug_mode:
                print(f"发送音频数据失败: {str(e)}")
            return False
    
    def end_audio(self):
        """结束音频发送
        
        Returns:
            发送成功返回True，否则返回False
        """
        if not self.ws or not self.is_connected:
            if self.debug_mode:
                print("发送结束标记失败：未连接")
            return False
        
        try:
            # 发送结束标记
            self.ws.send("--end--", websocket.ABNF.OPCODE_BINARY)
            return True
        
        except Exception as e:
            if self.debug_mode:
                print(f"发送结束标记失败: {str(e)}")
            return False
    
    def get_result(self, timeout=None):
        """获取识别结果
        
        Args:
            timeout: 超时时间，单位秒，None表示一直等待
            
        Returns:
            识别结果字典
        """
        try:
            return self.result_queue.get(block=True, timeout=timeout)
        except queue.Empty:
            return {"error": "获取结果超时"}
    
    def record_and_recognize(self, duration=5, sample_rate=16000, chunk_size=1024):
        """录音并识别
        
        Args:
            duration: 录音时长，单位秒
            sample_rate: 采样率，服务要求16k
            chunk_size: 每次读取的音频数据大小
            
        Returns:
            识别文本，如果失败则返回错误信息
        """
        # 检查是否已连接
        if not self.is_connected and not self.connect():
            return "连接语音识别服务失败"
        
        # 录音并发送
        try:
            # 清空结果队列
            while not self.result_queue.empty():
                self.result_queue.get_nowait()
            
            p = pyaudio.PyAudio()
            
            # 打开音频流
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                input=True,
                frames_per_buffer=chunk_size
            )
            
            print("开始录音...")
            
            # 录音
            frames = []
            for i in range(0, int(sample_rate / chunk_size * duration)):
                data = stream.read(chunk_size)
                frames.append(data)
                
                # 发送音频数据
                self.send_audio_data(data)
            
            print("录音结束，正在处理...")
            
            # 停止录音
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            # 结束音频发送
            self.end_audio()
            
            # 等待识别结果
            result_text = ""
            start_time = time.time()
            
            while time.time() - start_time < 10.0:  # 最多等待10秒
                result = self.get_result(timeout=1.0)
                
                if "text" in result:
                    result_text = result["text"]
                    if result.get("is_last", False) or result.get("is_finish", False):
                        break
                
                if "error" in result:
                    return f"识别出错: {result['error']}"
                
                if "closed" in result:
                    break
            
            return result_text
        
        except Exception as e:
            return f"录音或识别过程出错: {str(e)}"
        finally:
            # 结束音频发送
            self.end_audio()
    
    def recognize_wav_file(self, file_path, chunk_size=1024):
        """识别WAV文件
        
        Args:
            file_path: WAV文件路径
            chunk_size: 每次读取的音频数据大小
            
        Returns:
            识别文本，如果失败则返回错误信息
        """
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return f"文件不存在: {file_path}"
        
        # 检查是否为WAV文件
        if not file_path.lower().endswith(".wav"):
            return f"不支持的文件格式，仅支持WAV: {file_path}"
        
        # 检查是否已连接
        if not self.is_connected and not self.connect():
            return "连接语音识别服务失败"
        
        # 读取并发送WAV文件
        try:
            # 清空结果队列
            while not self.result_queue.empty():
                self.result_queue.get_nowait()
            
            # 读取WAV文件
            wf = wave.open(file_path, 'rb')
            
            # 检查格式
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
                return "音频格式不符合要求，需要16k/16bit单声道PCM格式"
            
            # 发送音频数据
            data = wf.readframes(chunk_size)
            while data:
                self.send_audio_data(data)
                data = wf.readframes(chunk_size)
            
            wf.close()
            
            # 结束音频发送
            self.end_audio()
            
            # 等待识别结果
            result_text = ""
            start_time = time.time()
            
            while time.time() - start_time < 10.0:  # 最多等待10秒
                result = self.get_result(timeout=1.0)
                
                if "text" in result:
                    result_text = result["text"]
                    if result.get("is_last", False) or result.get("is_finish", False):
                        break
                
                if "error" in result:
                    return f"识别出错: {result['error']}"
                
                if "closed" in result:
                    break
            
            return result_text
        
        except Exception as e:
            return f"文件识别过程出错: {str(e)}"
        finally:
            # 结束音频发送
            self.end_audio()
    
    def save_recording(self, output_file, duration=5, sample_rate=16000, chunk_size=1024):
        """录音并保存到WAV文件
        
        Args:
            output_file: 输出文件路径
            duration: 录音时长，单位秒
            sample_rate: 采样率
            chunk_size: 每次读取的音频数据大小
            
        Returns:
            保存成功返回True，否则返回False
        """
        try:
            p = pyaudio.PyAudio()
            
            # 打开音频流
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                input=True,
                frames_per_buffer=chunk_size
            )
            
            print("开始录音...")
            
            # 录音
            frames = []
            for i in range(0, int(sample_rate / chunk_size * duration)):
                data = stream.read(chunk_size)
                frames.append(data)
            
            print("录音结束...")
            
            # 停止录音
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            # 保存WAV文件
            wf = wave.open(output_file, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            return True
        
        except Exception as e:
            if self.debug_mode:
                print(f"录音保存失败: {str(e)}")
            return False 