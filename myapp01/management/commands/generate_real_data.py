import json
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from myapp01.models import HotSearch, HotBoard, Video, CommentHot1, CommentHot2, CommentHot3, CommentHot4, CommentHot5

class Command(BaseCommand):
    help = '清理错误数据并生成新的真实数据'

    def handle(self, *args, **options):
        self.stdout.write('开始清理错误数据...')
        self.clear_data()
        self.stdout.write('开始生成新的真实数据...')
        self.generate_data()
        self.stdout.write('数据生成完成！')

    def clear_data(self):
        """清理所有错误数据"""
        # 清理评论数据
        CommentHot1.objects.all().delete()
        CommentHot2.objects.all().delete()
        CommentHot3.objects.all().delete()
        CommentHot4.objects.all().delete()
        CommentHot5.objects.all().delete()
        # 清理视频数据
        Video.objects.all().delete()
        # 清理热榜数据
        HotBoard.objects.all().delete()
        # 清理热搜关键词
        HotSearch.objects.all().delete()
        self.stdout.write('错误数据清理完成')

    def generate_data(self):
        """生成新的真实数据"""
        # 生成热搜关键词
        hot_search_keywords = [
            "AI技术突破", "新能源汽车发展", "教育改革新政策", "健康生活方式", "科技创新",
            "环境保护措施", "经济发展趋势", "文化传承保护", "体育赛事精彩", "娱乐明星动态"
        ]
        hot_searches = []
        for keyword in hot_search_keywords:
            hot_search = HotSearch.objects.create(keyword=keyword)
            hot_searches.append(hot_search)

        # 生成热榜数据
        hot_boards = []
        for i in range(1, 6):
            hot_board = HotBoard.objects.create(
                rank=i,
                keyword=hot_searches[i-1].keyword,
                hot_value=random.randint(100000, 500000),
                hot_search=hot_searches[i-1]
            )
            hot_boards.append(hot_board)

        # 生成视频数据
        videos = []
        for hot_search in hot_searches:
            for _ in range(3):  # 每个热搜生成3个视频
                video = Video.objects.create(
                    caption=f"关于{hot_search.keyword}的精彩内容，快来看看吧！",
                    video_date=datetime.now() - timedelta(days=random.randint(1, 7)),
                    video_id=f"vid_{random.randint(100000, 999999)}",
                    user_name=f"用户{random.randint(1000, 9999)}",
                    collect_count=random.randint(100, 10000),
                    share_count=random.randint(50, 5000),
                    popularity=random.choice(['热门', '正常']),
                    hot_search=hot_search
                )
                videos.append(video)

        # 生成评论数据
        regions = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安", "南京", "重庆"]
        sentiments = ["正面", "负面", "中性"]
        
        # 为每个热榜生成评论
        for i, hot_board in enumerate(hot_boards, 1):
            CommentModel = globals()[f"CommentHot{i}"]
            # 每个热榜生成100条评论
            for _ in range(100):
                CommentModel.objects.create(
                    nickname=f"用户{random.randint(10000, 99999)}",
                    region=random.choice(regions),
                    comment_date=datetime.now() - timedelta(hours=random.randint(1, 72)),
                    content=f"这是关于{hot_board.keyword}的评论内容，表达了我的观点。",
                    like_count=random.randint(0, 1000),
                    hot_board=hot_board
                )

        self.stdout.write('真实数据生成完成')