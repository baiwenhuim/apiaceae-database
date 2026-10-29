#!/usr/bin/env python3
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import re
import sys

class RangeRequestHandler(SimpleHTTPRequestHandler):
    """支持 Range 请求和 CORS 的静态文件服务器"""
    
    def end_headers(self):
        # 添加 CORS 头
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Range, Content-Range, Accept-Ranges')
        self.send_header('Accept-Ranges', 'bytes')
        super().end_headers()
    
    def do_OPTIONS(self):
        """处理预检请求"""
        self.send_response(200)
        self.end_headers()
    
    def do_GET(self):
        """处理 GET 请求，支持 Range"""
        # 获取文件路径
        path = self.translate_path(self.path)
        
        # 检查文件是否存在
        if not os.path.exists(path):
            self.send_response(404)
            self.end_headers()
            return
        
        # 获取文件大小
        file_size = os.path.getsize(path)
        
        # 检查 Range 头
        range_header = self.headers.get('Range')
        
        if range_header:
            # 解析 Range 请求
            range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
            if range_match:
                start = int(range_match.group(1))
                end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
                
                # 验证范围
                if start >= file_size or end >= file_size:
                    self.send_response(416)  # Range Not Satisfiable
                    self.send_header('Content-Range', f'bytes */{file_size}')
                    self.end_headers()
                    return
                
                # 计算内容长度
                content_length = end - start + 1
                
                # 发送 206 Partial Content
                self.send_response(206)
                self.send_header('Content-Type', self.guess_type(path))
                self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
                self.send_header('Content-Length', str(content_length))
                self.send_header('Accept-Ranges', 'bytes')
                self.end_headers()
                
                # 读取并发送指定范围的数据
                with open(path, 'rb') as f:
                    f.seek(start)
                    chunk_size = 8192
                    bytes_remaining = content_length
                    while bytes_remaining > 0:
                        read_size = min(chunk_size, bytes_remaining)
                        data = f.read(read_size)
                        if not data:
                            break
                        self.wfile.write(data)
                        bytes_remaining -= len(data)
            else:
                # 无法解析的 Range 头，返回整个文件
                self.send_response(200)
                self.send_header('Content-Type', self.guess_type(path))
                self.send_header('Content-Length', str(file_size))
                self.end_headers()
                with open(path, 'rb') as f:
                    self.wfile.write(f.read())
        else:
            # 没有 Range 请求，返回整个文件
            self.send_response(200)
            self.send_header('Content-Type', self.guess_type(path))
            self.send_header('Content-Length', str(file_size))
            self.end_headers()
            with open(path, 'rb') as f:
                self.wfile.write(f.read())

if __name__ == '__main__':
    # 切换到 static 目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(script_dir, 'home/static')
    
    # 如果上面的路径不对，手动指定
    if not os.path.exists(static_dir):
        # 手动修改为你的 static 目录路径
        static_dir = '/home/baiwenhui/your_project/static'  # ← 修改这里
    
    if not os.path.exists(static_dir):
        print(f"Error: Static directory not found at {static_dir}")
        sys.exit(1)
    
    os.chdir(static_dir)
    print(f"Serving files from: {static_dir}")
    print("Starting Range+支持请求的静态服务器 on http://0.0.0.0:8001")
    print("Press Ctrl+C to stop")
    
    server = HTTPServer(('0.0.0.0', 8001), RangeRequestHandler)
    server.serve_forever()
