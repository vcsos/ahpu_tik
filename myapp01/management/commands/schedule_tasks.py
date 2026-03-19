import schedule
import time
import logging
from django.core.management.base import BaseCommand
from myapp01.spiders.hotboard_spider import HotBoardSpider
from myapp01.spiders.comment_spider_1 import CommentSpider1
from myapp01.spiders.comment_spider_2 import CommentSpider2
from myapp01.spiders.comment_spider_3 import CommentSpider3
from myapp01.spiders.comment_spider_4 import CommentSpider4
from myapp01.spiders.comment_spider_5 import CommentSpider5
from myapp01.spiders.video_spider_1 import VideoSpider
from myapp01.management.commands.analyze_sentiment import Command as SentimentCommand

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawl.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('schedule_tasks')

class Command(BaseCommand):
    help = '启动定时任务，自动采集数据和分析'

    def handle(self, *args, **kwargs):
        logger.info('启动定时任务系统')
        
        # 立即执行一次初始化采集
        self.run_initial_crawl()
        
        # 设置定时任务
        schedule.every(6).hours.do(self.crawl_all_data)
        schedule.every(12).hours.do(self.analyze_all_sentiment)
        
        # 启动调度循环
        logger.info('定时任务已设置，每6小时采集一次数据，每12小时分析一次情感')
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    def run_initial_crawl(self):
        """初始采集数据"""
        logger.info('执行初始数据采集')
        self.crawl_all_data()
        self.analyze_all_sentiment()
    
    def crawl_all_data(self):
        """采集所有数据"""
        logger.info('开始采集热榜数据')
        try:
            # 采集热榜
            hotboard_spider = HotBoardSpider()
            hotboard_spider.crawl()
            logger.info('热榜数据采集完成')
            
            # 采集评论
            comment_spiders = [
                CommentSpider1(),
                CommentSpider2(),
                CommentSpider3(),
                CommentSpider4(),
                CommentSpider5()
            ]
            
            for i, spider in enumerate(comment_spiders, 1):
                logger.info(f'开始采集热搜{i}的评论数据')
                spider.crawl()
                logger.info(f'热搜{i}评论数据采集完成')
            
            # 采集视频
            logger.info('开始采集视频数据')
            video_spider = VideoSpider()
            video_spider.crawl()
            logger.info('视频数据采集完成')
            
        except Exception as e:
            logger.error(f'数据采集失败: {str(e)}')
    
    def analyze_all_sentiment(self):
        """分析所有情感数据"""
        logger.info('开始情感分析')
        try:
            sentiment_command = SentimentCommand()
            sentiment_command.handle()
            logger.info('情感分析完成')
        except Exception as e:
            logger.error(f'情感分析失败: {str(e)}')
