import requests
import json
from datetime import datetime
from django.conf import settings
from myapp01.models import HotBoard
import redis


def crawl_hotboard():
    timestamp = int(datetime.now().timestamp() * 1000)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.douyin.com/hot',
    }
    url = f'https://www.douyin.com/aweme/v1/web/hot/search/list/?device_platform=webapp&aid=6383&channel=channel_pc_web&detail_list=1&source=6&pc_client_type=1&version_code=190500&ts={timestamp}'
    r = redis.Redis(**settings.REDIS_CONFIG)

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if data.get('status_code') == 0:
            word_list = data.get('data').get('word_list')
            for item in word_list:
                try:
                    # 保存到 MySQL
                    hot_item = HotBoard(
                        rank=item.get('position'),
                        keyword=item.get('word'),
                        hot_value=item.get('hot_value')
                    )
                    hot_item.save()

                    # 保存到 Redis
                    key = f'hotboard:{hot_item.id}'
                    data = {
                        'id': hot_item.id,                  # id
                        'rank': hot_item.rank,              # 排行
                        'keyword': hot_item.keyword,        # 关键词
                        'hot_value': hot_item.hot_value     # 热度值
                    }
                    r.set(key, json.dumps(data, ensure_ascii=False))
                except Exception as e:
                    print(f"处理热榜数据失败: {e}")
    except Exception as e:
        print(f"请求热榜失败: {e}")