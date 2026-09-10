# ============================================
# 敏感词库配置文件 - safety_words.py
# 儿童AI聊天机器人专用

# ----- 暴力相关敏感词 -----
VIOLENCE_WORDS = [
    "打死", "杀人", "自杀", "跳楼", "砍死", "炸死",
    "掐死", "勒死", "枪杀", "谋杀", "暗杀", "行凶",
    "打人", "打架", "斗殴", "欺负", "虐待", "暴力"
]

# ----- 脏话相关敏感词 -----
BAD_WORDS = [
    "笨蛋", "傻瓜", "白痴", "蠢货", "混蛋", "滚蛋",
    "去死", "该死", "操", "他妈", "tmd", "fuck",
    "shit", "垃圾", "废物", "恶心", "讨厌", "烦人"
]

# ----- 色情相关敏感词 -----
ADULT_WORDS = [
    "色情", "成人", "18禁", "av", "h网",
    "裸体", "裸露", "性感", "诱惑"
]

# ----- 其他不宜内容 -----
OTHER_BAD_WORDS = [
    "赌博", "吸毒", "抽烟", "喝酒", "酗酒",
    "偷东西", "抢劫", "作弊", "撒谎", "骗人"
]

# ----- 部分敏感字（单字检测）-----
PARTIAL_SENSITIVE_CHARS = [
    "死", "杀", "打", "骂", "操", "滚"
]

# ----- 合并所有敏感词（用于快速检测）-----
ALL_SENSITIVE_WORDS = VIOLENCE_WORDS + BAD_WORDS + ADULT_WORDS + OTHER_BAD_WORDS

# ----- 友好回复模板（当检测到敏感词时使用）-----
FRIENDLY_REPLIES = [
    "我们不说这个词哦，换个开心的话题吧！",
    "这个词不太好，我们来聊点有趣的事情吧～",
    "说点开心的吧！你今天开心吗？",
    "这个不能说，我们聊别的吧！",
    "小朋友不说这种话哦，我们来玩个游戏吧！",
    "用词要文明，做个有礼貌的好孩子！",
    "这个话题不太好，我们换个话题好吗？",
    "不说这些，我给你讲个笑话吧！"
]

# ----- 按类别获取敏感词的函数 -----
def get_words_by_category(category):
    """
    按类别获取敏感词
    category: 'violence', 'bad', 'adult', 'other', 'all'
    """
    categories = {
        'violence': VIOLENCE_WORDS,
        'bad': BAD_WORDS,
        'adult': ADULT_WORDS,
        'other': OTHER_BAD_WORDS,
        'all': ALL_SENSITIVE_WORDS,
        'partial': PARTIAL_SENSITIVE_CHARS
    }
    return categories.get(category, [])

# ----- 显示所有敏感词统计信息 -----
def show_stats():
    """显示敏感词统计信息"""
    print("\n" + "=" * 50)
    print("敏感词库统计信息")
    print("=" * 50)
    print(f"暴力相关: {len(VIOLENCE_WORDS)} 个")
    print(f"脏话相关: {len(BAD_WORDS)} 个")
    print(f"色情相关: {len(ADULT_WORDS)} 个")
    print(f"其他不宜: {len(OTHER_BAD_WORDS)} 个")
    print(f"部分敏感字: {len(PARTIAL_SENSITIVE_CHARS)} 个")
    print(f"总计完整词: {len(ALL_SENSITIVE_WORDS)} 个")
    print("=" * 50)

# ----- 测试函数（可选）-----
if __name__ == "__main__":
    print("敏感词库加载成功！")
    show_stats()