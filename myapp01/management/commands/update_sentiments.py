from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm
from ml_utils.model_loader import SentimentAnalyzer
from myapp01.models import CommentHot1, CommentHot3, CommentHot2, CommentHot4, CommentHot5

class Command(BaseCommand):
    help = '批量更新评论情感分析结果'

    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=32)

    def handle(self, *args, **options):
        analyzer = SentimentAnalyzer()
        batch_size = options['batch_size']

        for model_class in [CommentHot1, CommentHot2, CommentHot3, CommentHot4, CommentHot5]:
            self.stdout.write(f"正在处理 {model_class.__name__}...")
            queryset = model_class.objects.filter(sentiment__isnull=True)
            total = queryset.count()
            self.stdout.write(f"待处理 {model_class.__name__} 记录数: {total}")  # 新增日志

            with tqdm(total=total, desc=f"Processing {model_class.__name__}") as pbar:
                for i in range(0, total, batch_size):
                    batch = list(queryset[i:i+batch_size])
                    texts = [obj.content for obj in batch]
                    results = []

                    for text in texts:
                        try:
                            results.append(analyzer.predict(text))
                        except Exception as e:
                            self.stderr.write(f"处理文本 '{text}' 时出错: {str(e)}")
                            results.append(None)  # 或根据业务逻辑设置默认标签

                    with transaction.atomic():
                        for obj, sentiment in zip(batch, results):
                            obj.sentiment = sentiment
                        model_class.objects.bulk_update(batch, ['sentiment'])  # 批量更新

                    pbar.update(len(batch))