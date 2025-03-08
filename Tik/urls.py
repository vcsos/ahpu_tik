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

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views.login),  # 登录界面
    path('register/', views.register),  # 注册界面
    path('index/', views.index),  # 系统首页（仪表盘）
    path('layout/', views.layout),  # 模板（母版）
    path('information/', views.information),  # 舆情数据页面
    path('index/hot', views.hotlist),  # 热搜榜单
    path('index/hotdir/', views.hotdir),  # 热词
    path('index/view', views.view),  # 热搜分析
    path('index/saying', views.saying),  # 评论分析
    path('index/ip', views.ip),  # ip分析
    path('index/soso', views.soso),  # 舆情分析

]
