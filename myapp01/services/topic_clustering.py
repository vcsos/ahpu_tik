from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import numpy as np
from ..models import HotBoard, CommentHot1, CommentHot2, CommentHot3, CommentHot4, CommentHot5
from ..services.text_analysis import load_stopwords

class TopicClusteringService:
    """话题聚类服务"""
    
    @staticmethod
    def get_topic_clusters(n_clusters=5):
        """获取话题聚类
        
        Args:
            n_clusters: 聚类数量
            
        Returns:
            dict: 聚类结果
        """
        # 获取所有热榜关键词
        hotboards = HotBoard.objects.all()
        keywords = [board.keyword for board in hotboards]
        
        if not keywords:
            return {
                'clusters': [],
                'error': 'No hotboard data found'
            }
        
        # 加载停用词
        stop_words = load_stopwords()
        
        # 向量化
        vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=stop_words
        )
        tfidf_matrix = vectorizer.fit_transform(keywords)
        
        # 聚类
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        labels = kmeans.fit_predict(tfidf_matrix)
        
        # 降维用于可视化
        pca = PCA(n_components=2)
        pca_result = pca.fit_transform(tfidf_matrix.toarray())
        
        # 构建聚类结果
        clusters = {}
        for i, label in enumerate(labels):
            if label not in clusters:
                clusters[label] = {
                    'keywords': [],
                    'center': kmeans.cluster_centers_[label].tolist(),
                    'size': 0
                }
            clusters[label]['keywords'].append(keywords[i])
            clusters[label]['size'] += 1
        
        # 转换为列表格式
        cluster_list = []
        for label, data in clusters.items():
            cluster_list.append({
                'cluster_id': int(label),
                'keywords': data['keywords'],
                'size': data['size'],
                'center': data['center']
            })
        
        # 构建可视化数据
        visualization_data = []
        for i, (keyword, label, (x, y)) in enumerate(zip(keywords, labels, pca_result)):
            visualization_data.append({
                'keyword': keyword,
                'cluster': int(label),
                'x': float(x),
                'y': float(y)
            })
        
        return {
            'clusters': cluster_list,
            'visualization_data': visualization_data,
            'total_keywords': len(keywords),
            'total_clusters': n_clusters
        }
    
    @staticmethod
    def get_comment_clusters(hot_board_id, n_clusters=3):
        """获取评论聚类
        
        Args:
            hot_board_id: 热榜ID
            n_clusters: 聚类数量
            
        Returns:
            dict: 聚类结果
        """
        # 获取热榜
        try:
            hotboard = HotBoard.objects.get(id=hot_board_id)
        except HotBoard.DoesNotExist:
            return {
                'clusters': [],
                'error': 'Hotboard not found'
            }
        
        # 根据热榜排名选择评论表
        rank = hotboard.rank
        comment_models = {
            1: CommentHot1,
            2: CommentHot2,
            3: CommentHot3,
            4: CommentHot4,
            5: CommentHot5
        }
        
        CommentModel = comment_models.get(rank)
        if not CommentModel:
            return {
                'clusters': [],
                'error': 'Invalid rank'
            }
        
        # 获取评论
        comments = CommentModel.objects.filter(hot_board_id=hot_board_id)
        comment_texts = [comment.content for comment in comments if comment.content.strip()]
        
        if not comment_texts:
            return {
                'clusters': [],
                'error': 'No comments found'
            }
        
        # 加载停用词
        stop_words = load_stopwords()
        
        # 向量化
        vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=stop_words,
            max_df=0.8,
            min_df=2
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(comment_texts)
        except ValueError:
            return {
                'clusters': [],
                'error': 'Not enough unique words for clustering'
            }
        
        # 聚类
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        labels = kmeans.fit_predict(tfidf_matrix)
        
        # 降维用于可视化
        pca = PCA(n_components=2)
        pca_result = pca.fit_transform(tfidf_matrix.toarray())
        
        # 获取每个聚类的关键词
        terms = vectorizer.get_feature_names_out()
        cluster_keywords = {}
        for i in range(n_clusters):
            centroid = kmeans.cluster_centers_[i]
            top_indices = centroid.argsort()[-10:][::-1]  # 前10个关键词
            top_terms = [terms[idx] for idx in top_indices]
            cluster_keywords[i] = top_terms
        
        # 构建聚类结果
        clusters = {}
        for i, label in enumerate(labels):
            if label not in clusters:
                clusters[label] = {
                    'comments': [],
                    'keywords': cluster_keywords.get(label, []),
                    'size': 0
                }
            clusters[label]['comments'].append(comment_texts[i])
            clusters[label]['size'] += 1
        
        # 转换为列表格式
        cluster_list = []
        for label, data in clusters.items():
            cluster_list.append({
                'cluster_id': int(label),
                'comments': data['comments'][:5],  # 只返回前5条评论
                'keywords': data['keywords'],
                'size': data['size']
            })
        
        # 构建可视化数据
        visualization_data = []
        for i, (comment, label, (x, y)) in enumerate(zip(comment_texts, labels, pca_result)):
            visualization_data.append({
                'comment': comment[:100],  # 只显示前100个字符
                'cluster': int(label),
                'x': float(x),
                'y': float(y)
            })
        
        return {
            'clusters': cluster_list,
            'visualization_data': visualization_data,
            'total_comments': len(comment_texts),
            'total_clusters': n_clusters,
            'hotboard_keyword': hotboard.keyword
        }
    
    @staticmethod
    def get_cluster_summary():
        """获取聚类摘要
        
        Returns:
            dict: 聚类摘要
        """
        # 获取话题聚类
        topic_clusters = TopicClusteringService.get_topic_clusters()
        
        # 分析聚类分布
        cluster_sizes = [cluster['size'] for cluster in topic_clusters['clusters']]
        total_keywords = topic_clusters['total_keywords']
        
        # 计算聚类统计
        if cluster_sizes:
            avg_cluster_size = sum(cluster_sizes) / len(cluster_sizes)
            max_cluster_size = max(cluster_sizes)
            min_cluster_size = min(cluster_sizes)
        else:
            avg_cluster_size = 0
            max_cluster_size = 0
            min_cluster_size = 0
        
        return {
            'total_keywords': total_keywords,
            'total_clusters': len(cluster_sizes),
            'avg_cluster_size': avg_cluster_size,
            'max_cluster_size': max_cluster_size,
            'min_cluster_size': min_cluster_size,
            'cluster_distribution': cluster_sizes
        }
