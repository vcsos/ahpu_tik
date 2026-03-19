import os
from collections import defaultdict
from typing import Optional, List
from django.db import connection


def get_comment_table(rank: int) -> Optional[str]:
    """
    根据热榜 rank 返回对应的评论表名。
    """
    comment_models = {
        1: 'CommentHot1',
        2: 'CommentHot2',
        3: 'CommentHot3',
        4: 'CommentHot4',
        5: 'CommentHot5',
    }
    return comment_models.get(rank)


def load_stopwords() -> List[str]:
    """
    加载停用词表，用于 TF-IDF 构建。
    """
    try:
        current_dir = os.path.dirname(os.path.dirname(__file__))
        stopwords_path = os.path.join(current_dir, 'stopwords.txt')
        with open(stopwords_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []


def get_comment_texts(table_name: str, hot_board_id: int) -> List[str]:
    """
    从评论表中读取评论内容。
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT content 
            FROM {table_name}
            WHERE hot_board_id = %s
            """.format(table_name=table_name),
            [hot_board_id],
        )
        return [row[0] for row in cursor.fetchall() if row[0].strip()]

