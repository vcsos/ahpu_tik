from django.db import models

"""
可视化系统用户账号和密码
"""
class RegisterUser(models.Model):
    reg_mai=models.CharField(max_length=100,blank=False)
    reg_pwd=models.CharField(max_length=100,blank=False)


class Comment(models.Model):
    """
    评论数据模型
    用于存储抖音视频的用户评论信息
    """
    nickname = models.CharField(max_length=255,verbose_name="用户昵称",help_text="发表评论的用户昵称")
    region = models.CharField(max_length=255,blank=True,null=True,verbose_name="用户地区",help_text="用户所在地区（IP地址解析结果，可能为空）")
    comment_date = models.DateTimeField(verbose_name="评论时间",help_text="评论发表的具体时间")
    content = models.TextField(verbose_name="评论内容",help_text="用户发表的评论正文")
    like_count = models.IntegerField(default=0,verbose_name="点赞数",help_text="该评论获得的点赞数量")
    created_at = models.DateTimeField(auto_now_add=True,verbose_name="创建时间",help_text="数据记录自动生成的时间戳")

    class Meta:
        verbose_name = "评论数据"
        verbose_name_plural = verbose_name
        ordering = ['-comment_date']  # 默认按评论时间倒序排列

    def __str__(self):
        return f"{self.nickname} - {self.comment_date.strftime('%Y-%m-%d %H:%M')}"


class HotBoard(models.Model):
    """
    抖音热榜数据模型
    用于存储抖音实时热点榜单信息
    """
    rank = models.IntegerField(verbose_name="排名",help_text="热点在榜单中的位置")
    keyword = models.CharField(max_length=255,verbose_name="关键词",help_text="热点话题的核心关键词")
    hot_value = models.IntegerField(verbose_name="热度值",help_text="衡量热点热度的数值指标")
    created_at = models.DateTimeField(auto_now_add=True,verbose_name="抓取时间",help_text="数据抓取时的系统时间")

    class Meta:
        verbose_name = "热榜数据"
        verbose_name_plural = verbose_name
        ordering = ['-rank']  # 默认按排名升序排列

    def __str__(self):
        return f"{self.rank}. {self.keyword} ({self.hot_value})"


class Video(models.Model):
    """
    视频信息模型
    用于存储抖音视频的元数据信息
    """
    caption = models.TextField(verbose_name="视频文案",help_text="视频的描述文案")
    video_date = models.DateTimeField(verbose_name="发布时间",help_text="视频首次发布的时间")
    video_id = models.CharField(max_length=255,unique=True,verbose_name="视频ID",help_text="抖音系统分配的唯一视频标识符")
    user_name = models.CharField(max_length=255,verbose_name="发布者",help_text="视频发布者的用户名")
    collect_count = models.IntegerField(default=0,verbose_name="收藏数",help_text="视频被收藏的次数")
    share_count = models.IntegerField(default=0,verbose_name="转发数",help_text="视频被转发的次数")
    popularity = models.CharField(max_length=20,choices=[('热门', '热门'), ('正常', '正常')],default='正常',verbose_name="视频热度",help_text="根据转发量定义的热度等级（热门/正常）")
    created_at = models.DateTimeField(auto_now_add=True,verbose_name="入库时间",help_text="数据记录自动生成的时间戳")

    class Meta:
        verbose_name = "视频信息"
        verbose_name_plural = verbose_name
        ordering = ['-video_date']  # 默认按发布时间倒序排列

    def __str__(self):
        return f"{self.user_name} - {self.caption[:50]}..."