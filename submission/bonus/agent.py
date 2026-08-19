import uuid
from typing import List, Dict, Any

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
try:
    from feast import FeatureStore
except ImportError:
    FeatureStore = Any


class HybridMemoryAgent:
    def __init__(self, qdrant_client: QdrantClient, feature_store: FeatureStore = None):
        self.qdrant = qdrant_client
        self.fs = feature_store
        
        # Sử dụng mô hình nhẹ, tương tự NB2
        self.embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        self.collection_name = "episodic_memory"
        
        # Khởi tạo Qdrant collection nếu chưa có
        if not self.qdrant.collection_exists(self.collection_name):
            self.qdrant.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
            
    def remember(self, text: str, user_id: str = "u_001") -> None:
        """Add a new piece of episodic memory for this user."""
        # Chunk text (POC minimal: split by newlines hoặc lấy cả đoạn)
        chunks = [c.strip() for c in text.split("\n") if c.strip()]
        if not chunks:
            chunks = [text]
            
        # Embed và Upsert vào Qdrant
        vectors = list(self.embedder.embed(chunks))
        points = []
        for chunk, vector in zip(chunks, vectors):
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector.tolist(),
                    payload={"user_id": user_id, "text": chunk}
                )
            )
            
        self.qdrant.upsert(collection_name=self.collection_name, points=points)

    def recall(self, query: str, user_id: str = "u_001") -> str:
        """Retrieve top-K memories + user profile features -> return assembled context."""
        
        # 1. Get user profile + recent activity from Feast online store
        topic_affinity, reading_speed, queries_last_hour = "N/A", "N/A", "N/A"
        if self.fs is not None:
            try:
                features = self.fs.get_online_features(
                    features=[
                        "user_profile_features:topic_affinity",
                        "user_profile_features:reading_speed_wpm",
                        "query_velocity_features:queries_last_hour"
                    ],
                    entity_rows=[{"user_id": user_id}],
                ).to_dict()
                
                # Trích xuất giá trị (Feast trả về list cho mỗi cột)
                topic_affinity = features.get("topic_affinity", ["N/A"])[0] or "N/A"
                reading_speed = features.get("reading_speed_wpm", ["N/A"])[0] or "N/A"
                queries_last_hour = features.get("queries_last_hour", ["N/A"])[0] or "N/A"
            except Exception as e:
                pass # Bỏ qua nếu Feast chưa được setup đầy đủ trong môi trường local

        # 2. Hybrid search Qdrant filtered by user_id
        # (Để code POC đơn giản, ta dùng Vector search trên Qdrant với payload Filter)
        query_vector = next(self.embedder.embed([query])).tolist()
        search_result = self.qdrant.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id)
                    )
                ]
            ),
            limit=3
        )
        
        top_memories = [hit.payload["text"] for hit in search_result.points]
        memories_str = "\n- ".join(top_memories) if top_memories else "Không có ký ức nào phù hợp."
        
        # 3. Assemble context string
        context = f"""
[USER PROFILE & ACTIVITY]
- Topic affinity: {topic_affinity}
- Reading speed: {reading_speed} wpm
- Recent activity: {queries_last_hour} queries in the last hour.

[TOP EPISODIC MEMORIES]
- {memories_str}
"""
        return context.strip()
