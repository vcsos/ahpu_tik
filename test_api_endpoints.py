import requests

# 测试所有API端点
def test_all_api_endpoints():
    print('Testing all API endpoints:')
    print('=' * 60)
    
    endpoints = [
        ('GET', '/api/hot_boards/', '热搜数据'),
        ('GET', '/api/comments/?hotId=5009', '评论数据'),
        ('GET', '/api/region_distribution/?hot_board_id=5009', '地区分布'),
        ('GET', '/api/cluster-data/?hot_board_id=5009', '聚类分析'),
        ('GET', '/api/sentiment-analysis/?hot_board_id=5009', '情感分析'),
        ('POST', '/api/sentiment-predict/', '情感预测'),
        ('GET', '/api/hot-trends/', '热点趋势'),
        ('GET', '/api/hotspot-prediction/?keyword=AI', '热点预测'),
        ('GET', '/api/hotspot-anomalies/', '热点异常'),
        ('GET', '/api/topic-clusters/', '话题聚类'),
        ('GET', '/api/comment-clusters/?hot_board_id=5009', '评论聚类'),
        ('GET', '/api/cluster-summary/', '聚类摘要'),
    ]
    
    base_url = 'http://localhost:8000'
    
    for method, endpoint, description in endpoints:
        try:
            if method == 'POST':
                response = requests.post(base_url + endpoint, json={'text': '测试评论'})
            else:
                response = requests.get(base_url + endpoint)
            
            print(f'{endpoint:<60} {response.status_code} - {response.reason:<10} {description}')
        except Exception as e:
            print(f'{endpoint:<60} Error - {str(e):<10} {description}')
    
    print('=' * 60)

if __name__ == '__main__':
    test_all_api_endpoints()
