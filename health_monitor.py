#!/usr/bin/env python3

import requests
import time
from datetime import datetime
from prometheus_client import start_http_server, Gauge
from typing import Dict, List, Optional

# Định nghĩa các metric để theo dõi
NODE_UP = Gauge('rqlite_node_up', 'Status of rqlite node (1 = up, 0 = down)', ['node_addr'])
NODE_LEADER = Gauge('rqlite_node_leader', 'Whether node is leader (1 = leader, 0 = follower)', ['node_addr'])
NODE_RESPONSE_TIME = Gauge('rqlite_node_response_time', 'Response time in seconds', ['node_addr'])

class HealthMonitor:
    """
    Class giám sát sức khỏe của cụm rqlite.
    Theo dõi trạng thái, thời gian phản hồi và vai trò của từng node.
    """
    
    def __init__(self, nodes: List[str], check_interval: int = 5):
        """
        Khởi tạo health monitor
        
        Args:
            nodes: Danh sách địa chỉ các node cần giám sát
            check_interval: Khoảng thời gian giữa các lần kiểm tra (giây)
        """
        self.nodes = nodes
        self.check_interval = check_interval
        self.node_status: Dict[str, bool] = {node: False for node in nodes}
        
    def check_node_health(self, node_addr: str) -> Dict:
        """
        Kiểm tra sức khỏe của một node
        
        Args:
            node_addr: Địa chỉ của node cần kiểm tra
            
        Returns:
            Dict chứa thông tin về trạng thái node
        """
        try:
            # Đo thời gian phản hồi
            start_time = time.time()
            response = requests.get(f'http://{node_addr}/status', timeout=5)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                is_leader = data.get('store', {}).get('leader') == node_addr
                
                # Cập nhật các metric
                NODE_UP.labels(node_addr=node_addr).set(1)
                NODE_LEADER.labels(node_addr=node_addr).set(1 if is_leader else 0)
                NODE_RESPONSE_TIME.labels(node_addr=node_addr).set(response_time)
                
                return {
                    'status': 'healthy',
                    'is_leader': is_leader,
                    'response_time': response_time
                }
        except Exception as e:
            # Ghi nhận node không phản hồi
            NODE_UP.labels(node_addr=node_addr).set(0)
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    def monitor_cluster(self):
        """
        Giám sát liên tục toàn bộ cụm
        Kiểm tra sức khỏe của từng node theo chu kỳ
        """
        print(f"Bắt đầu giám sát cụm rqlite ({len(self.nodes)} nodes)")
        
        while True:
            for node in self.nodes:
                status = self.check_node_health(node)
                print(f"{datetime.now()}: Node {node} - {status['status']}")
            time.sleep(self.check_interval)

def main():
    """
    Hàm main để khởi chạy health monitor
    """
    # Khởi động Prometheus metrics server
    start_http_server(8000)
    
    # Danh sách nodes mặc định (có thể cấu hình qua biến môi trường)
    nodes = [
        "localhost:4001",
        "localhost:4003",
        "localhost:4005"
    ]
    
    # Khởi tạo và chạy health monitor
    monitor = HealthMonitor(nodes)
    monitor.monitor_cluster()

if __name__ == "__main__":
    main() 