import requests
import json
import logging
from datetime import datetime
from django.conf import settings
from myapp01.models import HotBoard, HotSearch
import redis

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def crawl_hotboard():
    try:
        # 删除数据库中原来的热榜数据
        HotBoard.objects.all().delete()

        # 连接 Redis
        r = redis.Redis(**settings.REDIS_CONFIG)
        # 删除 Redis 中原来的热榜数据
        keys = r.keys('hotboard:*')
        if keys:
            r.delete(*keys)

        # 获取当前时间戳
        timestamp = int(datetime.now().timestamp() * 1000)
        # 设置请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.douyin.com/hot',
        }
        # 构建请求 URL
        url = f'https://www.douyin.com/aweme/v1/web/hot/search/list/?device_platform=webapp&aid=6383&channel=channel_pc_web&detail_list=1&source=6&pc_client_type=1&version_code=190500&ts={timestamp}'

        # 发送请求
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        # 解析响应 JSON 数据
        data = response.json()

        if data.get('status_code') == 0:
            word_list = data.get('data', {}).get('word_list', [])
            for item in word_list:
                try:
                    # 获取或创建 HotSearch 实例
                    hot_search, _ = HotSearch.objects.get_or_create(keyword=item.get('word'))

                    # 保存到 MySQL
                    hot_item = HotBoard(
                        rank=item.get('position'),
                        keyword=item.get('word'),
                        hot_value=item.get('hot_value'),
                        hot_search=hot_search  # 关联到 HotSearch 实例
                    )
                    hot_item.save()
                    logging.info(f"成功保存热榜数据到 MySQL: {hot_item.keyword}")

                    # 保存到 Redis
                    key = f'hotboard:{hot_item.id}'
                    redis_data = {
                        'id': hot_item.id,
                        'rank': hot_item.rank,
                        'keyword': hot_item.keyword,
                        'hot_value': hot_item.hot_value
                    }
                    r.set(key, json.dumps(redis_data, ensure_ascii=False))
                    logging.info(f"成功保存热榜数据到 Redis: {hot_item.keyword}")
                except Exception as e:
                    logging.error(f"处理热榜数据失败: {e}", exc_info=True)
        else:
            logging.error(f"请求返回的状态码不为 0: {data.get('status_code')}")
    except requests.RequestException as e:
        logging.error(f"请求热榜失败: {e}", exc_info=True)
    except json.JSONDecodeError as e:
        logging.error(f"解析响应 JSON 数据失败: {e}", exc_info=True)
    except Exception as e:
        logging.error(f"发生未知错误: {e}", exc_info=True)
