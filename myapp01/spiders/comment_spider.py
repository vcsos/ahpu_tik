import json
from DrissionPage import ChromiumPage
from datetime import datetime
from django.conf import settings
from myapp01.models import Comment
import redis

def crawl_comments():
    dp = ChromiumPage()
    dp.listen.start('comment/list/')
    dp.get('https://v.douyin.com/i5kpQDRE/')
    r = redis.Redis(**settings.REDIS_CONFIG)

    for page in range(1, 21):
        resp = dp.listen.wait()
        json_data = resp.response.body
        comments = json_data['comments']

        with r.pipeline() as pipe:  # 通过 Redis 连接对象创建管道
            for index in comments:
                try:
                    create_time = index['create_time']
                    date = datetime.fromtimestamp(create_time)
                    ip_label = index.get('ip_label', '未知')

                    # 保存到 MySQL
                    comment = Comment(
                        nickname=index['user']['nickname'],
                        region=ip_label,
                        comment_date=date,
                        content=index['text'],
                        like_count=index['digg_count']
                    )
                    comment.save()

                    # 保存到 Redis
                    key = f'comment:{comment.id}'
                    data = {
                        'id': comment.id,
                        'nickname': comment.nickname,
                        'region': comment.region,
                        'date': date.isoformat(),
                        'content': comment.content,
                        'likes': comment.like_count
                    }
                    pipe.set(key, json.dumps(data, ensure_ascii=False))
                except Exception as e:
                    print(f"处理评论失败: {e}")
            pipe.execute()  # 批量提交

        next_page = dp.ele('css:.Rcc71LyU')
        dp.scroll.to_see(next_page)