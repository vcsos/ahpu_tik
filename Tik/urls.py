"""
URL configuration for Tik project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from myapp01 import views
from myapp01.views import get_cluster_data, sentiment_analysis, SentimentPredictView
from myapp01.services.trend_analysis import TrendAnalysisService
from myapp01.services.topic_clustering import TopicClusteringService

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login),  # 根路径直接进入登录界面
    path('login/', views.login),  # 登录界面
    path('register/', views.register),  # 注册界面
    path('index/', views.index),  # 系统首页（仪表盘）
    path('layout/', views.layout),  # 模板（母版）
    path('information/', views.information),  # 舆情数据页面
    path('index/hot', views.hotlist),  # 热搜榜单
    path('index/saying', views.saying),  # 评论分析
    path('index/ip', views.ip),  # ip分析
    path('index/soso', views.soso),  # 舆情分析
    path('hot_data_analysis/', views.hot_data_analysis, name='hot_data_analysis'),
    
    # API 端点
    path('api/hot_boards/', views.HotBoardListView.as_view(), name='hot_boards'),  # 热搜api
    path('api/comments/', views.get_comments, name='comments'),    #评论api
    path('api/region_distribution/', views.get_region_distribution),    #地区api
    path('api/cluster-data/', get_cluster_data, name='cluster_data'),# 聚类分析api
    path('api/sentiment-analysis/', sentiment_analysis, name='sentiment-analysis'),   #情感分布统计api
    path('api/sentiment-predict/', SentimentPredictView.as_view(), name='sentiment-predict'),   # 实时情感预测api
    
    # 趋势分析 API
    path('api/hot-trends/', views.get_hot_trends, name='hot_trends'),  # 热点趋势
    path('api/hotspot-prediction/', views.get_hotspot_prediction, name='hotspot_prediction'),  # 热点预测
    path('api/hotspot-anomalies/', views.get_hotspot_anomalies, name='hotspot_anomalies'),  # 热点异常
    
    # 话题聚类 API
    path('api/topic-clusters/', views.get_topic_clusters, name='topic_clusters'),  # 话题聚类
    path('api/comment-clusters/', views.get_comment_clusters, name='comment_clusters'),  # 评论聚类
    path('api/cluster-summary/', views.get_cluster_summary, name='cluster_summary'),  # 聚类摘要
]
