#!/usr/bin/env python
# encoding: utf-8

import requests
import json
import uuid
from auth_utils import gen_sign_headers, gen_canonical_query_string

class VivoGPT:
    """蓝心大模型API客户端"""
    
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
    
    def set_debug_mode(self, mode):
        """设置调试模式"""
        self.debug_mode = mode
    
    def chat(self, prompt, temperature=0.7, max_tokens=2048, stream=False):
        """同步调用蓝心大模型API
        
        Args:
            prompt: 提问内容
            temperature: 温度参数，控制输出的随机性
            max_tokens: 生成答案的最大长度
            stream: 是否使用流式接口
            
        Returns:
            同步调用返回完整响应，流式调用返回响应对象
        """
        # 生成请求ID和会话ID
        request_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        # 确定接口URI
        uri = "/vivogpt/completions/stream" if stream else "/vivogpt/completions"
        url = f"{self.base_url}{uri}"
        
        # 构建URL参数
        query = {"requestId": request_id}
        url_with_params = f"{url}?{gen_canonical_query_string(query)}"
        
        # 生成请求头
        headers = gen_sign_headers(self.app_id, self.app_key, "POST", uri, query)
        headers["Content-Type"] = "application/json"
        
        # 构建请求体
        data = {
            "model": "vivo-BlueLM-TB-Pro",
            "prompt": prompt,
            "sessionId": session_id,
            "extra": {
                "temperature": temperature,
                "max_new_tokens": max_tokens
            }
        }
        
        # 打印请求详情
        if self.debug_mode:
            print("\n调试信息:")
            print(f"请求URL: {url_with_params}")
            print(f"请求头: {json.dumps(headers, ensure_ascii=False, indent=2)}")
            print(f"请求体: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        # 发送请求
        if stream:
            response = requests.post(url_with_params, headers=headers, json=data, stream=True)
            return response
        else:
            response = requests.post(url_with_params, headers=headers, json=data)
            return response.json()
    
    def chat_with_history(self, messages, temperature=0.7, max_tokens=2048, stream=False):
        """使用多轮对话历史调用蓝心大模型API
        
        Args:
            messages: 消息历史列表，格式为[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
            temperature: 温度参数，控制输出的随机性
            max_tokens: 生成答案的最大长度
            stream: 是否使用流式接口
            
        Returns:
            同步调用返回完整响应，流式调用返回响应对象
        """
        # 生成请求ID和会话ID
        request_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        # 确定接口URI
        uri = "/vivogpt/completions/stream" if stream else "/vivogpt/completions"
        url = f"{self.base_url}{uri}"
        
        # 构建URL参数
        query = {"requestId": request_id}
        url_with_params = f"{url}?{gen_canonical_query_string(query)}"
        
        # 生成请求头
        headers = gen_sign_headers(self.app_id, self.app_key, "POST", uri, query)
        headers["Content-Type"] = "application/json"
        
        # 构建请求体
        data = {
            "model": "vivo-BlueLM-TB-Pro",
            "messages": messages,
            "sessionId": session_id,
            "extra": {
                "temperature": temperature,
                "max_new_tokens": max_tokens
            }
        }
        
        # 打印请求详情
        if self.debug_mode:
            print("\n调试信息:")
            print(f"请求URL: {url_with_params}")
            print(f"请求头: {json.dumps(headers, ensure_ascii=False, indent=2)}")
            print(f"请求体: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        # 发送请求
        if stream:
            response = requests.post(url_with_params, headers=headers, json=data, stream=True)
            return response
        else:
            response = requests.post(url_with_params, headers=headers, json=data)
            return response.json()

# 流式响应处理函数
def process_stream_response(response):
    """处理流式响应数据
    
    Args:
        response: 流式响应对象
        
    Returns:
        生成的完整内容字符串
    """
    if response.status_code == 200:
        full_content = ""
        chunks = []
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith('data:'):
                    try:
                        data_text = line_text[5:].strip()
                        if data_text != '[DONE]':
                            data_json = json.loads(data_text)
                            if 'message' in data_json:
                                full_content += data_json['message']
                                chunks.append(data_json['message'])
                            elif 'reply' in data_json:
                                full_content += data_json['reply']
                                chunks.append(data_json['reply'])
                    except json.JSONDecodeError:
                        if '[DONE]' not in line_text:
                            print(f"解析JSON失败: {line_text}")
                elif line_text.startswith('event:'):
                    event_type = line_text[6:].strip()
                    if event_type == 'error':
                        print("发生错误")
                    elif event_type == 'close':
                        pass  # 不打印响应完成消息
        return chunks
    else:
        print(f"请求失败，状态码: {response.status_code}")
        print(response.text)
        return [] 