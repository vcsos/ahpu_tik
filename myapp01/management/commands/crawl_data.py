from django.core.management.base import BaseCommand
from myapp01.spiders.comment_spider import crawl_comments
from myapp01.spiders.hotboard_spider import crawl_hotboard
from myapp01.spiders.video_spider import crawl_video_info

class Command(BaseCommand):
    help = 'Run all crawlers'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to crawl data...'))
        crawl_comments()
        crawl_hotboard()
        crawl_video_info()
        self.stdout.write(self.style.SUCCESS('Data crawling completed.'))