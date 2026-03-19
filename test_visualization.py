import requests
import json

# 测试基础URL
BASE_URL = 'http://127.0.0.1:8000'

def test_endpoint(url, method='GET', data=None):
    """测试单个端点"""
    try:
        if method == 'GET':
            response = requests.get(url, timeout=10)
        else:
            response = requests.post(url, json=data, timeout=10)
        
        print(f"测试 {url}")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            # 尝试解析JSON响应
            try:
                data = response.json()
                print(f"响应数据类型: {type(data)}")
                if isinstance(data, dict):
                    print(f"响应键: {list(data.keys())}")
                elif isinstance(data, list):
                    print(f"响应列表长度: {len(data)}")
                print("✓ 成功")
            except json.JSONDecodeError:
                # 对于HTML响应
                print("✓ 成功 (HTML响应)")
        else:
            print(f"✗ 失败: {response.text}")
        print("-" * 50)
    except Exception as e:
        print(f"✗ 错误: {str(e)}")
        print("-" * 50)

def test_visualization_modules():
    """测试所有数据可视化模块"""
    print("测试数据可视化模块")
    print("=" * 60)
    
    # 测试前端页面
    frontend_pages = [
        '/index/hot',      # 热搜榜单
        '/index/saying',   # 评论分析
        '/index/ip',       # IP分析
        '/index/soso',     # 舆情分析
        '/hot_data_analysis/',  # 热搜数据分析
    ]
    
    print("测试前端页面:")
    for page in frontend_pages:
        test_endpoint(BASE_URL + page)
    
    # 测试API端点（使用第一个热榜ID=5009）
    api_endpoints = [
        '/api/hot_boards/',              # 热搜数据
        '/api/comments/?hotId=5009',        # 评论数据
        '/api/region_distribution/?hot_board_id=5009',     # 地区分布数据
        '/api/cluster-data/?hot_board_id=5009',            # 聚类分析数据
        '/api/sentiment-analysis/?hot_board_id=5009',      # 情感分布统计
    ]
    
    print("\n测试API端点:")
    for endpoint in api_endpoints:
        test_endpoint(BASE_URL + endpoint)
    
    # 测试情感预测API (POST)
    print("\n测试情感预测API:")
    test_endpoint(
        BASE_URL + '/api/sentiment-predict/', 
        method='POST', 
        data={'text': '这是一个测试评论'}
    )

if __name__ == "__main__":
    test_visualization_modules()
