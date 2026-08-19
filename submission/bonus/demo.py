import os
from qdrant_client import QdrantClient

try:
    from feast import FeatureStore
except ImportError:
    FeatureStore = None

from agent import HybridMemoryAgent

def main():
    print("Khởi tạo Qdrant In-Memory Client...")
    qdrant = QdrantClient(":memory:")
    
    # Trỏ đường dẫn tuyệt đối đến app/feast_repo dựa trên vị trí file hiện tại
    current_dir = os.path.dirname(os.path.abspath(__file__))
    repo_path = os.path.abspath(os.path.join(current_dir, "..", "..", "app", "feast_repo"))
    fs = None
    if FeatureStore and os.path.exists(repo_path):
        try:
            print("Đang kết nối Feast Feature Store...")
            fs = FeatureStore(repo_path=repo_path)
        except Exception as e:
            print(f"Lỗi khởi tạo Feast, dùng Fallback (N/A): {e}")
    else:
        print("Không tìm thấy thư mục Feast repo, Profile context sẽ hiển thị N/A.")
        
    agent = HybridMemoryAgent(qdrant_client=qdrant, feature_store=fs)
    
    print("\n--- Đang Seed (Ghi nhớ) dữ liệu giả lập vào Episodic Memory ---")
    user = "u_001"
    
    # Seed dữ liệu để query hit
    agent.remember("Ghi chú: Kubernetes (k8s) là hệ thống mã nguồn mở để tự động hóa việc triển khai, scale và quản lý ứng dụng container.", user_id=user)
    agent.remember("Tôi đang tìm hiểu về cloud security, đặc biệt là IAM và mã hóa dữ liệu trên AWS.", user_id=user)
    agent.remember("Bài viết: Tự động mở rộng hạ tầng (auto-scaling) giúp tối ưu chi phí cực tốt khi traffic tăng vọt.", user_id=user)
    
    print("Seed hoàn tất!")
    
    # Danh sách 5 queries yêu cầu
    queries = [
        "Tôi đã đọc gì về Kubernetes?",
        "Recommend đọc gì tiếp",
        "Tôi đang quan tâm gì gần đây?",
        "Tài liệu về tự động mở rộng hạ tầng?",
        "Cho tôi summary cloud security"
    ]
    
    print("\n" + "="*60)
    for i, q in enumerate(queries, 1):
        print(f"\n[Query {i}]: {q}")
        context = agent.recall(query=q, user_id=user)
        print("-" * 30 + " ASSEMBLED CONTEXT " + "-" * 30)
        print(context)
        print("-" * 79)

if __name__ == "__main__":
    main()
