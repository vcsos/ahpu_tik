import datetime
import json
import redis
from DrissionPage._pages.chromium_page import ChromiumPage
from django.utils import timezone
from myapp01.models import CommentHot4, HotBoard  # 新增 HotBoard 导入
from Tik import settings


def process_comment(comment_data, model, r, hot_board):  # 新增 hot_board 参数
    try:
        create_time = comment_data.get('create_time')
        if create_time:
            naive_date = datetime.datetime.fromtimestamp(create_time)
            date = timezone.make_aware(naive_date, timezone=timezone.get_default_timezone())
        else:
            date = None
        ip_label = comment_data.get('ip_label', '未知')

        user_nickname = comment_data.get('user', {}).get('nickname', '未知')
        comment_text = comment_data.get('text', '')
        digg_count = comment_data.get('digg_count', 0)

        # 保存到 MySQL 并关联热搜
        comment = model(
            nickname=user_nickname,
            region=ip_label,
            comment_date=date,
            content=comment_text,
            like_count=digg_count,
            hot_board=hot_board  # 关键修改
        )
        comment.save()

        # 保存到 Redis（可选：根据接口要求调整键名）
        key = f'comment4:{comment.id}'  # 保持与接口缓存键一致
        data = {
            'id': comment.id,
            'nickname': user_nickname,
            'region': ip_label,
            'date': date.isoformat() if date else None,
            'content': comment_text,
            'likes': digg_count,
            'hot_board_id': hot_board.rank
        }
        r.set(key, json.dumps(data, ensure_ascii=False))
    except json.JSONDecodeError as e:
        print(f"解析评论数据失败: {e}")
    except KeyError as e:
        print(f"评论数据中缺少必要的键: {e}")
    except Exception as e:
        print(f"处理评论失败: {e}")


def crawl_comments_4():
    try:
        CommentHot4.objects.all().delete()

        # 获取对应的热搜对象（假设热搜4的 rank=4）
        try:
            hot_board = HotBoard.objects.get(rank=4)  # 关键修改
        except HotBoard.DoesNotExist:
            print("热搜4的记录不存在，无法关联评论数据")
            return

        dp = ChromiumPage()
        dp.listen.start('comment/list/')
        dp.get('https://v.douyin.com/KZyqDbjcc3Q/')  # 热搜4
        r = redis.Redis(**settings.REDIS_CONFIG)

        # 删除 Redis 中原有数据
        keys = r.keys('comment4:*')
        if keys:
            r.delete(*keys)

        for page in range(1, 41):
            try:
                resp = dp.listen.wait()
                json_data = resp.response.body

                comments = json_data.get('comments', [])

                with r.pipeline() as pipe:
                    for index in comments:
                        process_comment(index, CommentHot4, r, hot_board)  # 传递 hot_board
                    pipe.execute()

                next_page = dp.ele('css:.HV3aiR5J')
                dp.scroll.to_see(next_page)
                try:
                    next_page.click()
                except Exception as e:
                    print(f"点击下一页失败: {e}")
            except Exception as e:
                print(f"处理页面 {page} 失败: {e}")
    except Exception as e:
        print(f"初始化浏览器或 Redis 连接失败: {e}")