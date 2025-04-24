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
from myapp01.views import get_cluster_data, sentiment_analysis

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views.login),  # 登录界面
    path('register/', views.register),  # 注册界面
    path('index/', views.index),  # 系统首页（仪表盘）
    path('layout/', views.layout),  # 模板（母版）
    path('information/', views.information),  # 舆情数据页面
    path('index/hot', views.hotlist),  # 热搜榜单
    path('index/saying', views.saying),  # 评论分析
    path('index/ip', views.ip),  # ip分析
    path('index/soso', views.soso),  # 舆情分析
    path('api/hot_boards/', views.HotBoardListView.as_view(), name='hot_boards'),  # 热搜api
    path('api/comments/', views.get_comments, name='comments'),    #评论api
    path('api/region_distribution/', views.get_region_distribution),    #地区api
    path('hot_data_analysis/', views.hot_data_analysis, name='hot_data_analysis'),
    path('api/cluster-data/', get_cluster_data, name='cluster_data'),# 聚类分析api
    path('api/sentiment-analysis/',sentiment_analysis, name='sentiment-analysis'),   #情感分析api
]
