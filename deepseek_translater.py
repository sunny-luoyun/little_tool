#!/usr/bin/env python3
"""
日文小说翻译器（使用 DeepSeek API）
支持并发翻译、自适应并发控制、进度显示。
"""

import asyncio
import aiohttp
import argparse
import os
import sys
import time
from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from tqdm import tqdm

# ---------------------------- 配置区域 ----------------------------
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = "deepseek-chat"
MAX_CHUNK_CHARS = 1500                # 每个文本块的最大字符数
MAX_CONCURRENT_WORKERS = 20            # 最大并发工作协程数
MIN_CONCURRENT_WORKERS = 1             # 最小并发工作协程数
ADAPT_WINDOW_SIZE = 20                  # 用于自适应决策的滑动窗口大小
FAILURE_RATE_THRESHOLD = 0.1            # 允许的最大失败率（超过则减少并发）
SUCCESS_RATE_INCREASE_THRESHOLD = 0.98  # 成功率高于此且平均响应时间低于阈值时增加并发
RESPONSE_TIME_THRESHOLD = 3.0           # 平均响应时间阈值（秒）
RETRY_LIMIT = 3                         # 每个块的最大重试次数
RETRY_BACKOFF_FACTOR = 1.5              # 重试退避因子
# -------------------------------------------------------------------

@dataclass
class Chunk:
    """待翻译的文本块"""
    index: int
    text: str
    retries: int = 0

@dataclass
class TranslationResult:
    """翻译结果"""
    index: int
    text: Optional[str]
    success: bool
    error: Optional[str] = None

@dataclass
class WorkerStats:
    """工作协程统计信息"""
    success_count: int = 0
    failure_count: int = 0
    recent_response_times: deque = field(default_factory=lambda: deque(maxlen=ADAPT_WINDOW_SIZE))

    @property
    def total_requests(self) -> int:
        return self.success_count + self.failure_count

    @property
    def failure_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.failure_count / self.total_requests

    @property
    def avg_response_time(self) -> Optional[float]:
        if not self.recent_response_times:
            return None
        return sum(self.recent_response_times) / len(self.recent_response_times)

class AdaptiveController:
    """自适应控制器：根据统计信息调整工作协程数量"""
    def __init__(self, initial_workers: int = 5):
        self.current_workers = initial_workers
        self.stats = WorkerStats()
        self._lock = asyncio.Lock()

    async def record_success(self, response_time: float):
        async with self._lock:
            self.stats.success_count += 1
            self.stats.recent_response_times.append(response_time)

    async def record_failure(self):
        async with self._lock:
            self.stats.failure_count += 1

    async def should_adjust(self) -> Optional[int]:
        """根据统计信息决定是否调整并发数，返回新的 worker 数量或 None"""
        async with self._lock:
            if self.stats.total_requests < ADAPT_WINDOW_SIZE // 2:
                return None  # 数据不足，暂不调整

            failure_rate = self.stats.failure_rate
            avg_rt = self.stats.avg_response_time

            new_workers = self.current_workers

            # 失败率过高 -> 减少并发
            if failure_rate > FAILURE_RATE_THRESHOLD and self.current_workers > MIN_CONCURRENT_WORKERS:
                new_workers = max(MIN_CONCURRENT_WORKERS, self.current_workers - 1)
                print(f"\n[自适应] 失败率 {failure_rate:.2%} 过高，减少并发数至 {new_workers}")
            # 成功率很高且平均响应时间理想 -> 增加并发
            elif (failure_rate < 1 - SUCCESS_RATE_INCREASE_THRESHOLD and
                  avg_rt is not None and avg_rt < RESPONSE_TIME_THRESHOLD and
                  self.current_workers < MAX_CONCURRENT_WORKERS):
                new_workers = min(MAX_CONCURRENT_WORKERS, self.current_workers + 1)
                print(f"\n[自适应] 响应快速且成功率高，增加并发数至 {new_workers}")

            if new_workers != self.current_workers:
                self.current_workers = new_workers
                return new_workers
            return None

async def translate_chunk(
    session: aiohttp.ClientSession,
    chunk: Chunk,
    api_key: str,
    model: str = DEFAULT_MODEL
) -> Tuple[int, Optional[str], Optional[str], float]:
    """
    调用 DeepSeek API 翻译单个文本块。
    返回 (index, translated_text, error_message, response_time)
    """
    start_time = time.monotonic()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是一个日文翻译专家，将用户输入的日文文本翻译成流畅的中文。"},
            {"role": "user", "content": chunk.text}
        ],
        "temperature": 0.3,
        "max_tokens": 2000
    }
    try:
        async with session.post(DEEPSEEK_API_URL, headers=headers, json=payload) as resp:
            response_time = time.monotonic() - start_time
            if resp.status == 200:
                data = await resp.json()
                translated = data['choices'][0]['message']['content'].strip()
                return chunk.index, translated, None, response_time
            else:
                error_text = await resp.text()
                error_msg = f"HTTP {resp.status}: {error_text}"
                return chunk.index, None, error_msg, response_time
    except asyncio.TimeoutError:
        return chunk.index, None, "Timeout", time.monotonic() - start_time
    except Exception as e:
        return chunk.index, None, str(e), time.monotonic() - start_time

async def worker(
    worker_id: int,
    task_queue: asyncio.Queue,
    result_queue: asyncio.Queue,
    api_key: str,
    controller: AdaptiveController,
    session: aiohttp.ClientSession
):
    """工作协程：不断从任务队列获取块并翻译，结果放入结果队列"""
    while True:
        chunk: Chunk = await task_queue.get()
        try:
            index, translated, error, response_time = await translate_chunk(session, chunk, api_key)
            if translated is not None:
                await controller.record_success(response_time)
                await result_queue.put(TranslationResult(index, translated, success=True))
            else:
                await controller.record_failure()
                # 判断是否重试
                if chunk.retries < RETRY_LIMIT:
                    chunk.retries += 1
                    # 退避重试：等待一段时间后放回队列
                    wait = RETRY_BACKOFF_FACTOR ** chunk.retries
                    print(f"\n[重试 {chunk.retries}/{RETRY_LIMIT}] 块 {index} 失败: {error}，{wait:.1f}秒后重试")
                    await asyncio.sleep(wait)
                    await task_queue.put(chunk)
                else:
                    # 超过重试次数，记录失败结果
                    await result_queue.put(TranslationResult(index, None, success=False, error=error))
        finally:
            task_queue.task_done()

async def controller(
    task_queue: asyncio.Queue,
    result_queue: asyncio.Queue,
    api_key: str,
    total_chunks: int,
    pbar: tqdm
):
    """
    控制器协程：
    - 启动初始数量的 worker
    - 定期检查自适应统计信息并调整 worker 数量
    - 收集结果更新进度条
    - 所有任务完成后停止 worker
    """
    controller = AdaptiveController(initial_workers=5)
    workers = []
    stats_lock = asyncio.Lock()
    connector = aiohttp.TCPConnector(limit=0)  # 连接池无限制，由自适应控制
    async with aiohttp.ClientSession(connector=connector) as session:
        # 启动初始 workers
        for i in range(controller.current_workers):
            worker_task = asyncio.create_task(
                worker(i, task_queue, result_queue, api_key, controller, session)
            )
            workers.append(worker_task)

        # 收集结果并更新进度
        results = [None] * total_chunks
        completed = 0
        while completed < total_chunks:
            # 等待一个结果
            res = await result_queue.get()
            results[res.index] = res
            completed += 1
            pbar.update(1)
            pbar.set_postfix(workers=controller.current_workers)

            # 自适应调整（每完成一个结果检查一次，实际可降低频率）
            new_count = await controller.should_adjust()
            if new_count is not None:
                # 调整 worker 数量
                diff = new_count - len(workers)
                if diff > 0:
                    for _ in range(diff):
                        w = asyncio.create_task(
                            worker(len(workers), task_queue, result_queue, api_key, controller, session)
                        )
                        workers.append(w)
                elif diff < 0:
                    # 减少 worker：取消多余的 worker
                    for _ in range(-diff):
                        w = workers.pop()
                        w.cancel()
                # 更新进度条显示
                pbar.set_postfix(workers=new_count)

        # 所有任务完成，取消所有 worker
        for w in workers:
            w.cancel()
        await asyncio.gather(*workers, return_exceptions=True)

    return results

def split_text_into_chunks(text: str, max_chars: int = MAX_CHUNK_CHARS) -> List[str]:
    """
    将文本分割成适合翻译的块。
    按段落分割，段落过长则按句号、问号、感叹号进一步分割。
    """
    paragraphs = text.split('\n')
    chunks = []
    for para in paragraphs:
        if not para.strip():
            continue
        # 如果段落本身很短，直接作为一个块
        if len(para) <= max_chars:
            chunks.append(para)
        else:
            # 按句子分割（简单正则：句号、问号、感叹号后可能跟空格或换行）
            import re
            sentences = re.split(r'([。！？])', para)
            # 重组句子，使每个块不超过 max_chars
            current_chunk = ""
            for i in range(0, len(sentences)-1, 2):
                sent = sentences[i] + sentences[i+1]  # 句子+标点
                if len(current_chunk) + len(sent) <= max_chars:
                    current_chunk += sent
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = sent
            if current_chunk:
                chunks.append(current_chunk)
            # 如果最后还有残余（奇数个元素的情况），添加
            if len(sentences) % 2 == 1 and sentences[-1]:
                if len(current_chunk) + len(sentences[-1]) <= max_chars:
                    current_chunk += sentences[-1]
                    # 替换最后一个块
                    chunks[-1] = current_chunk
                else:
                    chunks.append(sentences[-1])
    # 过滤空块
    return [c for c in chunks if c.strip()]

async def main_async(api_key: str, file_path: str):
    """异步主函数"""
    # 读取文件
    if not os.path.exists(file_path):
        print(f"错误：文件 {file_path} 不存在")
        return
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    print(f"已读取文件，大小：{len(text)} 字符")

    # 分块
    chunks = split_text_into_chunks(text)
    total = len(chunks)
    print(f"已将文本分割为 {total} 个块")

    # 创建任务队列和结果队列
    task_queue = asyncio.Queue()
    for idx, chunk_text in enumerate(chunks):
        task_queue.put_nowait(Chunk(index=idx, text=chunk_text))
    result_queue = asyncio.Queue()

    # 进度条
    with tqdm(total=total, desc="翻译进度", unit="块") as pbar:
        results = await controller(task_queue, result_queue, api_key, total, pbar)

    # 按索引排序并写入输出文件
    output_path = os.path.splitext(file_path)[0] + "_translated.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        for res in results:
            if res and res.success:
                f.write(res.text + '\n\n')
            else:
                f.write(f"[翻译失败: {res.error if res else '未知错误'}]\n\n")
    print(f"\n翻译完成！结果已保存至：{output_path}")

def main():
    parser = argparse.ArgumentParser(description="日文小说翻译器（使用 DeepSeek API）")
    parser.add_argument("--key", help="DeepSeek API 密钥，若不提供则交互式输入")
    parser.add_argument("--file", help="待翻译的日文小说文件路径，若不提供则交互式输入")
    args = parser.parse_args()

    api_key = args.key
    if not api_key:
        api_key = input("请输入你的 DeepSeek API 密钥: ").strip()
        if not api_key:
            print("错误：未提供 API 密钥")
            sys.exit(1)

    file_path = args.file
    if not file_path:
        file_path = input("请输入日文小说 txt 文件路径: ").strip()
        if not file_path:
            print("错误：未提供文件路径")
            sys.exit(1)

    asyncio.run(main_async(api_key, file_path))

if __name__ == "__main__":
    main()