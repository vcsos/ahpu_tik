from django.db import models
from ..models import CommentHot1, CommentHot2, CommentHot3, CommentHot4, CommentHot5, HotBoard


class CommentRepository:
    """评论数据访问层"""

    # 评论模型映射
    COMMENT_MODELS = {
        1: CommentHot1,
        2: CommentHot2,
        3: CommentHot3,
        4: CommentHot4,
        5: CommentHot5,
    }

    @classmethod
    def get_comment_model(cls, rank):
        """根据排名获取评论模型"""
        return cls.COMMENT_MODELS.get(rank)

    @classmethod
    def get_comments_by_hot_board(cls, hot_board, page=1, page_size=20):
        """根据热榜获取评论数据"""
        rank = hot_board.rank
        CommentModel = cls.get_comment_model(rank)
        if not CommentModel:
            return [], 0

        offset = (page - 1) * page_size
        comments = CommentModel.objects.filter(hot_board=hot_board).order_by('-like_count', '-comment_date')[offset:offset+page_size]
        total = CommentModel.objects.filter(hot_board=hot_board).count()
        return comments, total

    @classmethod
    def get_region_distribution(cls, hot_board):
        """获取评论地区分布"""
        rank = hot_board.rank
        CommentModel = cls.get_comment_model(rank)
        if not CommentModel:
            return []

        regions = CommentModel.objects.filter(hot_board_id=hot_board.id) \
            .values_list('region', flat=True) \
            .exclude(region__isnull=True)

        return regions

    @classmethod
    def get_sentiment_distribution(cls, hot_board):
        """获取评论情感分布"""
        rank = hot_board.rank
        CommentModel = cls.get_comment_model(rank)
        if not CommentModel:
            return []

        sentiments = CommentModel.objects.filter(hot_board=hot_board) \
            .values('sentiment') \
            .annotate(count=models.Count('sentiment'))

        return sentiments

    @classmethod
    def get_top_comments(cls, hot_board, limit=100):
        """获取热门评论"""
        rank = hot_board.rank
        CommentModel = cls.get_comment_model(rank)
        if not CommentModel:
            return []

        return CommentModel.objects.filter(hot_board=hot_board).order_by('-like_count')[:limit]


