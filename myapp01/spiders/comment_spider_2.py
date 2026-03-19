import datetime
import json
from DrissionPage._pages.chromium_page import ChromiumPage
from django.utils import timezone
from myapp01.models import CommentHot2, HotBoard  # 新增 HotBoard 导入
from Tik import settings


def crawl_comments_2():
    # 先删除数据库中原有数据
    CommentHot2.objects.all().delete()

    # 获取对应的热搜对象（假设热搜2的 rank=2）
    try:
        hot_board = HotBoard.objects.get(rank=2)  # 关键修改
    except HotBoard.DoesNotExist:
        print("热搜2的记录不存在，无法关联评论数据")
        return

    dp = ChromiumPage()
    dp.listen.start('comment/list/')
    dp.get('https://v.douyin.com/pcTo7BlsuZ0/')  # 热搜2

    for page in range(1, 31):
        resp = dp.listen.wait()
        json_data = resp.response.body
        if isinstance(json_data, dict):
            # 如果已经是字典，直接使用
            json_dict = json_data
        else:
            try:
                # 将字符串解析为字典
                json_dict = json.loads(json_data)
            except json.JSONDecodeError:
                print("JSON 解析失败，请检查数据格式")
                continue

        comments = json_dict.get('comments', [])

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
                comment = CommentHot2(
                    nickname=user_nickname,
                    region=ip_label,
                    comment_date=date,
                    content=comment_text,
                    like_count=digg_count,
                    hot_board=hot_board
                )
                comment.save()
            except Exception as e:
                print(f"处理评论失败: {e}")

        next_page = dp.ele('css:.HV3aiR5J')
        dp.scroll.to_see(next_page)
        try:
            next_page.click()
        except Exception as e:
            print(f"点击下一页失败: {e}")