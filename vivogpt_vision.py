#!/usr/bin/env python
# encoding: utf-8

import requests
import json
import uuid
import time
import os
import base64
from auth_utils import gen_sign_headers, gen_canonical_query_string

class VivoVisionAPI:
    """蓝心大模型图片分析API客户端"""
    
    def __init__(self, app_id, app_key):
        """初始化API客户端
        
        Args:
            app_id: 应用ID
            app_key: 应用密钥
        """
        self.app_id = app_id
        self.app_key = app_key
        self.base_url = "https://api-ai.vivo.com.cn"
        self.debug_mode = False
        self.model = "BlueLM-Vision-prd"  # 默认模型
    
    def set_debug_mode(self, mode):
        """设置调试模式"""
        self.debug_mode = mode
    
    def set_model(self, model):
        """设置使用的模型
        
        Args:
            model: 模型名称，可选 "BlueLM-Vision-prd" 或 "vivo-BlueLM-V-2.0"
        """
        if model in ["BlueLM-Vision-prd", "vivo-BlueLM-V-2.0"]:
            self.model = model
        else:
            print(f"不支持的模型: {model}，使用默认模型 BlueLM-Vision-prd")
    
    def analyze_image(self, image_path, prompt, stream=False):
        """分析图片
        
        Args:
            image_path: 图片路径
            prompt: 分析提示，例如"描述图片的内容"
            stream: 是否使用流式输出
            
        Returns:
            分析结果响应
        """
        # 读取并编码图片
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # 生成请求ID和会话ID
        request_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        # 构建消息内容
        messages = [
            {
                "role": "user",
                "content": f"data:image/JPEG;base64,{image_base64}",
                "contentType": "image"
            },
            {
                "role": "user",
                "content": prompt,
                "contentType": "text"
            }
        ]
        
        # 构建请求数据
        data = {
            "requestId": request_id,
            "sessionId": session_id,
            "model": self.model,
            "messages": messages
        }
        
        # 请求参数
        query = {
            "requestId": request_id
        }
        
        # 确定URI
        if stream:
            uri = "/vivogpt/completions/stream"
        else:
            uri = "/vivogpt/completions"
        
        # 构建URL
        url = f"{self.base_url}{uri}"
        url_with_params = f"{url}?{gen_canonical_query_string(query)}"
        
        # 生成请求头
        headers = gen_sign_headers(self.app_id, self.app_key, "POST", uri, query)
        headers["Content-Type"] = "application/json"
        
        # 调试输出
        if self.debug_mode:
            print("\n调试信息 - 图片分析请求:")
            print(f"请求URL: {url_with_params}")
            print(f"请求头: {json.dumps(headers, ensure_ascii=False, indent=2)}")
            print(f"模型: {self.model}")
            print(f"流式输出: {stream}")
            print(f"请求ID: {request_id}")
            print(f"会话ID: {session_id}")
        
        # 发送请求
        start_time = time.time()
        
        if stream:
            return self._process_stream_request(url_with_params, headers, data, start_time)
        else:
            return self._process_sync_request(url_with_params, headers, data, start_time)
    
    def _process_sync_request(self, url, headers, data, start_time):
        """处理同步请求
        
        Args:
            url: 请求URL
            headers: 请求头
            data: 请求数据
            start_time: 开始时间
            
        Returns:
            (response_data, time_cost) 元组
        """
        response = requests.post(url, headers=headers, json=data)
        end_time = time.time()
        time_cost = end_time - start_time
        
        if self.debug_mode:
            print(f"请求耗时: {time_cost:.2f}秒")
        
        if response.status_code == 200:
            return response.json(), time_cost
        else:
            error_msg = {
                "code": response.status_code,
                "msg": response.text
            }
            return error_msg, time_cost
    
    def _process_stream_request(self, url, headers, data, start_time):
        """处理流式请求
        
        Args:
            url: 请求URL
            headers: 请求头
            data: 请求数据
            start_time: 开始时间
            
        Returns:
            生成器，产生流式响应的消息
        """
        response = requests.post(url, headers=headers, json=data, stream=True)
        
        if response.status_code != 200:
            error_msg = {
                "code": response.status_code,
                "msg": response.text
            }
            yield error_msg
            return
        
        first_chunk = True
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8', errors='ignore')
                
                if first_chunk:
                    first_chunk = False
                    first_time = time.time()
                    first_time_cost = first_time - start_time
                    
                    if self.debug_mode:
                        print(f"首个响应耗时: {first_time_cost:.2f}秒")
                
                # 处理事件行
                if line_text.startswith("event:"):
                    event_type = line_text.replace("event:", "").strip()
                    yield {"event": event_type}
                
                # 处理数据行
                elif line_text.startswith("data:"):
                    data_text = line_text.replace("data:", "").strip()
                    
                    if data_text == "[DONE]":
                        end_time = time.time()
                        time_cost = end_time - start_time
                        
                        if self.debug_mode:
                            print(f"总请求耗时: {time_cost:.2f}秒")
                        
                        yield {"done": True, "time_cost": time_cost}
                    else:
                        try:
                            data_json = json.loads(data_text)
                            yield {"data": data_json}
                        except json.JSONDecodeError:
                            yield {"error": "JSON解析错误", "raw": data_text}
    
    def analyze_image_sync(self, image_path, prompt):
        """同步方式分析图片
        
        Args:
            image_path: 图片路径
            prompt: 分析提示，例如"描述图片的内容"
            
        Returns:
            分析结果文本
        """
        response, _ = self.analyze_image(image_path, prompt, stream=False)
        
        if response.get("code") == 0 and "data" in response:
            return response["data"].get("content", "")
        else:
            error_msg = response.get("msg", "未知错误")
            return f"图片分析失败: {error_msg}"
    
    def analyze_image_stream(self, image_path, prompt):
        """流式方式分析图片
        
        Args:
            image_path: 图片路径
            prompt: 分析提示，例如"描述图片的内容"
            
        Returns:
            生成器，产生分析结果的片段
        """
        for chunk in self.analyze_image(image_path, prompt, stream=True):
            if "data" in chunk and "message" in chunk["data"]:
                yield chunk["data"]["message"]
            elif "done" in chunk:
                break
            elif "event" in chunk and chunk["event"] in ["error", "antispam"]:
                yield "\n[分析中断]"
                break 