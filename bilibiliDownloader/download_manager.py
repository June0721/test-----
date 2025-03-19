"""
下载管理器

下载任务状态:
- pending: 等待下载
- downloading: 正在下载
- completed: 下载完成
- failed: 下载失败
- canceled: 下载取消

下载任务包含的信息:
- url: 下载地址
- save_dir: 保存目录
- quality: 视频质量
- task_id: 任务ID
- status: 任务状态
- progress: 下载进度
- result: 下载结果
- error: 错误信息
- downloader: 下载器
- start_time: 开始时间
- end_time: 结束时间

下载管理器功能:
- 添加下载任务
- 取消下载任务
- 获取任务信息
- 获取所有任务
- 设置状态更新回调
- 关闭下载管理器

下载管理器实现:
- 使用队列控制下载任务的执行顺序
- 使用多线程实现并发下载任务
- 使用锁确保线程安全
- 使用状态回调通知任务状态更新
- 创建全局下载管理器实例

下载管理器用途:
- 管理下载任务，实现多任务下载
- 监控下载任务状态，实时更新UI
- 取消下载任务，停止下载任务的执行
- 限制最大并发数，避免同时下载过多任务
- 提供统一接口，方便调用和扩展

下载管理器与缓存管理器的对比:
- 下载管理器: 管理下载任务，实现多任务下载
- 缓存管理器: 管理缓存数据，实现数据存储和读取
- 下载管理器使用队列控制任务执行顺序
- 缓存管理器使用文件存储数据，实现数据持久化
- 下载管理器使用多线程实现并发下载任务
- 缓存管理器使用JSON格式存储数据，实现数据可读性
- 下载管理器使用状态回调通知任务状态更新
- 缓存管理器使用时间戳判断缓存是否过期
- 下载管理器提供统一接口，方便调用和扩展
- 缓存管理器提供get和set方法，实现数据读写操作

下载管理器与下载器工厂的对比:
- 下载管理器: 管理下载任务，实现多任务下载
- 下载器工厂: 创建下载器实例，根据需求选择下载器
- 下载管理器使用队列控制任务执行顺序
- 下载器工厂根据参数创建不同下载器实例
- 下载管理器使用多线程实现并发下载任务
- 下载器工厂根据需求创建适用的下载器实例
- 下载管理器使用状态回调通知任务状态更新
- 下载器工厂根据参数返回指定下载器实例
- 下载管理器提供统一接口，方便调用和扩展
- 下载器工厂使用工
下载管理器，管理多个下载任务
"""
import threading
import queue
import time
from typing import Dict, List, Optional, Callable

from downloader_factory import create_downloader
from logger import logger

class DownloadTask:
    """下载任务"""
    
    def __init__(self, url: str, save_dir: str, quality: str, task_id: str):
        self.url = url
        self.save_dir = save_dir
        self.quality = quality
        self.task_id = task_id
        self.status = "pending"  # pending, downloading, completed, failed, canceled
        self.progress = 0
        self.result = None
        self.error = None
        self.downloader = None
        self.start_time = None
        self.end_time = None
        
    def __str__(self):
        return f"Task {self.task_id}: {self.url} - {self.status} ({self.progress}%)"

class DownloadManager:
    """下载管理器"""
    
    def __init__(self, max_concurrent: int = 2):
        self.tasks = {}  # 所有任务
        self.queue = queue.Queue()  # 等待队列
        self.active_tasks = set()  # 活动任务ID
        self.max_concurrent = max_concurrent
        self.lock = threading.RLock()
        self.workers = []
        self.status_callback = None
        self.is_running = False
        
    def set_status_callback(self, callback: Callable):
        """设置状态更新回调"""
        self.status_callback = callback
        
    def add_task(self, url: str, save_dir: str, quality: str) -> str:
        """添加下载任务"""
        # 生成任务ID
        import uuid
        task_id = str(uuid.uuid4())[:8]
        
        # 创建任务
        task = DownloadTask(url, save_dir, quality, task_id)
        
        with self.lock:
            # 添加到任务字典
            self.tasks[task_id] = task
            # 添加到队列
            self.queue.put(task_id)
            
        logger.info(f"添加下载任务: {task_id} - {url}")
        
        # 确保工作线程在运行
        self._ensure_workers()
        
        return task_id
        
    def cancel_task(self, task_id: str) -> bool:
        """取消下载任务"""
        with self.lock:
            if task_id not in self.tasks:
                return False
                
            task = self.tasks[task_id]
            
            # 如果任务正在下载中，停止下载
            if task.status == "downloading" and task.downloader:
                task.downloader.stop_download()
                self.active_tasks.remove(task_id)
                
            # 更新状态
            task.status = "canceled"
            logger.info(f"取消下载任务: {task_id}")
            
            if self.status_callback:
                self.status_callback(task_id, "canceled", 0)
                
            return True
    
    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        """获取任务信息"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[DownloadTask]:
        """获取所有任务"""
        with self.lock:
            return list(self.tasks.values())
    
    def _ensure_workers(self):
        """确保工作线程在运行"""
        with self.lock:
            if not self.is_running:
                self.is_running = True
                
                # 创建工作线程
                for _ in range(self.max_concurrent):
                    worker = threading.Thread(target=self._worker_loop, daemon=True)
                    worker.start()
                    self.workers.append(worker)
                    
                logger.debug(f"启动{self.max_concurrent}个下载工作线程")
    
    def _worker_loop(self):
        """工作线程循环"""
        while self.is_running:
            try:
                # 获取任务ID
                try:
                    task_id = self.queue.get(timeout=1)
                except queue.Empty:
                    continue
                    
                with self.lock:
                    # 检查是否已达到最大并发数
                    if len(self.active_tasks) >= self.max_concurrent:
                        # 放回队列
                        self.queue.put(task_id)
                        time.sleep(0.5)
                        continue
                        
                    # 检查任务是否存在
                    if task_id not in self.tasks:
                        self.queue.task_done()
                        continue
                        
                    # 获取任务
                    task = self.tasks[task_id]
                    
                    # 检查任务状态
                    if task.status != "pending":
                        self.queue.task_done()
                        continue
                        
                    # 将任务加入活动集合
                    self.active_tasks.add(task_id)
                    
                # 设置任务状态
                task.status = "downloading"
                task.start_time = time.time()
                
                # 通知状态更新
                if self.status_callback:
                    self.status_callback(task_id, "downloading", 0)
                    
                logger.info(f"开始下载任务: {task_id} - {task.url}")
                
                # 创建下载器
                def progress_callback(current_bytes):
                    if task.downloader and hasattr(task.downloader, 'total_size') and task.downloader.total_size > 0:
                        progress = min(99, int(current_bytes * 100 / task.downloader.total_size))
                        task.progress = progress
                        if self.status_callback:
                            self.status_callback(task_id, "downloading", progress)
                
                task.downloader = create_downloader(progress_callback=progress_callback)
                
                # 执行下载
                try:
                    result = task.downloader.download_video(
                        url=task.url,
                        save_dir=task.save_dir,
                        quality=task.quality
                    )
                    
                    # 更新任务状态
                    task.status = "completed"
                    task.end_time = time.time()
                    task.result = result
                    task.progress = 100
                    
                    # 通知状态更新
                    if self.status_callback:
                        self.status_callback(task_id, "completed", 100, result)
                        
                    logger.info(f"下载任务完成: {task_id}")
                    
                except Exception as e:
                    # 更新任务状态
                    task.status = "failed"
                    task.end_time = time.time()
                    task.error = str(e)
                    
                    # 通知状态更新
                    if self.status_callback:
                        self.status_callback(task_id, "failed", task.progress, None, str(e))
                        
                    logger.error(f"下载任务失败: {task_id} - {str(e)}")
                    
                finally:
                    # 从活动任务中移除
                    with self.lock:
                        if task_id in self.active_tasks:
                            self.active_tasks.remove(task_id)
                    
                    # 标记队列任务完成
                    self.queue.task_done()
                
            except Exception as e:
                logger.error(f"工作线程异常: {str(e)}")
                time.sleep(1)  # 防止异常情况下CPU占用过高
        
    def shutdown(self):
        """关闭下载管理器"""
        logger.info("正在关闭下载管理器...")
        self.is_running = False
        
        # 取消所有活动任务
        with self.lock:
            for task_id in list(self.active_tasks):
                self.cancel_task(task_id)
                
        # 清空队列
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except queue.Empty:
                break
        
        # 等待所有工作线程结束
        for worker in self.workers:
            if worker.is_alive():
                worker.join(timeout=1)
                
        logger.info("下载管理器已关闭")

# 创建全局下载管理器
download_manager = DownloadManager()
