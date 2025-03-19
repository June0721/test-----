"""
视频下载核心逻辑
合并了403错误处理和Range请求优化
"""
import os
import time
import threading
import random
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional, Callable
import requests
import tempfile
import subprocess

from config import BILIBILI_API, DEFAULT_CONFIG, load_user_config, QUALITY_MAP
from utils import ensure_dir, format_file_name, extract_video_id

class VideoDownloader:
    def __init__(self, progress_callback: Optional[Callable] = None):
        """初始化下载器"""
        self.session = requests.Session()
        self.setup_session()
        self.progress_callback = progress_callback
        self.is_downloading = False
        self.current_progress = 0
        self.total_size = 0
        self._download_lock = threading.Lock()
        self.cancellation_event = threading.Event()

    def setup_session(self):
        """设置会话头和cookies，模拟浏览器行为"""
        # 可选的User-Agent列表
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ]

        # 设置基本请求头
        self.session.headers.update({
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': 'https://www.bilibili.com',
            'Referer': 'https://www.bilibili.com',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'Connection': 'keep-alive'
        })

        # 随机选择一个User-Agent
        self._refresh_headers()

        # 加载cookies
        user_config = load_user_config()
        cookies = {
            'SESSDATA': user_config.get('sessdata', ''),
            'bili_jct': user_config.get('bili_jct', ''),
            'buvid3': user_config.get('buvid3', ''),
            # 防盗链cookies
            'buvid_fp': '45f95911b287556b17a766d625fbd571',
            'b_nut': '1715147201',
            'CURRENT_FNVAL': '4048',
            'CURRENT_QUALITY': '120',
            'innersign': '0'
        }

        # 更新会话cookies
        for key, value in cookies.items():
            if value:  # 只设置非空值
                self.session.cookies.set(key, value)

    def _refresh_headers(self, url: str = None):
        """刷新请求头，更强的浏览器模拟"""
        # 原始视频页面URL，用于referer
        video_id = None
        if url and '/video/' in url:
            video_id = url.split('/video/')[-1].split('?')[0].split('/')[0]
        
        referer = f"https://www.bilibili.com/video/{video_id}" if video_id else "https://www.bilibili.com"
        
        # 增强请求头，更好地模拟真实浏览器
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Referer': referer,
            'Origin': 'https://www.bilibili.com',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors', 
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Range': 'bytes=0-',  # 默认请求完整文件
        }
        
        # 添加自定义请求ID和时间戳
        headers['X-Request-Id'] = ''.join(random.choices('0123456789abcdef', k=16))
        headers['X-Client-Timestamp'] = str(int(time.time()))
        
        self.session.headers.update(headers)
        
        # 刷新cookie中的时间戳
        timestamp = str(int(time.time()))
        self.session.cookies.set("_ts", timestamp)
        self.session.cookies.set("buvid_fp_plain", timestamp)

    def download_video(self, url: str, save_dir: str = None, quality: str = "superhigh") -> Dict:
        """下载视频"""
        if save_dir is None:
            save_dir = DEFAULT_CONFIG["download_dir"]

        self.is_downloading = True
        self.current_progress = 0
        self.total_size = 0
        self.cancellation_event.clear()

        try:
            # 提取视频ID
            video_id = extract_video_id(url)
            if not video_id:
                raise ValueError("无法从URL中提取视频ID")

            # 1. 获取视频信息
            print(f"正在获取视频信息: {video_id}")
            video_info = self._get_video_info(video_id)
            title = format_file_name(video_info["title"])
            cid = video_info["cid"]

            # 处理分p情况
            if "p=" in url:
                try:
                    page = int(url.split("p=")[1].split("&")[0])
                    pages = video_info.get("pages", [])
                    if pages and 1 <= page <= len(pages):
                        cid = pages[page-1]["cid"]
                        title += f"_P{page}_{format_file_name(pages[page-1].get('part', ''))}"
                except Exception as e:
                    print(f"处理分P失败: {e}，使用默认CID")

            # 确保下载目录存在
            ensure_dir(save_dir)
            output_file = os.path.join(save_dir, f"{title}.mp4")

            # 2. 获取视频流 - 修复这里的返回值处理
            print(f"正在获取视频流，画质选择: {quality}")
            try:
                # 兼容两种返回格式
                result = self._get_video_stream(video_id, cid, quality)
                if isinstance(result, tuple) and len(result) == 2:
                    stream_info, degradation_info = result
                else:
                    stream_info = result
                    degradation_info = self._get_degradation_info(stream_info) if stream_info["quality_requested"] != stream_info["quality_actual"] else None
            except ValueError as e:
                raise e

            # 3. 下载视频
            print("开始下载视频...")
            if stream_info.get("is_dash", True):
                self._download_dash_video(stream_info, output_file)
            else:
                self._download_direct_video(stream_info, output_file)

            # 4. 返回结果
            return {
                "title": video_info["title"],
                "bvid": video_id,
                "quality": quality,
                "actual_quality": self._quality_code_to_name(stream_info["quality_actual"]),
                "download_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "save_path": output_file,
                "degradation_info": degradation_info
            }

        except Exception as e:
            raise ValueError(f"下载失败: {str(e)}")

        finally:
            self.is_downloading = False

    def _get_video_info(self, video_id: str) -> Dict:
        """获取视频信息"""
        params = {"bvid": video_id} if video_id.startswith("BV") else {"aid": video_id[2:]}

        # 发送请求前刷新headers
        self._refresh_headers()

        response = self.session.get(
            BILIBILI_API["video_info"],
            params=params,
            timeout=20
        )
        response.raise_for_status()
        data = response.json()

        if data.get("code", -1) != 0:
            error_msg = data.get('message', '未知错误')
            if "请登录" in error_msg:
                raise ValueError("需要登录才能获取视频信息，请先登录")
            raise ValueError(f"获取视频信息失败: {error_msg}")

        video_data = data.get("data", {})
        return {
            "title": video_data.get("title", "未知标题"),
            "bvid": video_data.get("bvid"),
            "aid": video_data.get("aid"),
            "cid": video_data.get("cid"),
            "desc": video_data.get("desc", ""),
            "duration": video_data.get("duration", 0),
            "pages": video_data.get("pages", [])
        }

    def _get_video_stream(self, video_id: str, cid: int, quality: str = "high") -> tuple:
        """
        获取视频流信息
        
        Returns:
            tuple: (stream_info, degradation_info) - 视频流信息和画质降级信息(如果有)
        """
        quality_map = {
            "ultra": 127,   # 8K
            "superhigh": 120, # 4K
            "high": 116,     # 1080P60
            "medium": 80,    # 1080P
            "low": 64        # 720P
        }
        requested_qn = quality_map.get(quality, 80)

        params = {
            "bvid": video_id if video_id.startswith("BV") else None,
            "aid": video_id[2:] if video_id.startswith("av") else None,
            "cid": cid,
            "qn": requested_qn,
            "fnval": 4048,  # 启用DASH
            "fourk": 1,     # 允许4K
            "fnver": 0
        }
        params = {k: v for k, v in params.items() if v is not None}

        # 刷新请求头
        self._refresh_headers(f"https://www.bilibili.com/video/{video_id}")

        response = self.session.get(
            BILIBILI_API["video_stream"],
            params=params,
            timeout=20
        )
        response.raise_for_status()
        data = response.json()

        if data.get("code", -1) != 0:
            error_message = data.get("message", "未知错误")
            raise ValueError(f"获取视频流失败: {error_message}")

        stream_data = data.get("data", {})
        if not stream_data:
            raise ValueError("返回的视频流数据为空")

        actual_qn = stream_data.get("quality", 0)
        accept_quality = stream_data.get("accept_quality", [])
        accept_description = stream_data.get("accept_description", [])

        stream_info = {
            "quality_requested": requested_qn,
            "quality_actual": actual_qn,
            "quality_list": list(zip(accept_quality, accept_description)),
            "is_dash": "dash" in stream_data
        }

        if stream_info["is_dash"]:
            dash = stream_data["dash"]
            video_streams = dash.get("video", [])
            if not video_streams:
                raise ValueError("未找到可用的视频流")

            # 选择视频流
            selected_video = None
            for stream in sorted(video_streams, key=lambda x: x.get("id", 0), reverse=True):
                if stream.get("id") == actual_qn:
                    selected_video = stream
                    break
            if not selected_video:
                selected_video = video_streams[0]

            # 选择音频流
            audio_streams = dash.get("audio", [])
            selected_audio = None
            if audio_streams:
                selected_audio = sorted(audio_streams, key=lambda x: x.get("id", 0), reverse=True)[0]

            stream_info["video_stream"] = selected_video
            stream_info["audio_stream"] = selected_audio

        elif "durl" in stream_data:
            durls = stream_data.get("durl", [])
            if not durls:
                raise ValueError("未找到可下载链接")
            stream_info["video_url"] = durls[0]["url"]
            stream_info["is_dash"] = False

        else:
            raise ValueError("未找到支持的视频格式")

        return stream_info, self._get_degradation_info(stream_info) if stream_info["quality_requested"] != stream_info["quality_actual"] else None

    def _download_dash_video(self, stream_info: Dict, output_file: str):
        """下载DASH格式视频"""
        video_url = stream_info["video_stream"]["baseUrl"]

        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.m4s', delete=False) as video_tmp:
            video_path = video_tmp.name

        audio_path = None
        if stream_info.get("audio_stream"):
            with tempfile.NamedTemporaryFile(suffix='.m4s', delete=False) as audio_tmp:
                audio_path = audio_tmp.name

        try:
            # 下载视频流
            print("开始下载视频流...")
            self._download_with_retry(
                url=video_url,
                output_path=video_path,
                file_type="video"
            )

            if self.cancellation_event.is_set():
                return

            # 下载音频
            if audio_path and stream_info.get("audio_stream"):
                print("视频下载完成，开始下载音频流...")
                audio_url = stream_info["audio_stream"]["baseUrl"]
                self._download_with_retry(
                    url=audio_url,
                    output_path=audio_path,
                    file_type="audio"
                )

                if self.cancellation_event.is_set():
                    return

                # 合并音视频
                print("开始合并音视频...")
                self._merge_audio_video(video_path, audio_path, output_file)
            else:
                # 无音频，直接重命名视频文件
                import shutil
                shutil.copy2(video_path, output_file)
                print("视频下载完成（无音轨）")

        finally:
            # 清理临时文件
            try:
                if os.path.exists(video_path):
                    os.remove(video_path)
                if audio_path and os.path.exists(audio_path):
                    os.remove(audio_path)
            except Exception as e:
                print(f"清理临时文件失败: {e}")

    def _download_direct_video(self, stream_info: Dict, output_file: str):
        """下载普通格式视频"""
        video_url = stream_info["video_url"]
        self._download_with_retry(
            url=video_url,
            output_path=output_file,
            file_type="video"
        )

    def _download_with_retry(self, url: str, output_path: str, file_type: str = "video"):
        """带重试的下载函数，处理403错误"""
        max_retries = 8  # 增加重试次数
        retry_count = 0
        
        # 扩展CDN备选列表
        cdn_hosts = [
            "upos-hz-mirrorakam.akamaized.net",
            "upos-sz-mirrorali.bilivideo.com",
            "upos-sz-mirrorcos.bilivideo.com", 
            "upos-sz-mirrorali.bilivideo.com",
            "upos-sz-mirroraliov.bilivideo.com",
            "cn-hk-eq-bcache-01.bilivideo.com",
            "upos-cs-upcdnbda.bilivideo.com", 
            "upos-cs-upcdnws.bilivideo.com",
            "upos-sz-upcdnbda.bilivideo.com",
            "cn-sh-fx-bcache-18.bilivideo.com"
        ]
        
        # 添加请求方式选择
        request_modes = ["simple", "range", "browser_sim", "direct"]
        current_mode = 0
        
        while retry_count < max_retries:
            try:
                # 更换CDN或请求模式
                if retry_count > 0:
                    # 每两次失败后切换请求模式
                    if retry_count % 2 == 0:
                        current_mode = (current_mode + 1) % len(request_modes)
                        print(f"切换请求模式: {request_modes[current_mode]}")
                    
                    # 更换CDN
                    current_cdn = url.split('/')[2]
                    other_cdns = [cdn for cdn in cdn_hosts if cdn != current_cdn]
                    if other_cdns:
                        new_cdn = random.choice(other_cdns)
                        url = url.replace(current_cdn, new_cdn)
                        print(f"尝试使用备用CDN: {new_cdn}")
                    
                    # 对于持续失败的情况，添加随机延迟
                    time.sleep(1 + random.random() * 2)
                
                # 根据当前请求模式选择下载方法
                mode = request_modes[current_mode]
                
                if mode == "browser_sim":
                    # 模拟浏览器行为
                    self._simulate_browser_visit()
                    
                # 刷新请求头并确保referer正确指向视频页面
                self._refresh_headers(url)
                
                # 尝试获取文件大小
                try:
                    head_response = self.session.head(url, timeout=15)
                    head_response.raise_for_status()
                    total_size = int(head_response.headers.get('content-length', 0))
                except Exception as e:
                    print(f"获取文件大小失败: {e}, 尝试其他方式")
                    total_size = 0
                
                # 根据不同模式尝试下载
                if total_size > 0 and mode in ["simple", "browser_sim"]:
                    # 使用分块下载
                    self._download_with_chunks(url, output_path, total_size)
                    return
                elif mode == "range":
                    # 使用Range请求模式
                    self._download_with_range(url, output_path)
                    return
                else:
                    # 直接流式下载
                    self._download_stream_mode(url, output_path)
                    return
                    
            except requests.HTTPError as e:
                if e.response.status_code == 403:
                    print(f"403 Forbidden错误，尝试更换CDN节点 ({retry_count+1}/{max_retries})")
                    retry_count += 1
                    continue
                else:
                    print(f"HTTP错误: {e.response.status_code}")
                    retry_count += 1
            except Exception as e:
                print(f"下载出错: {str(e)}")
                retry_count += 1
        
        raise ValueError(f"下载{file_type}失败，已达到最大重试次数")

    def _simulate_browser_visit(self):
        """模拟浏览器行为，先访问B站首页和视频页面再下载"""
        try:
            print("模拟浏览器访问行为...")
            # 访问B站首页
            self.session.get("https://www.bilibili.com/", timeout=10)
            time.sleep(1)
            
            # 访问一个随机B站视频页面
            video_ids = ["BV1xx411c7KC", "BV1vs4y1f7bM", "BV1uT411S7Sb"]
            random_video = random.choice(video_ids)
            self.session.get(f"https://www.bilibili.com/video/{random_video}", timeout=10)
            time.sleep(1)
        except Exception as e:
            print(f"模拟浏览器行为失败: {e}")

    def _download_chunk(self, url: str, start: int, end: int, output_path: str):
        """下载指定范围的数据块"""
        headers = {
            'Range': f'bytes={start}-{end}',
            'Referer': 'https://www.bilibili.com',
            'User-Agent': random.choice(self.user_agents)
        }

        retries = 3
        for i in range(retries):
            try:
                response = self.session.get(url, headers=headers, timeout=30)
                response.raise_for_status()

                with open(output_path, 'r+b') as f:
                    f.seek(start)
                    data = response.content
                    f.write(data)

                # 更新进度
                with self._download_lock:
                    self.current_progress += len(data)
                    if self.progress_callback:
                        self.progress_callback(self.current_progress)

                return
            except Exception as e:
                if i == retries - 1:
                    raise ValueError(f"下载数据块失败: {str(e)}")
                time.sleep(1)

    def _download_stream_mode(self, url: str, output_path: str):
        """流式下载模式"""
        try:
            with self.session.get(url, stream=True, timeout=60) as response:
                response.raise_for_status()

                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if self.cancellation_event.is_set():
                            return
                        if chunk:
                            f.write(chunk)
                            with self._download_lock:
                                self.current_progress += len(chunk)
                                if self.progress_callback:
                                    self.progress_callback(self.current_progress)
        except Exception as e:
            raise ValueError(f"流式下载失败: {str(e)}")

    def _merge_audio_video(self, video_file: str, audio_file: str, output_file: str):
        """合并音频和视频文件"""
        try:
            # 检查ffmpeg
            import shutil
            ffmpeg_path = shutil.which('ffmpeg')
            if not ffmpeg_path:
                raise ValueError("未找到ffmpeg，无法合并音视频")

            # 合并命令
            command = [
                ffmpeg_path,
                '-i', video_file,
                '-i', audio_file,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-strict', 'experimental',
                output_file,
                '-y'  # 覆盖已有文件
            ]

            # 执行命令
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            stdout, stderr = process.communicate()

            if process.returncode != 0:
                print(f"FFmpeg错误: {stderr.decode('utf-8', errors='ignore')}")
                raise ValueError("合并音视频失败")

        except Exception as e:
            raise ValueError(f"合并音视频失败: {str(e)}")

    def _download_with_chunks(self, url: str, output_path: str, total_size: int):
        """使用分块方式下载大文件"""
        # 更新总大小
        self.total_size += total_size

        # 分块大小，默认5MB或文件大小的1/10
        chunk_size = min(5242880, max(1048576, total_size // 10))
        max_workers = min(8, max(2, total_size // (1024 * 1024 * 10)))

        # 创建空文件
        with open(output_path, 'wb') as f:
            f.truncate(total_size)

        # 多线程下载
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for start in range(0, total_size, chunk_size):
                end = min(start + chunk_size - 1, total_size - 1)
                futures.append(executor.submit(
                    self._download_chunk, url, start, end, output_path
                ))

            # 等待所有任务完成
            for future in futures:
                if self.cancellation_event.is_set():
                    return
                future.result()

    def _download_with_range(self, url: str, output_path: str):
        """使用Range请求尝试下载文件"""
        # 先请求1字节确认Range支持并获取文件大小
        headers = {'Range': 'bytes=0-1'}
        response = self.session.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        content_range = response.headers.get('content-range', '')
        total_size = 0
        
        if content_range and '/' in content_range:
            try:
                total_size = int(content_range.split('/')[1])
            except (IndexError, ValueError):
                raise ValueError("无法确定文件大小")
        else:
            raise ValueError("服务器不支持Range请求")
        
        # 更新总大小
        self.total_size += total_size
        print(f"文件总大小: {total_size} 字节")
        
        # 使用多线程分块下载
        self._download_with_chunks(url, output_path, total_size)

    def _quality_code_to_name(self, code: int) -> str:
        """将画质代码转换为名称"""
        return QUALITY_MAP.get(code, f"未知画质({code})")

    def _get_degradation_info(self, stream_info: Dict) -> Dict:
        """生成画质降级信息"""
        requested_name = self._quality_code_to_name(stream_info["quality_requested"])
        actual_name = self._quality_code_to_name(stream_info["quality_actual"])

        return {
            "requested": stream_info["quality_requested"],
            "requested_name": requested_name,
            "current": stream_info["quality_actual"],
            "current_name": actual_name,
            "reason": "该画质需要大会员或视频本身不提供此画质"
        }

    def stop_download(self):
        """停止下载"""
        self.cancellation_event.set()
        self.is_downloading = False