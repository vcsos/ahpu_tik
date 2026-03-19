from ..repositories.hotboard_repository import HotBoardRepository
from ..serializers import HotBoardSerializer


class HotBoardService:
    """热榜服务层"""

    @staticmethod
    def get_hot_boards_list():
        """获取热榜列表"""
        hot_boards = HotBoardRepository.get_hot_boards_by_rank(5)
        serializer = HotBoardSerializer(hot_boards, many=True)
        return serializer.data

    @staticmethod
    def get_hot_board_by_id(hot_board_id):
        """根据ID获取热榜"""
        return HotBoardRepository.get_hot_board_by_id(hot_board_id)

    @staticmethod
    def get_latest_update_time():
        """获取最新更新时间"""
        return HotBoardRepository.get_latest_update_time()

    @staticmethod
    def get_hot_list_data():
        """获取热搜榜单数据"""
        hot_items = HotBoardRepository.get_all_hot_boards()
        update_time = HotBoardRepository.get_latest_update_time()
        return hot_items, update_time