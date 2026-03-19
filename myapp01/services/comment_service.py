from collections import defaultdict
from ..repositories.comment_repository import CommentRepository
from ..repositories.hotboard_repository import HotBoardRepository


class CommentService:
    """评论服务层"""

    @staticmethod
    def get_comments_by_hot_id(hot_id, page=1, page_size=20):
        """根据热榜ID获取评论"""
        hot_board = HotBoardRepository.get_hot_board_by_id(hot_id)
        if not hot_board:
            return None

        comments, total = CommentRepository.get_comments_by_hot_board(hot_board, page, page_size)

        # 序列化评论数据
        data = [{
            "nickname": c.nickname,
            "region": c.region,
            "date": c.comment_date.isoformat(),
            "content": c.content,
            "likes": c.like_count,
        } for c in comments]

        return {
            'data': data,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }

    @staticmethod
    def get_region_distribution(hot_board_id):
        """获取地区分布"""
        hot_board = HotBoardRepository.get_hot_board_by_id(hot_board_id)
        if not hot_board:
            return None

        regions = CommentRepository.get_region_distribution(hot_board)

        # 统计地区数据并标准化名称
        region_counts = defaultdict(int)
        for r in regions:
            if not r:
                continue
            normalized = CommentService._normalize_region(r)
            region_counts[normalized] += 1

        # 生成图表数据
        sorted_regions = sorted(region_counts.items(), key=lambda x: -x[1])
        top10 = sorted_regions[:10]

        # 优化地图数据格式
        map_data = []
        for region, count in sorted_regions:
            map_data.append({
                'name': region,
                'value': count
            })

        return {
            'top10': {
                'regions': [r[0] for r in top10],
                'values': [r[1] for r in top10]
            },
            'map_data': map_data,
            'total_regions': len(region_counts),
            'total_comments': sum(region_counts.values())
        }

    @staticmethod
    def get_sentiment_analysis(hot_board_id):
        """获取情感分析"""
        hot_board = HotBoardRepository.get_hot_board_by_id(hot_board_id)
        if not hot_board:
            return None

        # 统计情感分布
        sentiments = CommentRepository.get_sentiment_distribution(hot_board)

        # 构建情感分布数据
        sentiment_distribution = {}
        for s in sentiments:
            sentiment = str(s['sentiment']).strip() or '未知'
            sentiment_distribution[sentiment] = s['count']

        # 确保基本情感类型存在
        for sentiment in ['积极', '消极', '中性', '未知']:
            if sentiment not in sentiment_distribution:
                sentiment_distribution[sentiment] = 0

        # 构建散点图数据
        comments = CommentRepository.get_top_comments(hot_board, 100)
        scatter_data = []
        for i, comment in enumerate(comments):
            try:
                point = {
                    'x': float(comment.like_count),
                    'y': float(i),
                    'likes': int(comment.like_count),
                    'sentiment': str(comment.sentiment).strip() or '未知',
                    'content': comment.content[:50]
                }
                scatter_data.append(point)
            except Exception as e:
                print(f"数据格式错误: {e}")

        return {
            'distribution': sentiment_distribution,
            'total_comments': sum(sentiment_distribution.values()),
            'sentiment_types': list(sentiment_distribution.keys()),
            'sentiment_values': list(sentiment_distribution.values()),
            'scatter_data': scatter_data
        }

    @staticmethod
    def _normalize_region(region):
        """统一地区名称格式"""
        replacements = ['省', '市', '自治区', '特别行政区']
        for rep in replacements:
            region = region.replace(rep, '')
        return region