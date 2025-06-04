#!/usr/bin/env python3

import requests
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from flask import Flask, render_template, jsonify

@dataclass
class NodeEvent:
    """
    Lưu trữ thông tin về sự kiện down/up của node
    """
    timestamp: datetime
    event_type: str  # 'down' hoặc 'up'
    downtime: float = 0.0  # thời gian downtime tính bằng giây

@dataclass
class NodeStatus:
    """
    Theo dõi trạng thái và lịch sử của node
    """
    address: str
    is_healthy: bool = True
    last_check: datetime = field(default_factory=datetime.now)
    last_down: Optional[datetime] = None
    events: List[NodeEvent] = field(default_factory=list)
    total_downtime: float = 0.0

class NodeRecoveryMonitor:
    """
    Theo dõi và ghi nhận sự kiện phục hồi của các node trong cluster
    """
    def __init__(self, nodes: List[str]):
        """
        Khởi tạo monitor
        
        Args:
            nodes: Danh sách địa chỉ các node cần theo dõi
        """
        self.nodes = {node: NodeStatus(address=node) for node in nodes}
        
    def check_node(self, node_addr: str) -> None:
        """
        Kiểm tra trạng thái node và cập nhật lịch sử
        
        Args:
            node_addr: Địa chỉ node cần kiểm tra
        """
        node = self.nodes[node_addr]
        current_time = datetime.now()
        
        try:
            response = requests.get(f'http://{node_addr}/status', timeout=2)
            is_healthy = response.status_code == 200
        except:
            is_healthy = False
            
        # Node chuyển từ healthy sang unhealthy
        if node.is_healthy and not is_healthy:
            node.last_down = current_time
            node.events.append(NodeEvent(
                timestamp=current_time,
                event_type='down'
            ))
            
        # Node phục hồi từ unhealthy sang healthy
        elif not node.is_healthy and is_healthy:
            downtime = (current_time - node.last_down).total_seconds()
            node.total_downtime += downtime
            node.events.append(NodeEvent(
                timestamp=current_time,
                event_type='up',
                downtime=downtime
            ))
            
        node.is_healthy = is_healthy
        node.last_check = current_time

    def get_node_stats(self) -> Dict:
        """
        Lấy thống kê về trạng thái và lịch sử các node
        
        Returns:
            Dict chứa thông tin thống kê của các node
        """
        stats = {}
        for addr, node in self.nodes.items():
            stats[addr] = {
                'is_healthy': node.is_healthy,
                'total_downtime': node.total_downtime,
                'last_check': node.last_check.isoformat(),
                'recent_events': [
                    {
                        'timestamp': e.timestamp.isoformat(),
                        'type': e.event_type,
                        'downtime': e.downtime
                    }
                    for e in node.events[-5:]  # 5 sự kiện gần nhất
                ]
            }
        return stats

# Khởi tạo Flask app
app = Flask(__name__)
monitor = NodeRecoveryMonitor([
    'localhost:4001',  # rqlite1 HTTP API
    'localhost:4003',  # rqlite2 HTTP API
    'localhost:4005'   # rqlite3 HTTP API
])

@app.route('/')
def index():
    """Hiển thị trang dashboard"""
    return render_template('recovery_dashboard.html', 
                         stats=monitor.get_node_stats())

@app.route('/api/stats')
def get_stats():
    """API endpoint trả về thống kê dạng JSON"""
    return jsonify(monitor.get_node_stats())

def monitor_loop():
    """Background task kiểm tra các node"""
    while True:
        for node in monitor.nodes:
            monitor.check_node(node)
        time.sleep(5)

if __name__ == '__main__':
    from threading import Thread
    # Chạy monitor trong thread riêng
    Thread(target=monitor_loop, daemon=True).start()
    # Khởi động web server
    app.run(port=50022) 