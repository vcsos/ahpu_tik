import os
import sys
import random
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置Django设置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tik.settings')

# 导入Django
import django
django.setup()

# 导入所有模型
from myapp01.models import RegisterUser, HotSearch, HotBoard, Video, CommentHot1, CommentHot2, CommentHot3, CommentHot4, CommentHot5

# 视频文案模板
VIDEO_CAPTIONS = [
    "今天给大家分享一个超实用的生活小技巧，学会之后真的太方便了！赶紧点赞收藏吧~",
    "这个太绝了！我都不知道原来还可以这样操作，学会了受益终生！",
    "姐妹们冲！这个宝藏店铺必须安利给大家，真的太好逛了！",
    "日常vlog来啦~今天发生了好多有趣的事情，一起来看看吧！",
    "美食探店日记：发现一家超级好吃的餐厅，性价比超高！",
    "健身打卡第{days}天，坚持就是胜利！有一起的姐妹吗？",
    "护肤心得分享，这几款产品用了一段时间，效果真的绝了！",
    "旅行攻略来啦！{city}三天两夜游玩路线，建议收藏！",
    "职场干货分享，这些面试技巧帮你轻松拿到offer！",
    "萌宠日常，我家{pet}又调皮了，但真的太可爱了！",
    "穿搭分享，今天的这套搭配真的绝绝子！",
    "化妆教程，手把手教你画出精致妆容！",
    "读书笔记分享，这本书真的让我收获很多！",
    "手工DIY教程，在家也能做出精美小物件！",
    "美食制作教程，这道菜简单又好吃！",
    "运动健身分享，这个动作坚持做效果超棒！",
    "学习干货分享，这些方法让你的效率翻倍！",
    "家居整理小技巧，让你的房间焕然一新！",
    "数码产品评测，这款真的值得入手吗？",
    "汽车知识科普，老司机都不一定知道！",
]

PETS = ["猫咪", "狗狗", "仓鼠", "兔子", "鹦鹉", "金鱼"]

# 用户名模板
USER_NAMES = [
    "生活小达人", "美食博主小美", "旅行达人小帅", "健身教练阿强", "护肤达人小雪",
    "萌宠主人小可爱", "穿搭博主小仙", "职场导师老王", "数码达人小科", "汽车发烧友老李",
    "烹饪达人小厨", "读书爱好者小文", "运动健将小健", "手工达人小艺", "美妆博主小颜",
    "摄影爱好者小摄", "游戏达人小游", "音乐发烧友小音", "舞蹈达人小舞", "绘画艺术家小画",
    "花花世界", "梦想家小梦", "追光者", "星辰大海", "温柔岁月", "时光机",
    "快乐星球", "元气满满", "宝藏女孩", "人间烟火", "诗和远方", "岁月静好",
    "阿杰的日常", "小红的分享", "大壮的生活", "小美的日记", "老王的厨房", "小李的旅行",
    "快乐小兔", "阳光男孩", "暖阳下的猫", "月光少女", "彩虹糖", "小确幸",
    "生活记录者", "美好收集家", "快乐制造机", "正能量传递", "微笑使者", "幸福传播者",
]

# 地区列表
REGIONS = [
    "北京", "上海", "广州", "深圳", "杭州", "成都", "重庆", "武汉",
    "西安", "南京", "苏州", "天津", "长沙", "郑州", "青岛", "厦门",
    "福建", "山东", "浙江", "江苏", "广东", "四川", "湖北", "湖南",
    "河北", "河南", "安徽", "江西", "辽宁", "吉林", "黑龙江", "云南",
    "海外", "香港", "澳门", "台湾", "日本", "韩国", "新加坡", "美国",
]

# 评论内容模板
COMMENT_TEMPLATES = [
    "太棒了！学到了很多！",
    "楼主说的太对了，支持！",
    "这也太绝了吧，我第一次知道！",
    "收藏了，以后肯定会用到的！",
    "已经试过了，效果真的很不错！",
    "这个方法太实用了，感谢分享！",
    "看完了，感觉受益匪浅！",
    "终于找到了这个，感谢博主！",
    "厉害了！这个技巧太牛了！",
    "跟着学了一遍，真的可以！",
    "太有用了，必须点赞支持！",
    "这个建议很中肯，谢谢楼主！",
    "学到了学到了，涨知识了！",
    "原来是这样，明白了！",
    "这个真的解决了我的问题！",
    "好文！值得收藏和分享！",
    "良心分享，必须支持！",
    "太有道理了，完全赞同！",
    "这个角度很新颖，学习了！",
    "第一遍没看懂，再看一遍！",
    "说得很好，但我有不同看法！",
    "这个观点很独特！",
    "支持楼主，期待更多分享！",
    "关注了，希望看到更多内容！",
    "真的很有用，已经分享给朋友了！",
    "看完之后感觉豁然开朗！",
    "这个解释太清楚了！",
    "每次看都有新的收获！",
    "确实如此，深有体会！",
    "这个太及时了，正需要！",
    "谁能想到还能这样操作！",
    "太有才了，这是什么神仙操作！",
    "收藏党报道，马住慢慢看！",
    "感谢分享，继续支持！",
    "哈哈哈哈笑死我了！",
    "这也太真实了吧！",
    "扎心了老铁！",
    "说的就是我想说的！",
    "神评论预定！",
    "前排占座！",
    "确实，说得太对了！",
    "恍然大悟，原来如此！",
    "这个思路太清晰了！",
    "好家伙，这也太厉害了！",
    "学到了新技能，感谢！",
    "这个方法值得推广！",
    "我觉得还可以这样！",
    "补充一点，其实还可以！",
    "顺便说一下，注意这个！",
    "亲测有效，放心使用！",
    "过来人表示确实是这样！",
    "新手小白学习了！",
    "大佬带带我！",
    "这个可以，很实用！",
    "内容很干，建议收藏！",
    "学会了，准备去试试！",
    "这个技巧太秀了！",
    "太强了，膜拜大佬！",
    "建议加精，太棒了！",
    "每一条都很实用！",
    "收藏吃灰系列哈哈哈！",
    "说得好，我投一票！",
    "爱了爱了，太喜欢了！",
    "希望博主多出这样的内容！",
    "这个系列希望能一直更新！",
    "看完心情变好了！",
    "正能量满满，支持！",
    "太可爱了，心都化了！",
    "这个真是绝绝子！",
    "yyds，永远的神！",
    "绝了，这个想法太棒了！",
    "慕了慕了，太羡慕了！",
    "冲冲冲！支持支持！",
    "这个太赞了，必须分享！",
]

# 热搜关键词
HOT_KEYWORDS = [
    "人工智能发展趋势", "新能源汽车市场", "健康生活方式", "教育改革政策", "科技创新突破",
    "环境保护措施", "文化传承发展", "体育赛事热点", "娱乐明星动态", "经济发展分析",
    "旅游攻略推荐", "美食文化探索", "时尚潮流趋势", "数码产品评测", "职场发展建议",
    "亲子教育经验", "心理健康知识", "投资理财技巧", "社交平台热点", "医疗健康资讯",
]

# 生成随机日期
def get_random_date(days=30):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    random_date = start_date + (end_date - start_date) * random.random()
    return random_date

# 生成随机时间
def get_random_time():
    return f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}"

# 生成随机热度值
def get_random_hot_value():
    return random.randint(1000, 100000)

# 生成随机点赞数
def get_random_like_count():
    return random.randint(0, 5000)

# 生成随机收藏数
def get_random_collect_count():
    return random.randint(0, 10000)

# 生成随机分享数
def get_random_share_count():
    return random.randint(0, 5000)

# 生成随机视频ID
def generate_video_id():
    return f"v{random.randint(10000000, 99999999)}"

# 生成随机情感分析结果
def get_random_sentiment():
    return random.choice(["积极", "消极"])

# 生成数据
def generate_data():
    print("开始生成数据...")
    
    # 1. 生成热搜数据
    hot_searches = []
    for i, keyword in enumerate(HOT_KEYWORDS):
        hot_search = HotSearch(
            keyword=keyword,
            created_at=get_random_date()
        )
        hot_search.save()
        hot_searches.append(hot_search)
        print(f"生成热搜关键词: {keyword}")
    
    # 2. 生成热榜数据
    hot_boards = []
    for i in range(1, 6):  # 前5个热搜
        hot_board = HotBoard(
            rank=i,
            keyword=hot_searches[i-1].keyword,
            hot_value=get_random_hot_value(),
            created_at=get_random_date(),
            hot_search=hot_searches[i-1]
        )
        hot_board.save()
        hot_boards.append(hot_board)
        print(f"生成热榜数据: {i}. {hot_searches[i-1].keyword}")
    
    # 3. 生成视频数据
    videos = []
    for i in range(100):  # 生成100个视频
        caption_template = random.choice(VIDEO_CAPTIONS)
        if "{days}" in caption_template:
            caption = caption_template.format(days=random.randint(1, 365))
        elif "{city}" in caption_template:
            caption = caption_template.format(city=random.choice(REGIONS))
        elif "{pet}" in caption_template:
            caption = caption_template.format(pet=random.choice(PETS))
        else:
            caption = caption_template
        
        video = Video(
            caption=caption,
            video_date=get_random_date(),
            video_id=generate_video_id(),
            user_name=random.choice(USER_NAMES),
            collect_count=get_random_collect_count(),
            share_count=get_random_share_count(),
            popularity=random.choice(["热门", "正常"]),
            created_at=get_random_date(),
            hot_search=random.choice(hot_searches)
        )
        video.save()
        videos.append(video)
        if (i+1) % 10 == 0:
            print(f"生成视频数据: {i+1}/100")
    
    # 4. 生成评论数据
    comment_models = [CommentHot1, CommentHot2, CommentHot3, CommentHot4, CommentHot5]
    total_comments = 0
    
    for i, (hot_board, comment_model) in enumerate(zip(hot_boards, comment_models)):
        # 为每个热榜生成200条评论
        for j in range(200):
            comment = comment_model(
                nickname=random.choice(USER_NAMES),
                region=random.choice(REGIONS),
                comment_date=get_random_date(),
                content=random.choice(COMMENT_TEMPLATES),
                like_count=get_random_like_count(),
                created_at=get_random_date(),
                video=random.choice(videos) if random.random() > 0.5 else None,
                hot_board=hot_board,
                sentiment=get_random_sentiment()
            )
            comment.save()
            total_comments += 1
            if total_comments % 100 == 0:
                print(f"生成评论数据: {total_comments}/1000")
    
    # 5. 生成用户数据
    for i in range(10):
        user = RegisterUser(
            reg_mail=f"user{i}@example.com",
            reg_pwd=f"password{i+123}"
        )
        user.save()
    
    print(f"数据生成完成！")
    print(f"- 热搜关键词: {len(hot_searches)}")
    print(f"- 热榜数据: {len(hot_boards)}")
    print(f"- 视频数据: {len(videos)}")
    print(f"- 评论数据: {total_comments}")
    print(f"- 用户数据: 10")

if __name__ == "__main__":
    generate_data()
