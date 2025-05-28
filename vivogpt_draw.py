#!/usr/bin/env python
# encoding: utf-8

import requests
import json
import uuid
import time
import os
from auth_utils import gen_sign_headers, gen_canonical_query_string

class VivoArtAPI:
    """蓝心大模型绘画API客户端"""
    
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
        
        # 默认绘画参数
        self.default_style_config = "4cbc9165bc615ea0815301116e7925a3"  # 通用v6.0
        self.default_height = 1024
        self.default_width = 1024
        self.default_cfg_scale = 7
        self.default_steps = 20
    
    def set_debug_mode(self, mode):
        """设置调试模式"""
        self.debug_mode = mode
    
    def get_styles(self):
        """获取可用风格列表
        
        Returns:
            风格列表响应
        """
        # 生成请求ID
        data_id = str(uuid.uuid4())
        
        # 接口URI和参数
        uri = "/api/v1/styles"
        query = {
            "businessCode": "pc",
            "dataId": data_id,
            "styleType": "txt2img"
        }
        
        # 构建URL
        url = f"{self.base_url}{uri}"
        url_with_params = f"{url}?{gen_canonical_query_string(query)}"
        
        # 生成请求头
        headers = gen_sign_headers(self.app_id, self.app_key, "GET", uri, query)
        
        # 调试输出
        if self.debug_mode:
            print("\n调试信息 - 请求风格列表:")
            print(f"请求URL: {url_with_params}")
            print(f"请求头: {json.dumps(headers, ensure_ascii=False, indent=2)}")
        
        # 发送请求
        response = requests.get(url_with_params, headers=headers)
        return response.json()
    
    def get_prompts(self):
        """获取文生图推荐词列表
        
        Returns:
            推荐词列表响应
        """
        # 生成请求ID
        data_id = str(uuid.uuid4())
        
        # 接口URI和参数
        uri = "/api/v1/prompts"
        query = {
            "businessCode": "pc",
            "dataId": data_id
        }
        
        # 构建URL
        url = f"{self.base_url}{uri}"
        url_with_params = f"{url}?{gen_canonical_query_string(query)}"
        
        # 生成请求头
        headers = gen_sign_headers(self.app_id, self.app_key, "GET", uri, query)
        
        # 调试输出
        if self.debug_mode:
            print("\n调试信息 - 请求推荐词列表:")
            print(f"请求URL: {url_with_params}")
            print(f"请求头: {json.dumps(headers, ensure_ascii=False, indent=2)}")
        
        # 发送请求
        response = requests.get(url_with_params, headers=headers)
        return response.json()
    
    def submit_drawing_task(self, prompt, style_config=None, height=None, width=None, 
                          init_image=None, image_type=0, seed=-1, cfg_scale=None, 
                          denoising_strength=0.1, ctrl_net_strength=0.5, steps=None, 
                          negative_prompt=""):
        """提交绘画任务
        
        Args:
            prompt: 图像描述
            style_config: 风格模板ID
            height: 图像高度
            width: 图像宽度
            init_image: 初始图像，用于图生图
            image_type: 初始图像类型，0=base64，1=URL
            seed: 随机种子
            cfg_scale: 文本相关度
            denoising_strength: 图片相关度
            ctrl_net_strength: 控制强度
            steps: 采样步数
            negative_prompt: 反向关键词
            
        Returns:
            提交任务的响应
        """
        # 使用默认值
        style_config = style_config or self.default_style_config
        height = height or self.default_height
        width = width or self.default_width
        cfg_scale = cfg_scale or self.default_cfg_scale
        steps = steps or self.default_steps
        
        # 生成请求ID
        data_id = str(uuid.uuid4())
        
        # 接口URI
        uri = "/api/v1/task_submit"
        url = f"{self.base_url}{uri}"
        
        # 构建请求体
        data = {
            "dataId": data_id,
            "businessCode": "pc",
            "userAccount": "",
            "prompt": prompt,
            "styleConfig": style_config,
            "height": height,
            "width": width,
            "seed": seed,
            "cfgScale": cfg_scale,
            "steps": steps,
            "negativePrompt": negative_prompt
        }
        
        # 如果有初始图像，添加到请求中
        if init_image:
            data["initImages"] = init_image
            data["imageType"] = image_type
            data["denoisingStrength"] = denoising_strength
            data["ctrlNetStrength"] = ctrl_net_strength
        
        # 生成请求头
        headers = gen_sign_headers(self.app_id, self.app_key, "POST", uri, {})
        headers["Content-Type"] = "application/json"
        
        # 调试输出
        if self.debug_mode:
            print("\n调试信息 - 提交绘画任务:")
            print(f"请求URL: {url}")
            print(f"请求头: {json.dumps(headers, ensure_ascii=False, indent=2)}")
            print(f"请求体: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        # 发送请求
        response = requests.post(url, headers=headers, json=data)
        return response.json()
        
    def query_task_progress(self, task_id):
        """查询绘画任务进度
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务进度响应
        """
        # 接口URI和参数
        uri = "/api/v1/task_progress"
        query = {
            "task_id": task_id
        }
        
        # 构建URL
        url = f"{self.base_url}{uri}"
        url_with_params = f"{url}?{gen_canonical_query_string(query)}"
        
        # 生成请求头
        headers = gen_sign_headers(self.app_id, self.app_key, "GET", uri, query)
        
        # 调试输出
        if self.debug_mode:
            print("\n调试信息 - 查询任务进度:")
            print(f"请求URL: {url_with_params}")
            print(f"请求头: {json.dumps(headers, ensure_ascii=False, indent=2)}")
        
        # 发送请求
        response = requests.get(url_with_params, headers=headers)
        return response.json()
    
    def cancel_task(self, task_id):
        """取消绘画任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            取消任务的响应
        """
        # 生成请求ID
        data_id = str(uuid.uuid4())
        
        # 接口URI
        uri = "/api/v1/task_cancel"
        url = f"{self.base_url}{uri}"
        
        # 构建请求体
        data = {
            "dataId": data_id,
            "businessCode": "pc",
            "task_id": task_id
        }
        
        # 生成请求头
        headers = gen_sign_headers(self.app_id, self.app_key, "POST", uri, {})
        headers["Content-Type"] = "application/json"
        
        # 调试输出
        if self.debug_mode:
            print("\n调试信息 - 取消绘画任务:")
            print(f"请求URL: {url}")
            print(f"请求头: {json.dumps(headers, ensure_ascii=False, indent=2)}")
            print(f"请求体: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        # 发送请求
        response = requests.post(url, headers=headers, json=data)
        return response.json()
    
    def submit_and_wait(self, prompt, style_config=None, height=None, width=None, 
                       init_image=None, image_type=0, seed=-1, cfg_scale=None,
                       denoising_strength=0.1, ctrl_net_strength=0.5, steps=None, 
                       negative_prompt="", max_wait_time=600, poll_interval=5):
        """提交绘画任务并等待结果
        
        Args:
            prompt: 图像描述
            style_config: 风格模板ID
            height: 图像高度
            width: 图像宽度
            init_image: 初始图像，用于图生图
            image_type: 初始图像类型，0=base64，1=URL
            seed: 随机种子
            cfg_scale: 文本相关度
            denoising_strength: 图片相关度
            ctrl_net_strength: 控制强度
            steps: 采样步数
            negative_prompt: 反向关键词
            max_wait_time: 最大等待时间(秒)
            poll_interval: 轮询间隔(秒)
            
        Returns:
            (finished, result) 元组，finished为是否成功完成，result为任务结果
        """
        # 提交任务
        response = self.submit_drawing_task(
            prompt, style_config, height, width, init_image, image_type,
            seed, cfg_scale, denoising_strength, ctrl_net_strength, steps, negative_prompt
        )
        
        if response.get("code") != 200:
            return False, response
        
        # 获取任务ID
        task_id = response["result"]["task_id"]
        
        # 轮询任务状态
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            # 查询任务进度
            progress = self.query_task_progress(task_id)
            
            if progress.get("code") != 200:
                return False, progress
            
            # 任务完成
            if progress["result"].get("finished") and progress["result"].get("status") == 2:
                return True, progress
            
            # 任务失败
            if progress["result"].get("status") == 3:
                return False, progress
            
            time.sleep(poll_interval)
        
        # 超时
        return False, {"code": "TIMEOUT", "msg": "任务等待超时"}
    
    def download_image(self, image_url, output_dir="./images", filename=None):
        """下载生成的图像
        
        Args:
            image_url: 图像URL
            output_dir: 输出目录
            filename: 文件名，如果未提供则从URL中提取
        
        Returns:
            保存的文件路径
        """
        # 创建输出目录
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 如果未提供文件名，从URL中提取
        if filename is None:
            filename = os.path.basename(image_url)
        
        # 构建完整的文件路径
        filepath = os.path.join(output_dir, filename)
        
        # 下载文件
        response = requests.get(image_url, stream=True)
        if response.status_code != 200:
            return None
        
        # 保存文件
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return filepath 