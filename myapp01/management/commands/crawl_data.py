from django.core.management.base import BaseCommand

from myapp01 import data_processor
from myapp01.spiders import (
    crawl_comments_1, crawl_comments_2, crawl_comments_3,
    crawl_comments_4, crawl_comments_5, crawl_hotboard, crawl_multiple_videos
)
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run all crawlers'

    # 定义一个包含所有爬虫函数的列表
    CRAWLERS = [
        crawl_hotboard,
        crawl_multiple_videos,
        crawl_comments_1,
        crawl_comments_2,
        crawl_comments_3,
        crawl_comments_4,
        crawl_comments_5,
        data_processor,
    ]

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to crawl data...'))
        for crawler in self.CRAWLERS:
            try:
                # 尝试执行每个爬虫函数
                crawler()
                logger.info(f'{crawler.__name__} 爬取完成.')
            except Exception as e:
                # 捕获并记录异常信息
                logger.error(f'Error occurred while running {crawler.__name__}: {e}')
                self.stdout.write(self.style.ERROR(f'Error in {crawler.__name__}: {e}'))
        self.stdout.write(self.style.SUCCESS('数据爬取完成.'))