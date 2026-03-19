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
from .utils.redis_client import get_redis_connection
from .services.text_analysis import get_comment_table, load_stopwords, get_comment_texts
from .services.hotboard_service import HotBoardService
from .services.comment_service import CommentService
from .services.trend_analysis import TrendAnalysisService
from .services.topic_clustering import TopicClusteringService
from ml_utils.model_loader import SentimentAnalyzer


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


redis_conn = get_redis_connection(db=0)
sentiment_analyzer = SentimentAnalyzer()
from django.db.models import Count


def index(request):
    # 最高评论点赞数（从MySQL）
    max_comment = CommentHot1.objects.order_by('-like_count').first()
    max_like_count = max_comment.like_count if max_comment else 0

    # 最高收藏数（从Redis video）
    max_collects = 0
    latest_videos = []
    max_shares = 0
    max_hot_value = 0
    hotboards = []
    current_hot_board_id = None

    # 优雅降级处理Redis连接
    try:
        # 最高收藏数和最新视频
        video_keys = redis_conn.keys('video:*')
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

        # 最高热度值 & 热搜数据
        hotboard_keys = redis_conn.keys('hotboard:*')
        for key in hotboard_keys:
            board_data = json.loads(redis_conn.get(key))
            hotboards.append(board_data)
            if board_data['hot_value'] > max_hot_value:
                max_hot_value = board_data['hot_value']

        # 最高分享数
        max_shares = max([video.get('shares', 0) for video in
                          [json.loads(redis_conn.get(k)) for k in video_keys]], default=0)

        if hotboards:
            current_hot_board_id = hotboards[0].get('id')
    except Exception as e:
        print(f"Redis连接失败: {e}")
        # 使用默认值
        max_collects = 0
        max_shares = 0
        max_hot_value = 0
        hotboards = []
        latest_videos = []

    context = {
        'max_like_count': max_like_count,
        'max_collects': max_collects,
        'max_hot_value': max_hot_value,
        'max_shares': max_shares,
        'latest_videos': latest_videos,
        'hotboards_json': json.dumps(hotboards),
        'current_hot_board_id': current_hot_board_id
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
    # 使用服务层获取数据
    hot_items, update_time = HotBoardService.get_hot_list_data()

    return render(request, 'hot.html', {
        'hot_items': hot_items,
        'update_time': update_time
    })


class HotBoardListView(APIView):
    def get(self, request):
        # 缓存检查（优雅降级）
        cache_key = 'hot_boards_list'
        try:
            if cached := cache.get(cache_key):
                return Response(cached)
        except Exception as e:
            print(f"缓存读取失败: {e}")
        
        # 使用服务层获取数据
        data = HotBoardService.get_hot_boards_list()
        
        # 缓存10分钟（优雅降级）
        try:
            cache.set(cache_key, data, 600)
        except Exception as e:
            print(f"缓存写入失败: {e}")
        
        return Response(data)


def get_comments(request):
    hot_id = request.GET.get('hotId')
    if not hot_id:
        return JsonResponse({'error': '缺少hotId参数'}, status=400)

    # 分页参数
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))

    # 缓存检查（优雅降级）
    cache_key = f'comments_{hot_id}_{page}_{page_size}'
    try:
        if cached := cache.get(cache_key):
            return JsonResponse(cached, safe=False)
    except Exception as e:
        print(f"缓存读取失败: {e}")

    # 使用服务层获取数据
    result = CommentService.get_comments_by_hot_id(hot_id, page, page_size)
    if not result:
        return JsonResponse({'error': '未找到指定热榜'}, status=404)

    # 缓存5分钟（优雅降级）
    try:
        cache.set(cache_key, result, 300)
    except Exception as e:
        print(f"缓存写入失败: {e}")
    
    return JsonResponse(result, safe=False)


# --------------------------评论数据----------------------------------------


def normalize_region(region):
    """统一地区名称格式"""
    replacements = ['省', '市', '自治区', '特别行政区']
    for rep in replacements:
        region = region.replace(rep, '')
    return region


def get_region_distribution(request):
    hot_board_id = request.GET.get('hot_board_id')
    if not hot_board_id:
        return JsonResponse({'error': '缺少hot_board_id参数'}, status=400)

    # 缓存检查（优雅降级）
    cache_key = f"region_{hot_board_id}"
    try:
        if cached := cache.get(cache_key):
            return JsonResponse(cached)
    except Exception as e:
        print(f"缓存读取失败: {e}")

    # 使用服务层获取数据
    result = CommentService.get_region_distribution(hot_board_id)
    if not result:
        return JsonResponse({'error': '未找到指定热榜'}, status=404)

    # 缓存1小时（优雅降级）
    try:
        cache.set(cache_key, result, 3600)
    except Exception as e:
        print(f"缓存写入失败: {e}")
    
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

    # 缓存检查（优雅降级）
    cache_key = f"sentiment_{hot_board_id}"
    try:
        if cached := cache.get(cache_key):
            return JsonResponse(cached)
    except Exception as e:
        print(f"缓存读取失败: {e}")

    # 使用服务层获取数据
    result = CommentService.get_sentiment_analysis(hot_board_id)
    if not result:
        return JsonResponse({'error': '未找到指定热榜'}, status=404)

    # 缓存30分钟（优雅降级）
    try:
        cache.set(cache_key, result, 1800)
    except Exception as e:
        print(f"缓存写入失败: {e}")
    
    return JsonResponse(result)


class SentimentPredictView(APIView):
    """
    在线实时情感分析 API。
    支持：
    - 单条文本：{"text": "xxx"}
    - 多条文本：{"texts": ["xxx", "yyy"]}
    返回每条文本的情感标签和可选概率。
    """

    def post(self, request):
        data = request.data or {}
        texts = data.get("texts")
        text = data.get("text")

        # 兼容单条和多条输入
        if texts is None:
            if not text:
                return JsonResponse({"error": "缺少 text 或 texts 字段"}, status=400)
            texts = [text]

        # 过滤空字符串
        texts = [t for t in texts if isinstance(t, str) and t.strip()]
        if not texts:
            return JsonResponse({"error": "文本内容为空"}, status=400)

        # 使用 CPU 模型批量推理
        labels = sentiment_analyzer.predict_batch(texts)

        results = [
            {"text": t, "label": label}
            for t, label in zip(texts, labels)
        ]
        return JsonResponse({"results": results}, status=200)


# 趋势分析 API
def get_hot_trends(request):
    """获取热点趋势数据"""
    days = int(request.GET.get('days', 7))
    result = TrendAnalysisService.get_hot_trends(days)
    return JsonResponse(result)


def get_hotspot_prediction(request):
    """预测热点趋势"""
    keyword = request.GET.get('keyword')
    days = int(request.GET.get('days', 3))
    if not keyword:
        return JsonResponse({"error": "缺少keyword参数"}, status=400)
    result = TrendAnalysisService.get_hotspot_prediction(keyword, days)
    return JsonResponse(result)


def get_hotspot_anomalies(request):
    """检测热点异常"""
    days = int(request.GET.get('days', 7))
    threshold = float(request.GET.get('threshold', 1.5))
    result = TrendAnalysisService.get_hotspot_anomalies(days, threshold)
    return JsonResponse(result)


# 话题聚类 API
def get_topic_clusters(request):
    """获取话题聚类"""
    n_clusters = int(request.GET.get('n_clusters', 5))
    result = TopicClusteringService.get_topic_clusters(n_clusters)
    return JsonResponse(result)


def get_comment_clusters(request):
    """获取评论聚类"""
    hot_board_id = request.GET.get('hot_board_id')
    n_clusters = int(request.GET.get('n_clusters', 3))
    if not hot_board_id:
        return JsonResponse({"error": "缺少hot_board_id参数"}, status=400)
    result = TopicClusteringService.get_comment_clusters(hot_board_id, n_clusters)
    return JsonResponse(result)


def get_cluster_summary(request):
    """获取聚类摘要"""
    result = TopicClusteringService.get_cluster_summary()
    return JsonResponse(result)
