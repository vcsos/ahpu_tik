from ..models import HotBoard


class HotBoardRepository:
    """热榜数据访问层"""

    @staticmethod
    def get_all_hot_boards():
        """获取所有热榜数据"""
        return HotBoard.objects.all().order_by('rank')

    @staticmethod
    def get_hot_boards_by_rank(rank_limit=5):
        """获取指定排名范围内的热榜数据"""
        return HotBoard.objects.filter(rank__lte=rank_limit).order_by('rank')

    @staticmethod
    def get_hot_board_by_id(hot_board_id):
        """根据ID获取热榜数据"""
        try:
            return HotBoard.objects.get(id=hot_board_id)
        except HotBoard.DoesNotExist:
            return None

    @staticmethod
    def get_latest_update_time():
        """获取最新更新时间"""
        latest = HotBoard.objects.order_by('-created_at').first()
        return latest.created_at if latest else None