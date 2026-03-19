from datetime import datetime, timedelta
from collections import defaultdict
from ..models import HotBoard, HotSearch

class TrendAnalysisService:
    """趋势分析服务"""
    
    @staticmethod
    def get_hot_trends(days=7):
        """获取热点趋势数据
        
        Args:
            days: 分析最近多少天的数据
            
        Returns:
            dict: 趋势分析结果
        """
        # 计算时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 获取时间范围内的热榜数据
        hotboards = HotBoard.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).order_by('created_at')
        
        # 按关键词分组
        keyword_trends = defaultdict(list)
        for board in hotboards:
            keyword_trends[board.keyword].append({
                'timestamp': board.created_at,
                'hot_value': board.hot_value,
                'rank': board.rank
            })
        
        # 构建趋势数据
        trends = []
        for keyword, data_points in keyword_trends.items():
            # 按时间排序
            sorted_data = sorted(data_points, key=lambda x: x['timestamp'])
            
            # 提取时间和热度值
            timestamps = [point['timestamp'].strftime('%Y-%m-%d %H:%M') for point in sorted_data]
            hot_values = [point['hot_value'] for point in sorted_data]
            ranks = [point['rank'] for point in sorted_data]
            
            trends.append({
                'keyword': keyword,
                'timestamps': timestamps,
                'hot_values': hot_values,
                'ranks': ranks,
                'max_hot': max(hot_values) if hot_values else 0,
                'min_hot': min(hot_values) if hot_values else 0,
                'avg_hot': sum(hot_values) / len(hot_values) if hot_values else 0
            })
        
        return {
            'trends': trends,
            'time_range': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            },
            'total_keywords': len(trends)
        }
    
    @staticmethod
    def get_hotspot_prediction(keyword, days=3):
        """预测热点趋势
        
        Args:
            keyword: 关键词
            days: 预测未来天数
            
        Returns:
            dict: 预测结果
        """
        # 获取该关键词的历史数据
        hotboards = HotBoard.objects.filter(
            keyword=keyword
        ).order_by('created_at')
        
        if not hotboards:
            return {
                'keyword': keyword,
                'prediction': [],
                'error': 'No historical data found'
            }
        
        # 提取历史数据
        historical_data = []
        for board in hotboards:
            historical_data.append({
                'timestamp': board.created_at,
                'hot_value': board.hot_value
            })
        
        # 简单的线性预测（实际项目中可以使用更复杂的模型）
        if len(historical_data) < 2:
            # 数据不足，返回最后一个值
            last_value = historical_data[-1]['hot_value']
            predictions = []
            current_date = historical_data[-1]['timestamp']
            
            for i in range(1, days + 1):
                next_date = current_date + timedelta(days=i)
                predictions.append({
                    'timestamp': next_date.strftime('%Y-%m-%d'),
                    'predicted_hot': last_value
                })
        else:
            # 计算趋势
            recent_data = historical_data[-7:]  # 最近7天数据
            if len(recent_data) < 2:
                recent_data = historical_data
            
            # 计算斜率
            values = [d['hot_value'] for d in recent_data]
            slope = (values[-1] - values[0]) / (len(values) - 1)
            
            # 预测未来趋势
            predictions = []
            last_date = historical_data[-1]['timestamp']
            last_value = historical_data[-1]['hot_value']
            
            for i in range(1, days + 1):
                next_date = last_date + timedelta(days=i)
                predicted_value = max(0, last_value + slope * i)  # 热度不能为负
                predictions.append({
                    'timestamp': next_date.strftime('%Y-%m-%d'),
                    'predicted_hot': int(predicted_value)
                })
        
        return {
            'keyword': keyword,
            'historical_data': [
                {
                    'timestamp': d['timestamp'].strftime('%Y-%m-%d'),
                    'hot_value': d['hot_value']
                }
                for d in historical_data[-7:]
            ],
            'prediction': predictions,
            'trend': '上升' if slope > 0 else '下降' if slope < 0 else '稳定'
        }
    
    @staticmethod
    def get_hotspot_anomalies(days=7, threshold=1.5):
        """检测热点异常
        
        Args:
            days: 分析最近多少天的数据
            threshold: 异常阈值
            
        Returns:
            list: 异常热点列表
        """
        # 获取趋势数据
        trends = TrendAnalysisService.get_hot_trends(days)
        
        anomalies = []
        for trend in trends['trends']:
            if len(trend['hot_values']) < 2:
                continue
            
            # 计算热度变化率
            values = trend['hot_values']
            changes = []
            for i in range(1, len(values)):
                if values[i-1] > 0:
                    change_rate = abs(values[i] - values[i-1]) / values[i-1]
                    changes.append(change_rate)
            
            if changes:
                avg_change = sum(changes) / len(changes)
                if avg_change > threshold:
                    anomalies.append({
                        'keyword': trend['keyword'],
                        'avg_change_rate': avg_change,
                        'max_hot': trend['max_hot'],
                        'min_hot': trend['min_hot'],
                        'timestamp': trend['timestamps'][-1]
                    })
        
        # 按变化率排序
        anomalies.sort(key=lambda x: x['avg_change_rate'], reverse=True)
        
        return {
            'anomalies': anomalies[:10],  # 只返回前10个异常
            'total_anomalies': len(anomalies)
        }
