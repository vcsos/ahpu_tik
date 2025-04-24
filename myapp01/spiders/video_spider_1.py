import json
import logging
from DrissionPage import ChromiumPage
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from myapp01.models import Video
import redis

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def update_video_info(video, aweme_detail, share_count, popularity):
    video.caption = aweme_detail.get('desc', '')
    create_time = aweme_detail.get('create_time', 0)
    video_date = timezone.make_aware(datetime.fromtimestamp(create_time), timezone.get_default_timezone())
    video.video_date = video_date
    video.user_name = aweme_detail.get('author', {}).get('nickname', '')
    video.collect_count = aweme_detail.get('statistics', {}).get('collect_count', 0)
    video.share_count = share_count
    video.popularity = popularity
    video.save()
    return video

def extract_aweme_detail(resp):
    try:
        if isinstance(resp.response.body, bytes):
            json_str = resp.response.body.decode('utf-8')
            json_data = json.loads(json_str)
        elif isinstance(resp.response.body, dict):
            json_data = resp.response.body
        else:
            logging.error("响应内容类型不支持")
            return None
        return json_data.get('aweme_detail')
    except UnicodeDecodeError:
        logging.error("响应内容解码失败")
    except json.JSONDecodeError:
        logging.error("JSON解析失败")
    return None


def process_single_video(dp, video_url, r):
    """
    处理单个视频的信息
    :param dp: 浏览器页面对象
    :param video_url: 视频URL
    :param r: Redis连接对象
    """
    try:
        tab = dp.new_tab()
        tab.listen.start('aweme/detail/')
        tab.get(video_url)

        try:
            resp = tab.listen.wait()
            aweme_detail = extract_aweme_detail(resp)

            if aweme_detail:
                share_count = aweme_detail.get('statistics', {}).get('share_count', 0)
                popularity = "热门" if share_count >= 10000 else "正常"
                video_id = aweme_detail.get('aweme_id', '')

                video, created = Video.objects.get_or_create(
                    video_id=video_id,
                    defaults={
                        'caption': aweme_detail.get('desc', ''),
                        'video_date': timezone.make_aware(
                            datetime.fromtimestamp(aweme_detail.get('create_time', 0)),
                            timezone.get_default_timezone()
                        ),
                        'user_name': aweme_detail.get('author', {}).get('nickname', ''),
                        'collect_count': aweme_detail.get('statistics', {}).get('collect_count', 0),
                        'share_count': share_count,
                        'popularity': popularity
                    }
                )

                if not created:
                    video = update_video_info(video, aweme_detail, share_count, popularity)

                # 存储到Redis
                key = f'video:{video.id}'
                data = {
                    'id': video.id,
                    'caption': video.caption,
                    'date': video.video_date.isoformat(),
                    'video_id': video.video_id,
                    'user': video.user_name,
                    'collects': video.collect_count,
                    'shares': video.share_count,
                    'popularity': video.popularity
                }
                r.set(key, json.dumps(data, ensure_ascii=False))
                logging.info(f"成功处理视频：{video_url}")
            else:
                logging.warning(f"视频数据异常：{video_url}")

        except Exception as e:
            logging.error(f"处理响应失败：{str(e)}")

    except Exception as e:
        logging.error(f"初始化标签页失败：{str(e)}")
    finally:
        try:
            tab.close()
        except NameError:
            pass


def crawl_multiple_videos():
    """
    处理多个视频的信息
    """
    # 配置视频URL列表（示例）
    video_urls = [
        'https://v.douyin.com/Vhn_KMcsAdU',
        'https://v.douyin.com/pcTo7BlsuZ0/',
        'https://v.douyin.com/HsEe-zPacTA/',
        'https://v.douyin.com/KZyqDbjcc3Q/',
        'https://v.douyin.com/x101CtUbblg/',
    ]

    dp = ChromiumPage()
    r = redis.Redis(**settings.REDIS_CONFIG)

    try:
        # 删除 MySQL 数据库中的数据
        Video.objects.all().delete()
        logging.info("已删除 MySQL 数据库中的视频数据")

        # 删除 Redis 中的数据
        keys = r.keys('video:*')
        if keys:
            r.delete(*keys)
            logging.info("已删除 Redis 中的视频数据")

        for url in video_urls:
            logging.info(f"正在处理视频：{url}")
            process_single_video(dp, url, r)
    except Exception as e:
        logging.error(f"爬虫运行异常：{str(e)}")
    finally:
        try:
            dp.quit()
        except AttributeError:
            pass
        logging.info("所有视频处理完成")


if __name__ == "__main__":
    crawl_multiple_videos()
