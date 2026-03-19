from django.core.management.base import BaseCommand
from myapp01.models import HotSearch, HotBoard, CommentHot1, CommentHot2, CommentHot3, CommentHot4, CommentHot5

class Command(BaseCommand):
    help = '执行各种统计分析'

    def handle(self, *args, **options):
        self.stdout.write('开始执行统计分析...')
        self.analyze_hot_boards()
        self.analyze_sentiment()
        self.analyze_ip()
        self.analyze_yuqing()
        self.analyze_hot_search_statistics()
        self.analyze_hot_data_statistics()
        self.stdout.write('统计分析完成！')

    def analyze_hot_boards(self):
        """分析热搜榜单"""
        self.stdout.write('\n=== 热搜榜单分析 ===')
        hot_boards = HotBoard.objects.all().order_by('rank')
        for board in hot_boards:
            self.stdout.write(f'排名 {board.rank}: {board.keyword} - 热度值: {board.hot_value} ({board.formatted_hot})')

    def analyze_sentiment(self):
        """分析热搜情感"""
        self.stdout.write('\n=== 热搜情感分析 ===')
        comment_models = [
            (CommentHot1, "热搜1"),
            (CommentHot2, "热搜2"),
            (CommentHot3, "热搜3"),
            (CommentHot4, "热搜4"),
            (CommentHot5, "热搜5")
        ]
        
        for model, name in comment_models:
            total = model.objects.count()
            positive = model.objects.filter(sentiment="正面").count()
            negative = model.objects.filter(sentiment="负面").count()
            neutral = model.objects.filter(sentiment="中性").count()
            
            self.stdout.write(f'\n{name}情感分布:')
            self.stdout.write(f'总评论数: {total}')
            self.stdout.write(f'正面: {positive} ({positive/total*100:.1f}%)')
            self.stdout.write(f'负面: {negative} ({negative/total*100:.1f}%)')
            self.stdout.write(f'中性: {neutral} ({neutral/total*100:.1f}%)')

    def analyze_ip(self):
        """分析IP地区分布"""
        self.stdout.write('\n=== IP分析 ===')
        comment_models = [CommentHot1, CommentHot2, CommentHot3, CommentHot4, CommentHot5]
        region_counts = {}
        
        for model in comment_models:
            comments = model.objects.exclude(region__isnull=True).exclude(region__exact='')
            for comment in comments:
                if comment.region in region_counts:
                    region_counts[comment.region] += 1
                else:
                    region_counts[comment.region] = 1
        
        # 按地区评论数排序
        sorted_regions = sorted(region_counts.items(), key=lambda x: x[1], reverse=True)
        self.stdout.write('地区评论数TOP10:')
        for region, count in sorted_regions[:10]:
            self.stdout.write(f'{region}: {count}条评论')

    def analyze_yuqing(self):
        """分析舆情"""
        self.stdout.write('\n=== 舆情分析 ===')
        # 计算每个热搜的评论数和情感倾向
        comment_models = [
            (CommentHot1, 1),
            (CommentHot2, 2),
            (CommentHot3, 3),
            (CommentHot4, 4),
            (CommentHot5, 5)
        ]
        
        for model, rank in comment_models:
            try:
                hot_board = HotBoard.objects.get(rank=rank)
                keyword = hot_board.keyword
                total = model.objects.count()
                positive = model.objects.filter(sentiment="正面").count()
                negative = model.objects.filter(sentiment="负面").count()
                
                # 计算情感倾向
                if positive > negative:
                    tendency = "正向"
                elif negative > positive:
                    tendency = "负向"
                else:
                    tendency = "中性"
                
                self.stdout.write(f'\n{keyword}舆情分析:')
                self.stdout.write(f'总评论数: {total}')
                self.stdout.write(f'情感倾向: {tendency}')
                self.stdout.write(f'正面评论: {positive} ({positive/total*100:.1f}%)')
                self.stdout.write(f'负面评论: {negative} ({negative/total*100:.1f}%)')
            except HotBoard.DoesNotExist:
                pass

    def analyze_hot_search_statistics(self):
        """分析热搜统计"""
        self.stdout.write('\n=== 热搜统计 ===')
        total_hot_searches = HotSearch.objects.count()
        total_hot_boards = HotBoard.objects.count()
        
        # 计算平均热度值
        hot_boards = HotBoard.objects.all()
        if hot_boards:
            avg_hot_value = sum(board.hot_value for board in hot_boards) / len(hot_boards)
            max_hot_board = hot_boards.order_by('-hot_value').first()
            min_hot_board = hot_boards.order_by('hot_value').first()
            
            self.stdout.write(f'总热搜关键词数: {total_hot_searches}')
            self.stdout.write(f'总热榜项数: {total_hot_boards}')
            self.stdout.write(f'平均热度值: {avg_hot_value:.0f}')
            self.stdout.write(f'最高热度: {max_hot_board.keyword} - {max_hot_board.hot_value}')
            self.stdout.write(f'最低热度: {min_hot_board.keyword} - {min_hot_board.hot_value}')

    def analyze_hot_data_statistics(self):
        """分析热搜数据统计"""
        self.stdout.write('\n=== 热搜数据统计 ===')
        # 计算各热度区间的热搜数量
        hot_boards = HotBoard.objects.all()
        ranges = [
            (0, 100000, "0-10万"),
            (100000, 200000, "10-20万"),
            (200000, 300000, "20-30万"),
            (300000, 400000, "30-40万"),
            (400000, 500000, "40-50万"),
            (500000, 999999999, "50万以上")
        ]
        
        for min_val, max_val, label in ranges:
            count = hot_boards.filter(hot_value__gte=min_val, hot_value__lt=max_val).count()
            self.stdout.write(f'{label}: {count}个热搜')