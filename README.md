# RQLite Cluster Monitor
Ứng dụng monitor cho RQLite cluster, theo dõi sức khỏe và phục hồi của các node.
## Tính năng
- Monitor trạng thái của các node trong cluster
- Theo dõi leader election
- Đánh giá sức khỏe tổng thể của cluster
- Ghi nhận các sự kiện up/down của node
- Dashboard trực quan
## Cài đặt
1. Clone repository:
git clone https://github.com/your-username/rqlite-monitor.git
cd rqlite-monitor
2. Tạo và kích hoạt môi trường ảo:
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate  # Windows
3. Cài đặt dependencies:
pip install -r requirements.txt
 Cấu hình
1. Chỉnh sửa danh sách nodes trong `app/cluster_health_monitor.py`:
```python
CLUSTER_NODES = [
    "http://localhost:4001",
    "http://localhost:4003",
    "http://localhost:4005"
]
## Sử dụng
1. Khởi động health monitor:
python app/cluster_health_monitor.py
2. Khởi động recovery monitor:
python app/node_recovery_monitor.py
3. Truy cập dashboard:
- Health Monitor: http://localhost:5003
- Recovery Monitor: http://localhost:5002
## API Endpoints
- GET `/api/cluster` - Lấy thông tin trạng thái cluster
- GET `/api/stats` - Lấy thống kê về các node