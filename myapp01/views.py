import random
from collections import defaultdict
import pandas as pd
from django.core.cache import cache
from django.shortcuts import render, redirect, HttpResponse
import re
from django.http import JsonResponse
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
import json
import redis
from django.shortcuts import render
from .models import HotBoard, CommentHot1, CommentHot2, CommentHot3, CommentHot4, CommentHot5, RegisterUser
from .serializers import HotBoardSerializer
from django.db import connection
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import os
from celery import shared_task

redis_conn = redis.Redis(host='localhost', port=6379, db=0)
redis_client = redis.Redis(host='localhost', port=6379, db=0)


# 注册页面
def register(request):
    if request.method == 'GET':
        return render(request, 'register.html')
    else:
        email = request.POST.get("email")
        password = request.POST.get("pwd")

        if not all([email, password]):
            return render(request, 'register.html', {"errmsg": "数据不完整"})
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {"msg": '邮箱格式不正确'})
        if len(password) < 9:
            return render(request, 'register.html', {"emsg": "密码长度必须为 9 位以上"})

        user = RegisterUser()
        user.reg_mail = email
        user.reg_pwd = password
        user.save()
        return render(request, 'login.html')


def login(request):
    if request.method == 'GET':
        return render(request, 'login.html')
    else:
        email = request.POST.get("email")
        password = request.POST.get("pwd")

        if not all([email, password]):
            return render(request, 'login.html', {"msg1": "数据不完整"})

        user = RegisterUser.objects.filter(reg_mail=email).first()
        if not user:
            return render(request, 'login.html', {'msg2': "用户不存在", })
        if password != user.reg_pwd:
            return render(request, 'login.html', {"msg3": "密码错误", "email": email})
        return render(request, 'index.html')


def index(request):
    # 最高评论点赞数（从MySQL）
    max_comment_cache_key = 'max_comment_like_count'
    max_comment = cache.get(max_comment_cache_key)
    if not max_comment:
        max_comment = CommentHot1.objects.order_by('-like_count').first()
        cache.set(max_comment_cache_key, max_comment, 3600)
    max_like_count = max_comment.like_count if max_comment else 0

    # 最高收藏数（从Redis video）
    max_collects_cache_key = 'max_collects'
    max_collects = cache.get(max_collects_cache_key)
    if not max_collects:
        max_collects = 0
        video_keys = redis_conn.keys('video:*')
        latest_videos = []
        for key in video_keys:
            video_data = json.loads(redis_conn.get(key))
            if video_data.get('collects', 0) > max_collects:
                max_collects = video_data['collects']
            # 收集最新舆情数据
            if len(latest_videos) < 5:
                latest_videos.append({
                    'caption': video_data['caption'],
                    'video_id': video_data['video_id'],
                    'user': video_data['user'],
                    'collects': video_data.get('collects'),
                    'shares': video_data.get('shares', 0),
                    'popularity': video_data['popularity']
                })
        cache.set(max_collects_cache_key, max_collects, 3600)

    # 最高热度值 & 热搜数据（从Redis hotboard）
    max_hot_value_cache_key = 'max_hot_value'
    max_hot_value = cache.get(max_hot_value_cache_key)
    hotboards = []
    if not max_hot_value:
        max_hot_value = 0
        hotboard_keys = redis_conn.keys('hotboard:*')
        for key in hotboard_keys:
            board_data = json.loads(redis_conn.get(key))
            hotboards.append(board_data)
            if board_data['hot_value'] > max_hot_value:
                max_hot_value = board_data['hot_value']
        cache.set(max_hot_value_cache_key, max_hot_value, 3600)

    # 最高分享数（从Redis video中找最高shares）
    max_shares_cache_key = 'max_shares'
    max_shares = cache.get(max_shares_cache_key)
    if not max_shares:
        max_shares = max([video.get('shares', 0) for video in
                          [json.loads(redis_conn.get(k)) for k in video_keys]], default=0)
        cache.set(max_shares_cache_key, max_shares, 3600)

    current_hot_board_id = None
    if hotboards:
        current_hot_board_id = hotboards[0].get('id')  # 假设 Redis 热榜数据包含 id 字段

    context = {
        'max_like_count': max_like_count,
        'max_collects': max_collects,
        'max_hot_value': max_hot_value,
        'max_shares': max_shares,
        'latest_videos': latest_videos,
        'hotboards_json': json.dumps(hotboards),
        'current_hot_board_id': current_hot_board_id  # 新增传递热榜 ID
    }
    return render(request, "index.html", context)


def layout(request):
    return render(request, "layout.html")


def information(request):
    return render(request, "information.html")


def saying(request):
    return render(request, "saying.html")


def ip(request):
    return render(request, "ip.html")


def soso(request):
    return render(request, "soso.html")


# --------------------------评论数据---------------------------------------
def hotlist(request):
    # 获取按排名升序排列的热榜数据
    hot_items_cache_key = 'hot_items'
    hot_items = cache.get(hot_items_cache_key)
    if not hot_items:
        hot_items = HotBoard.objects.all().order_by('rank')
        cache.set(hot_items_cache_key, hot_items, 3600)

    # 获取最新更新时间（取最新创建的记录时间）
    update_time_cache_key = 'hot_update_time'
    update_time = cache.get(update_time_cache_key)
    if not update_time:
        update_time = HotBoard.objects.order_by('-created_at').first().created_at if hot_items.exists() else None
        cache.set(update_time_cache_key, update_time, 3600)

    return render(request, 'hot.html', {
        'hot_items': hot_items,
        'update_time': update_time
    })


class HotBoardListView(APIView):
    def get(self, request):
        # 按rank升序排列（1-5）
        hot_boards_cache_key = 'hot_boards_1_5'
        hot_boards = cache.get(hot_boards_cache_key)
        if not hot_boards:
            hot_boards = HotBoard.objects.filter(rank__lte=5).order_by('rank')
            cache.set(hot_boards_cache_key, hot_boards, 3600)
        serializer = HotBoardSerializer(hot_boards, many=True)
        return Response(serializer.data)


def get_comments(request):
    hot_id = request.GET.get('hotId')
    if not hot_id:
        return JsonResponse({'error': '缺少hotId参数'}, status=400)

    try:
        hot_board = HotBoard.objects.get(id=hot_id)
    except HotBoard.DoesNotExist:
        return JsonResponse({'error': '未找到指定热榜'}, status=404)

    # 根据rank动态选择评论模型
    rank = hot_board.rank
    comment_model_mapping = {
        1: CommentHot1,
        2: CommentHot2,
        3: CommentHot3,
        4: CommentHot4,
        5: CommentHot5,
    }

    if rank not in comment_model_mapping:
        return JsonResponse({'error': '无效的排名'}, status=400)

    CommentModel = comment_model_mapping[rank]
    comments_cache_key = f'comments_{hot_id}'
    comments = cache.get(comments_cache_key)
    if not comments:
        comments = CommentModel.objects.filter(hot_board=hot_board)
        cache.set(comments_cache_key, comments, 3600)

    # 序列化评论数据
    data = [{
        "nickname": c.nickname,
        "region": c.region,
        "date": c.comment_date.isoformat(),
        "content": c.content,
        "likes": c.like_count,
    } for c in comments]

    return JsonResponse(data, safe=False)


# --------------------------评论数据----------------------------------------


def normalize_region(region):
    """统一地区名称格式"""
    replacements = ['省', '市', '自治区', '特别行政区']
    for rep in replacements:
        region = region.replace(rep, '')
    return region


def get_region_distribution(request):
    hot_search_id = request.GET.get('hot_search_id')
    if not hot_search_id:
        return JsonResponse({'error': '缺少hot_search_id参数'}, status=400)

    # 缓存检查
    cache_key = f"region_{hot_search_id}"
    if cached := cache.get(cache_key):
        return JsonResponse(cached)

    try:
        hot_board = HotBoard.objects.get(id=hot_search_id)
    except HotBoard.DoesNotExist:
        return JsonResponse({'error': '无效的热搜ID'}, status=404)

    # 动态选择评论模型
    comment_model_mapping = {
        1: CommentHot1,
        2: CommentHot2,
        3: CommentHot3,
        4: CommentHot4,
        5: CommentHot5,
    }
    CommentModel = comment_model_mapping.get(hot_board.rank)
    if not CommentModel:
        return JsonResponse({'error': '无效的排名'}, status=400)

    # 统计地区数据
    regions_cache_key = f'regions_{hot_search_id}'
    regions = cache.get(regions_cache_key)
    if not regions:
        regions = CommentModel.objects.filter(hot_board_id=hot_search_id) \
            .values_list('region', flat=True)
        cache.set(regions_cache_key, regions, 3600)

    # 处理统计结果
    region_counts = defaultdict(int)
    for r in regions:
        normalized = normalize_region(r)
        region_counts[normalized] += 1

    # 生成图表数据
    sorted_regions = sorted(region_counts.items(), key=lambda x: -x[1])
    top10 = sorted_regions[:10]  # 取前10个地区

    result = {
        'regions': [r[0] for r in top10],  # 仅前10地区
        'values': [r[1] for r in top10],  # 对应数值
        'map_data': dict(sorted_regions)  # 地图仍显示全部数据
    }
    # 缓存1小时
    cache.set(cache_key, result, 3600)
    return JsonResponse(result)


# ----------------------------------------以上IP分析--------------------------------------------------------


def get_comment_table(rank):
    COMMENT_MODELS = {
        1: 'myapp01_commenthot1_processed',
        2: 'myapp01_commenthot2_processed',
        3: 'myapp01_commenthot3_processed',
        4: 'myapp01_commenthot4_processed',
        5: 'myapp01_commenthot5_processed',
    }
    return COMMENT_MODELS.get(rank)


def load_stopwords():
    try:
        current_dir = os.path.dirname(__file__)
        stopwords_path = os.path.join(current_dir, 'stopwords.txt')
        with open(stopwords_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []


def get_comment_texts(table_name, hot_board_id):
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT 分词 
            FROM {table_name}
            WHERE hot_board_id = %s
        """, [hot_board_id])
        return [row[0] for row in cursor.fetchall() if row[0].strip()]


@shared_task
def hot_data_analysis_task(hot_board_id):
    try:
        hot_board = HotBoard.objects.get(id=hot_board_id)
    except HotBoard.DoesNotExist:
        return {'error': 'Invalid hot_board_id'}

    table_name = get_comment_table(hot_board.rank)
    if not table_name:
        return {'error': 'Invalid rank'}

    stop_words = load_stopwords()

    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT `time`, like_count, 分词, 年月日 
            FROM {table_name}
            WHERE hot_board_id = %s
        """, [hot_board_id])
        rows = cursor.fetchall()

    time_dist = defaultdict(int)
    like_ranges = {'0-100': 0, '100-500': 0, '500-1000': 0, '1000-2000': 0, '2000+': 0}
    word_freq = defaultdict(int)

    for row in rows:
        hour = row[0].split(':')[0]
        time_dist[f"{hour}:00"] += 1

        likes = row[1]
        if likes <= 100:
            like_ranges['0-100'] += 1
        elif likes <= 500:
            like_ranges['100-500'] += 1
        elif likes <= 1000:
            like_ranges['500-1000'] += 1
        elif likes <= 2000:
            like_ranges['1000-2000'] += 1
        else:
            like_ranges['2000+'] += 1

        words = row[2].split()
        for word in words:
            word_freq[word] += 1

    documents = [' '.join(row[2].split()) for row in rows if row[2].strip()]

    if not documents:
        return {'error': '无有效文本数据'}

    vectorizer = TfidfVectorizer(
        max_features=1000,
        stop_words=stop_words
    )
    try:
        tfidf_matrix = vectorizer.fit_transform(documents)
    except ValueError:
        return {'error': '文本数据不足以生成特征'}

    n_clusters = 10
    try:
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        kmeans.fit(tfidf_matrix)
    except Exception as e:
        return {'error': f'聚类分析失败: {str(e)}'}

    terms = vectorizer.get_feature_names_out()
    cluster_keywords = []

    for i in range(n_clusters):
        centroid_weights = kmeans.cluster_centers_[i].argsort()[::-1]
        top_keywords = [terms[index] for index in centroid_weights[:3]]
        cluster_keywords.extend(top_keywords)

    candidates = [
        (word, word_freq[word])
        for word in set(cluster_keywords)
        if word in word_freq
    ]

    if not candidates:
        return {'error': '无有效候选热词'}

    sorted_words = sorted(candidates, key=lambda x: -x[1])[:10]
    word_words = sorted(candidates, key=lambda x: -x[1])[:100]

    top_words = [w[0] for w in sorted_words]
    word_counts = [w[1] for w in sorted_words]
    wordcloud_data = [{'name': w[0], 'value': w[1]} for w in word_words]

    result = {
        'time': {
            'xAxis': sorted(time_dist.keys()),
            'data': [time_dist[k] for k in sorted(time_dist.keys())]
        },
        'likes': {
            'categories': list(like_ranges.keys()),
            'data': list(like_ranges.values())
        },
        'words': {
            'top_words': top_words,
            'word_counts': word_counts,
            'wordcloud': wordcloud_data
        }
    }

    cache.set(f"hot_analysis_{hot_board_id}", result, timeout=3600)
    return result


def hot_data_analysis(request):
    hot_board_id = request.GET.get('hot_board_id')
    if not hot_board_id:
        return JsonResponse({'error': 'Missing hot_board_id'}, status=400)

    cache_key = f"hot_analysis_{hot_board_id}"
    if cached := cache.get(cache_key):
        return JsonResponse(cached)

    # 异步执行任务
    task = hot_data_analysis_task.delay(hot_board_id)
    return JsonResponse({'task_id': task.id}, status=202)


def get_cluster_data(request):
    hot_board_id = request.GET.get('hot_board_id')
    cache_key = f"cluster_data_{hot_board_id}"

    if cached := cache.get(cache_key):
        return JsonResponse(cached, safe=False)

    try:
        # 复用现有分析逻辑
        hot_board = HotBoard.objects.get(id=hot_board_id)
        table_name = get_comment_table(hot_board.rank)
        stop_words = load_stopwords()
        documents = get_comment_texts(table_name, hot_board_id)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    if not documents:
        return JsonResponse({'error': 'No valid comments'}, status=400)

    # 执行聚类和降维
    vectorizer = TfidfVectorizer(max_features=1000, stop_words=stop_words)
    tfidf_matrix = vectorizer.fit_transform(documents)
    kmeans = KMeans(n_clusters=10, random_state=42)
    labels = kmeans.fit_predict(tfidf_matrix)
    pca = PCA(n_components=2)
    pca_result = pca.fit_transform(tfidf_matrix.toarray())

    # 构建数据格式
    data = []
    for i, (x, y) in enumerate(pca_result):
        data.append({
            'x': float(x),
            'y': float(y),
            'label': int(labels[i]),
            'text': documents[i]
        })

    cache.set(cache_key, data, timeout=3600)
    return JsonResponse(data, safe=False)


def sentiment_analysis(request):
    # 模拟情感分析数据
    positive = random.randint(10, 100)
    negative = random.randint(10, 100)
    neutral = random.randint(10, 100)
    data = {
        "positive": positive,
        "negative": negative,
        "neutral": neutral
    }
    return JsonResponse(data)