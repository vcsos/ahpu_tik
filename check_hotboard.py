import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tik.settings')
django.setup()

from myapp01.models import HotBoard

# 获取所有热榜
boards = HotBoard.objects.all()
print('HotBoard Count:', len(boards))
print('\nHotBoard Details:')
for i, board in enumerate(boards):
    print(f'{i+1}. ID: {board.id}, Rank: {board.rank}, Keyword: {board.keyword}, Hot Value: {board.hot_value}')
