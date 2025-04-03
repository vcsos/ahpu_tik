import datetime
import json
import redis
from DrissionPage._pages.chromium_page import ChromiumPage
from django.utils import timezone
from myapp01.models import CommentHot1, HotBoard  # 新增 HotBoard 导入

from Tik import settings


def crawl_comments_1():
    # 先删除数据库中原有数据
    CommentHot1.objects.all().delete()

    # 获取对应的热搜对象（假设热搜1的 rank=1）
    hot_board = HotBoard.objects.get(rank=1)  # 关键修改

    dp = ChromiumPage()
    dp.listen.start('comment/list/')
    dp.get('https://v.douyin.com/Vhn_KMcsAdU/')  # 热搜1
    r = redis.Redis(**settings.REDIS_CONFIG)

    # 删除 Redis 中原有数据
    keys = r.keys('comment1:*')
    if keys:
        r.delete(*keys)

    for page in range(1, 41):
        resp = dp.listen.wait()
        json_data = resp.response.body

        comments = json_data.get('comments', [])

        with r.pipeline() as pipe:
            for index in comments:
                try:
                    create_time = index.get('create_time')
                    if create_time:
                        naive_date = datetime.datetime.fromtimestamp(create_time)
                        date = timezone.make_aware(naive_date)
                    else:
                        date = None
                    ip_label = index.get('ip_label', '未知')

                    user_nickname = index.get('user', {}).get('nickname', '未知')
                    comment_text = index.get('text', '')
                    digg_count = index.get('digg_count', 0)

                    # 保存到 MySQL 并关联热搜
                    comment = CommentHot1(
                        nickname=user_nickname,
                        region=ip_label,
                        comment_date=date,
                        content=comment_text,
                        like_count=digg_count,
                        hot_board=hot_board  # 关键修改
                    )
                    comment.save()

                    # 保存到 Redis
                    key = f'comment1:{comment.id}'
                    data = {
                        'id': comment.id,
                        'nickname': user_nickname,
                        'region': ip_label,
                        'date': date.isoformat() if date else None,
                        'content': comment_text,
                        'likes': digg_count,
                        'hot_board_id': hot_board.rank
                    }
                    pipe.set(key, json.dumps(data, ensure_ascii=False))
                except Exception as e:
                    print(f"处理评论失败: {e}")
            pipe.execute()

        next_page = dp.ele('css:.LvAtyU_f')
        dp.scroll.to_see(next_page)
        try:
            next_page.click()
        except Exception as e:
            print(f"点击下一页失败: {e}")