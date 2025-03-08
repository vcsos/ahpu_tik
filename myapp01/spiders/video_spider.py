import json

from DrissionPage import ChromiumPage
from datetime import datetime
from django.conf import settings
from myapp01.models import Video
import redis


def crawl_video_info():
    dp = ChromiumPage()
    dp.listen.start('aweme/detail/')
    dp.get('https://v.douyin.com/i5kcg41e/')
    r = redis.Redis(**settings.REDIS_CONFIG)

    try:
        resp = dp.listen.wait()
        json_data = resp.response.body

        if 'aweme_detail' in json_data:
            aweme_detail = json_data['aweme_detail']
            create_time = aweme_detail.get('create_time', 0)
            video_date = datetime.fromtimestamp(create_time)
            share_count = aweme_detail.get('statistics', {}).get('share_count', 0)
            popularity = "热门" if share_count >= 10000 else "正常"

            # 保存到 MySQL
            video = Video(
                caption=aweme_detail.get('desc', ''),
                video_date=video_date,
                video_id=aweme_detail.get('aweme_id', ''),
                user_name=aweme_detail.get('author', {}).get('nickname', ''),
                collect_count=aweme_detail.get('statistics', {}).get('collect_count', 0),
                share_count=share_count,
                popularity=popularity
            )
            video.save()

            # 保存到 Redis
            key = f'video:{video.id}'
            data = {
                'id': video.id,                                   # id
                'caption': video.caption,                         # 视频文案
                'date': video.video_date.isoformat(),             # 视频日期
                'video_id': video.video_id,                       # 视频ID
                'user': video.user_name,                          # 用户名称
                'collects': video.collect_count,                  # 收藏数
                'shares': video.share_count,                      # 转发数
                'popularity': video.popularity                    # 热门，正常
            }
            r.set(key, json.dumps(data, ensure_ascii=False))
    except Exception as e:
        print(f"处理视频数据失败: {e}")