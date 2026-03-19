import requests

# 测试的URL列表
urls = [
    "http://127.0.0.1:8000/",  # 登录界面
    "http://127.0.0.1:8000/register/",  # 注册界面
    "http://127.0.0.1:8000/index/",  # 系统首页
    "http://127.0.0.1:8000/information/",  # 舆情数据
    "http://127.0.0.1:8000/index/hot",  # 热搜榜单
    "http://127.0.0.1:8000/index/saying",  # 评论分析
    "http://127.0.0.1:8000/index/ip",  # IP分析
    "http://127.0.0.1:8000/index/soso"  # 舆情分析
]

print("开始测试前端界面...")
for url in urls:
    try:
        response = requests.get(url, timeout=10)
        print(f"{url}: {response.status_code} - {response.reason}")
    except Exception as e:
        print(f"{url}: 错误 - {str(e)}")
print("测试完成！")