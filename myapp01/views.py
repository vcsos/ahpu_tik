import random
from collections import defaultdict
import pandas as pd
from django.core.cache import cache
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
import re
from django.http import JsonResponse
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
import json
import redis
from django.shortcuts import render
from Tik import settings
from .models import HotBoard, CommentHot1, CommentHot2, CommentHot3, CommentHot4, CommentHot5, RegisterUser
from .serializers import HotBoardSerializer
from django.db import connection
from collections import defaultdict


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


redis_conn = redis.Redis(host='localhost', port=6379, db=0)
import json
import redis
from django.shortcuts import render
from django.db.models import Count

# Redis配置
redis_client = redis.Redis(host='localhost', port=6379, db=0)


def index(request):
    # 最高评论点赞数（从MySQL）
    max_comment = CommentHot1.objects.order_by('-like_count').first()
    max_like_count = max_comment.like_count if max_comment else 0

    # 最高收藏数（从Redis video）
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

    # 最高热度值 & 热搜数据（从Redis hotboard）
    max_hot_value = 0
    hotboards = []
    hotboard_keys = redis_conn.keys('hotboard:*')
    for key in hotboard_keys:
        board_data = json.loads(redis_conn.get(key))
        hotboards.append(board_data)
        if board_data['hot_value'] > max_hot_value:
            max_hot_value = board_data['hot_value']

    # 最高分享数（从Redis video中找最高shares）
    max_shares = max([video.get('shares', 0) for video in
                      [json.loads(redis_conn.get(k)) for k in video_keys]], default=0)

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
    hot_items = HotBoard.objects.all().order_by('rank')

    # 获取最新更新时间（取最新创建的记录时间）
    update_time = HotBoard.objects.order_by('-created_at').first().created_at if hot_items.exists() else None

    return render(request, 'hot.html', {
        'hot_items': hot_items,
        'update_time': update_time
    })


class HotBoardListView(APIView):
    def get(self, request):
        # 按rank升序排列（1-5）
        hot_boards = HotBoard.objects.filter(rank__lte=5).order_by('rank')
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
    comments = CommentModel.objects.filter(hot_board=hot_board)

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

    # 获取热搜对象
    hot_board = get_object_or_404(HotBoard, id=hot_search_id)

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

    # 统计地区数据并标准化名称
    regions = CommentModel.objects.filter(hot_board_id=hot_search_id) \
        .values_list('region', flat=True) \
        .exclude(region__isnull=True)  # 排除空值

    region_counts = defaultdict(int)
    for r in regions:
        if not r:  # 跳过空字符串
            continue
        normalized = normalize_region(r)
        region_counts[normalized] += 1

    # 生成图表数据（保持地图显示全部数据，柱状图/饼图显示TOP10）
    sorted_regions = sorted(region_counts.items(), key=lambda x: -x[1])
    top10 = sorted_regions[:10]

    result = {
        'regions': [r[0] for r in top10],
        'values': [r[1] for r in top10],
        'map_data': dict(sorted_regions)  # 包含所有标准化后的地区
    }

    # 缓存1小时
    cache.set(cache_key, result, 3600)
    return JsonResponse(result)


# ----------------------------------------以上IP分析--------------------------------------------------------

import os
from collections import defaultdict
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from .models import HotBoard
from .serializers import HotBoardSerializer


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


def hot_data_analysis(request):
    hot_board_id = request.GET.get('hot_board_id')
    if not hot_board_id:
        return JsonResponse({'error': 'Missing hot_board_id'}, status=400)

    try:
        hot_board = HotBoard.objects.get(id=hot_board_id)
    except HotBoard.DoesNotExist:
        return JsonResponse({'error': 'Invalid hot_board_id'}, status=404)

    table_name = get_comment_table(hot_board.rank)
    if not table_name:
        return JsonResponse({'error': 'Invalid rank'}, status=400)

    cache_key = f"hot_analysis_{hot_board_id}"
    if cached := cache.get(cache_key):
        return JsonResponse(cached)

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
        return JsonResponse({'error': '无有效文本数据'}, status=400)

    vectorizer = TfidfVectorizer(
        max_features=1000,
        stop_words=stop_words
    )
    try:
        tfidf_matrix = vectorizer.fit_transform(documents)
    except ValueError:
        return JsonResponse({'error': '文本数据不足以生成特征'}, status=400)

    n_clusters = 10
    try:
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        kmeans.fit(tfidf_matrix)
    except Exception as e:
        return JsonResponse({'error': f'聚类分析失败: {str(e)}'}, status=500)

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
        return JsonResponse({'error': '无有效候选热词'}, status=400)

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

    cache.set(cache_key, result, timeout=3600)
    return JsonResponse(result)


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


from django.http import JsonResponse
from .models import CommentHot1, CommentHot2, CommentHot3, CommentHot4, CommentHot5


def sentiment_analysis(request):
    hot_board_id = request.GET.get('hot_board_id')
    if not hot_board_id:
        return JsonResponse({'error': '缺少hot_board_id参数'}, status=400)

    hot_board = get_object_or_404(HotBoard, id=hot_board_id)
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

    comments = CommentModel.objects.filter(hot_board=hot_board).all()
    scatter_data = []
    for comment in comments:
        # 添加类型强制转换和校验
        try:
            point = {
                'x': float(random.uniform(0, 100)),
                'y': float(random.uniform(0, 100)),
                'likes': int(comment.like_count),  # 确保为整数
                'sentiment': str(comment.sentiment).strip() or '未知'  # 处理空值
            }
            scatter_data.append(point)
        except Exception as e:
            print(f"数据格式错误: {e}")  # 添加错误日志

    # 统计情感分布（保留原有统计逻辑）
    sentiments = CommentModel.objects.filter(hot_board=hot_board) \
        .values('sentiment') \
        .annotate(count=Count('sentiment'))

    sentiment_counts = {"积极": 0, "消极": 0}
    for s in sentiments:
        sentiment = s['sentiment']
        count = s['count']
        if sentiment in sentiment_counts:
            sentiment_counts[sentiment] = count

    return JsonResponse({
        "positive": sentiment_counts["积极"],
        "negative": sentiment_counts["消极"],
        "scatter_data": scatter_data
    })
