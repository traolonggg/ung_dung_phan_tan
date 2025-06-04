from flask import Flask, render_template, jsonify
import requests
import time
from datetime import datetime

app = Flask(__name__)

# Cấu hình cluster - 3 nodes
CLUSTER_NODES = [
    "http://localhost:4001",
    "http://localhost:4003", 
    "http://localhost:4005"
]

def check_node_health(node_url):
    """Kiểm tra health của 1 node"""
    try:
        start_time = time.time()
        response = requests.get(f"{node_url}/status", timeout=2)
        response_time = round((time.time() - start_time) * 1000, 2)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'url': node_url,
                'status': 'OK',
                'response_time': f"{response_time}ms",
                'role': data.get('store', {}).get('raft', {}).get('state', 'unknown'),
                'leader': data.get('store', {}).get('leader', 'unknown')
            }
        else:
            return {
                'url': node_url,
                'status': 'ERROR',
                'response_time': f"{response_time}ms",
                'error': f'HTTP {response.status_code}'
            }
    except Exception as e:
        return {
            'url': node_url,
            'status': 'OFFLINE',
            'response_time': 'N/A',
            'error': str(e)
        }

def check_cluster_health():
    """Kiểm tra health của toàn cluster"""
    nodes_health = []
    
    for node_url in CLUSTER_NODES:
        health = check_node_health(node_url)
        nodes_health.append(health)
    
    # Tính toán tổng quan cluster
    total_nodes = len(nodes_health)
    healthy_nodes = len([n for n in nodes_health if n['status'] == 'OK'])
    
    cluster_status = 'HEALTHY'
    if healthy_nodes == 0:
        cluster_status = 'DOWN'
    elif healthy_nodes < total_nodes // 2 + 1:
        cluster_status = 'CRITICAL'
    elif healthy_nodes < total_nodes:
        cluster_status = 'DEGRADED'
    
    return {
        'cluster_status': cluster_status,
        'healthy_nodes': healthy_nodes,
        'total_nodes': total_nodes,
        'nodes': nodes_health,
        'check_time': datetime.now().strftime('%H:%M:%S')
    }

@app.route('/')
def home():
    """Trang chính hiển thị cluster health"""
    cluster_health = check_cluster_health()
    return render_template('cluster_health.html', cluster=cluster_health)

@app.route('/api/cluster')
def api_cluster():
    """API trả về cluster health"""
    return jsonify(check_cluster_health())

if __name__ == '__main__':
    print("RQLite Cluster Health Monitor")
    print(f"Dashboard: http://localhost:5003")
    print(f"Monitoring cluster: {len(CLUSTER_NODES)} nodes")
    
    app.run(debug=True, host='localhost', port=5003) 