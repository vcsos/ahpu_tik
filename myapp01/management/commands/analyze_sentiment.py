import os
import json
from django.core.management.base import BaseCommand
from myapp01.models import CommentHot1, CommentHot2, CommentHot3, CommentHot4, CommentHot5

class Command(BaseCommand):
    help = '对评论数据进行情感分析'

    def handle(self, *args, **options):
        self.stdout.write('开始情感分析...')
        # 模拟情感分析，实际项目中可以使用真实的NLP模型
        self.analyze_comments()
        self.stdout.write('情感分析完成！')

    def analyze_comments(self):
        """对所有评论进行情感分析"""
        comment_models = [CommentHot1, CommentHot2, CommentHot3, CommentHot4, CommentHot5]
        sentiments = ["正面", "负面", "中性"]
        
        for model in comment_models:
            comments = model.objects.all()
            for comment in comments:
                # 简单的情感分析逻辑，实际项目中可以使用更复杂的模型
                # 这里根据评论长度和内容简单判断
                content_length = len(comment.content)
                if content_length > 50:
                    sentiment = "正面"
                elif content_length < 20:
                    sentiment = "负面"
                else:
                    sentiment = "中性"
                
                comment.sentiment = sentiment
                comment.save()
            
            self.stdout.write(f'完成{model._meta.verbose_name}的情感分析，共处理{comments.count()}条评论')