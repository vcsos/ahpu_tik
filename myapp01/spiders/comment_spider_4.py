import datetime
import json
from DrissionPage._pages.chromium_page import ChromiumPage
from django.utils import timezone
from myapp01.models import CommentHot4, HotBoard  # 新增 HotBoard 导入
from Tik import settings


def process_comment(comment_data, model, hot_board):
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
            hot_board=hot_board
        )
        comment.save()

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
            hot_board = HotBoard.objects.get(rank=4)
        except HotBoard.DoesNotExist:
            print("热搜4的记录不存在，无法关联评论数据")
            return

        dp = ChromiumPage()
        dp.listen.start('comment/list/')
        dp.get('https://v.douyin.com/KZyqDbjcc3Q/')  # 热搜4

        for page in range(1, 41):
            try:
                resp = dp.listen.wait()
                json_data = resp.response.body

                try:
                    json_obj = json.loads(json_data)
                    comments = json_obj.get('comments', [])
                except json.JSONDecodeError:
                    print("JSON 解析失败，请检查数据格式")
                    continue

                for index in comments:
                    process_comment(index, CommentHot4, hot_board)

                next_page = dp.ele('css:.HV3aiR5J')
                dp.scroll.to_see(next_page)
                try:
                    next_page.click()
                except Exception as e:
                    print(f"点击下一页失败: {e}")
            except Exception as e:
                print(f"处理页面 {page} 失败: {e}")
    except Exception as e:
        print(f"初始化浏览器连接失败: {e}")