import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from collections import Counter
import jieba
import re
import numpy as np
from wordcloud import WordCloud
from PIL import Image, ImageDraw, ImageFont
import os
import io
import textwrap
from contextlib import redirect_stdout

# ========== 配置区域 ==========
# 在这里修改文件路径和年份
FILE_PATH = "mes.xlsx"  # 修改为你的文件路径
ANALYSIS_YEAR = 2026# 修改为你想分析的年份 (2022-2026)
# ==============================

# 设置中文字体（Mac系统）
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


def load_and_clean_data(file_path, year):
    """加载并清洗数据"""
    df = pd.read_excel(file_path, header=None)
    df.columns = ['datetime', 'qq', 'name', 'message']
    df['datetime'] = pd.to_datetime(df['datetime'], format='%Y/%m/%d %H:%M')
    df = df[df['datetime'].dt.year == year]
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour
    df['weekday'] = df['datetime'].dt.dayofweek
    df['month'] = df['datetime'].dt.month
    df = df.sort_values('datetime').reset_index(drop=True)
    return df


def basic_statistics(df):
    """基础统计分析"""
    print(f"\n{'=' * 60}")
    print(f"📊 {ANALYSIS_YEAR}年度聊天数据分析报告")
    print(f"{'=' * 60}\n")

    total_messages = len(df)
    total_days = df['date'].nunique()
    date_range = f"{df['datetime'].min().strftime('%Y-%m-%d')} 至 {df['datetime'].max().strftime('%Y-%m-%d')}"

    print(f"📅 统计时间段: {date_range}")
    print(f"💬 总消息数: {total_messages} 条")
    print(f"📆 聊天天数: {total_days} 天")
    print(f"📈 日均消息: {total_messages / total_days:.1f} 条/天\n")

    print(f"{'=' * 60}")
    print("👥 个人消息统计")
    print(f"{'=' * 60}")
    person_stats = df.groupby('name').agg({
        'message': 'count',
        'datetime': lambda x: (x.max() - x.min()).days
    }).round(2)
    person_stats.columns = ['消息数', '跨越天数']
    person_stats['占比'] = (person_stats['消息数'] / total_messages * 100).round(2)
    person_stats['平均消息长度'] = df.groupby('name')['message'].apply(lambda x: x.str.len().mean()).round(2)

    for name, row in person_stats.iterrows():
        print(f"\n{name}:")
        print(f"  发送消息: {int(row['消息数'])} 条 ({row['占比']}%)")
        print(f"  平均长度: {row['平均消息长度']:.1f} 字")

    return person_stats


def time_analysis(df):
    """时间分布分析"""
    print(f"\n{'=' * 60}")
    print("⏰ 时间分布分析")
    print(f"{'=' * 60}")

    hour_dist = df['hour'].value_counts().sort_index()
    most_active_hour = hour_dist.idxmax()
    print(f"\n最活跃时段: {most_active_hour}:00-{most_active_hour}:59 ({hour_dist.max()} 条消息)")

    weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    weekday_dist = df['weekday'].value_counts().sort_index()
    most_active_day = weekday_names[weekday_dist.idxmax()]
    print(f"最活跃星期: {most_active_day} ({weekday_dist.max()} 条消息)")

    month_dist = df['month'].value_counts().sort_index()
    most_active_month = month_dist.idxmax()
    print(f"最活跃月份: {most_active_month}月 ({month_dist.max()} 条消息)")

    daily_count = df.groupby('date').size()
    most_active_date = daily_count.idxmax()
    print(f"聊得最多的一天: {most_active_date} ({daily_count.max()} 条消息)")

    return hour_dist, weekday_dist, month_dist


def interaction_analysis(df):
    """互动模式分析"""
    print(f"\n{'=' * 60}")
    print("💬 互动模式深度分析")
    print(f"{'=' * 60}")

    print(f"\n⚡ 回复速度分析")
    print(f"{'-' * 60}")

    df['time_diff'] = df['datetime'].diff()
    df['prev_name'] = df['name'].shift(1)
    reply_df = df[df['name'] != df['prev_name']].copy()
    reply_df = reply_df[reply_df['time_diff'] <= timedelta(hours=1.5)]

    reply_stats = None
    if len(reply_df) > 0:
        SLOW_5MIN = timedelta(minutes=5)
        SLOW_30MIN = timedelta(minutes=30)
        SLOW_60MIN = timedelta(minutes=60)
        reply_stats = reply_df.groupby('name')['time_diff'].agg([
            ('平均回复时间', lambda x: x.mean().total_seconds() / 60),
            ('中位数回复时间', lambda x: x.median().total_seconds() / 60),

            # ✅ 高分位数：体现“经常拖很久”
            ('P90回复时间', lambda x: x.quantile(0.90).total_seconds() / 60),
            ('P95回复时间', lambda x: x.quantile(0.95).total_seconds() / 60),

            # ✅ 慢回复占比：体现“总是不及时”
            ('>5分钟占比', lambda x: (x > SLOW_5MIN).mean() * 100),
            ('>30分钟占比', lambda x: (x > SLOW_30MIN).mean() * 100),
            ('>60分钟占比', lambda x: (x > SLOW_60MIN).mean() * 100),

            ('最快回复', lambda x: x.min().total_seconds()),
            ('回复次数', 'count')
        ]).round(2)

        for name, row in reply_stats.iterrows():
            print(f"\n{name}:")
            print(f"  中位数回复时间: {row['中位数回复时间']:.1f} 分钟")
            print(f"  90%百分位回复时间: {row['P90回复时间']:.1f} 分钟")
            print(f"  95%百分位回复时间: {row['P95回复时间']:.1f} 分钟")
            print(f"  慢回复占比 >5min:  {row['>5分钟占比']:.1f}%")
            print(f"  慢回复占比 >30min: {row['>30分钟占比']:.1f}%")
            print(f"  慢回复占比 >60min: {row['>60分钟占比']:.1f}%")
            print(f"  最快回复: {row['最快回复']:.0f} 秒")

        slowest_person = reply_stats['>30分钟占比'].idxmax()
        print(f"\n🐢 最不及时回复（>30min占比最高）: {slowest_person}")

    print(f"\n🔄 对话轮次分析")
    print(f"{'-' * 60}")

    df['session_break'] = (df['time_diff'] > timedelta(minutes=30)) | (df['time_diff'].isna())
    df['session_id'] = df['session_break'].cumsum()

    session_stats = []
    for session_id, group in df.groupby('session_id'):
        if len(group) >= 2:
            name_changes = (group['name'] != group['name'].shift()).sum()
            session_stats.append({
                'session_id': session_id,
                'rounds': name_changes,
                'messages': len(group),
                'duration': (group['datetime'].max() - group['datetime'].min()).total_seconds() / 60
            })

    session_df = pd.DataFrame(session_stats)

    if len(session_df) > 0:
        print(f"总对话场次: {len(session_df)} 次")
        print(f"平均每次对话轮次: {session_df['rounds'].mean():.1f} 轮")
        print(f"平均每次对话消息数: {session_df['messages'].mean():.1f} 条")
        print(f"平均对话时长: {session_df['duration'].mean():.1f} 分钟")
        print(f"最长对话: {session_df['rounds'].max()} 轮 ({session_df['messages'].max()} 条消息)")

    print(f"\n🎯 主动性分析")
    print(f"{'-' * 60}")

    initiators = (df.sort_values("datetime")
    .groupby("session_id")
    .first()["name"])  # 每段对话第一条消息的发送者

    init_counts = initiators.value_counts()
    init_ratio = (init_counts / init_counts.sum() * 100).round(2)

    initiation_stats = {}
    for name in df["name"].unique():
        initiation_stats[name] = {
            "init_count": int(init_counts.get(name, 0)),
            "init_ratio": float(init_ratio.get(name, 0.0))
        }

    for name, st in initiation_stats.items():
        print(f"\n{name}:")
        print(f"  发起对话: {st['init_count']} 次")
        print(f"  发起占比: {st['init_ratio']:.2f}%")

    topic_leader = max(initiation_stats.items(), key=lambda x: x[1]["init_count"])
    print(f"\n🏆 更常先开口的人: {topic_leader[0]}")

    # 如果你还想看“最长连续由谁发起的 streak”（可选）
    initiator_streak = (initiators != initiators.shift()).cumsum()
    streak_len = initiators.groupby(initiator_streak).size()
    print("最长连续发起 streak:", streak_len.max())

    print(f"\n😊 表情使用分析")
    print(f"{'-' * 60}")

    emoji_pattern = r'/[\u4e00-\u9fa5]+'
    person_emojis = {}
    for name in df['name'].unique():
        person_msgs = df[df['name'] == name]['message'].astype(str)
        emojis = []
        for msg in person_msgs:
            emojis.extend(re.findall(emoji_pattern, msg))
        person_emojis[name] = Counter(emojis)

    all_emojis = sum(person_emojis.values(), Counter())

    if all_emojis:
        print(f"\n📊 表情使用总榜 TOP 10:")
        for emoji, count in all_emojis.most_common(10):
            print(f"  {emoji}: {count} 次")

        for name, emoji_counter in person_emojis.items():
            if emoji_counter:
                print(f"\n{name} 最爱用的表情 TOP 5:")
                for emoji, count in emoji_counter.most_common(5):
                    print(f"  {emoji}: {count} 次")

    return reply_stats, session_df, initiation_stats, all_emojis


def content_deep_analysis(df):
    """内容深度分析"""
    print(f"\n{'=' * 60}")
    print("🔍 内容深度分析")
    print(f"{'=' * 60}")

    # 准备文本数据
    all_text = ' '.join(df['message'].astype(str))
    emoji_pattern = r'/[\u4e00-\u9fa5]+'
    all_text_clean = re.sub(emoji_pattern, '', all_text)
    all_text_clean = re.sub(r'\[图片\]|\[表情\]|\[引用\]', '', all_text_clean)

    words = jieba.cut(all_text_clean)
    stopwords = {
        '的', '了', '是', '我', '你', '在', '有', '和', '就', '不', '人', '都', '一', '一个',
        '上', '也', '很', '到', '说', '要', '去', '吗', '啊', '呢', '吧', '哦', '嘛',
        '哈', '哈哈', '这', '那', '什么', '怎么', '为什么', '这样', '那样', '没有', '可以',
        '图片', 'nan', '引用', '表情', '然后', '但是', '还是', '如果', '因为', '所以',
        '已经', '还有', '或者', '而且', '不过', '只是', '应该', '可能', '觉得', '好像',
        '感觉', '自己', '他们', '我们', '你们', '出来', '起来', '下来', '过来'
    }
    word_list = [w for w in words if len(w) > 1 and w not in stopwords and not w.isdigit() and w.strip()]
    word_counter = Counter(word_list)

    # 1. 高频词统计
    print(f"\n📝 高频词 TOP 20:")
    for word, count in word_counter.most_common(20):
        print(f"  {word}: {count} 次")

    # 2. 游戏话题统计

    game_keywords = {
        '原神': ['原神', '须弥', '提瓦特', '派蒙', '旅行者'],
        '王者荣耀': ['王者', '荣耀', '峡谷', '五杀', '超神', '打野', '中路', '上路', '下路', '辅助'],
        '英雄联盟': ['lol', 'LOL', '英雄联盟', '召唤师峡谷', '峡谷'],
        '和平精英': ['和平精英', '吃鸡', '落地成盒', '空投'],
        '我的世界': ['我的世界', 'mc', 'MC', '史蒂夫', '苦力怕'],
        'GTA': ['gta', 'GTA', '圣安地列斯', '罪恶都市'],
        '塞尔达': ['塞尔达', '旷野之息', '王国之泪'],
        '宝可梦': ['宝可梦', '精灵宝可梦', '口袋妖怪', '皮卡丘'],
        '明日方舟': ['明日方舟', '方舟', '博士', '刀客塔'],
        '崩坏': ['崩坏', '星穹铁道', '崩铁']
    }

    # 3. 话题分类统计
    print(f"\n📚 话题分类统计")
    print(f"{'-' * 60}")

    topic_keywords = {
        # 📚 学习 / 学业
        '学习': [
            '学习', '作业', '考试', '复习', '背书', '刷题', '题目', '错题',
            '老师', '课程', '上课', '下课', '学校', '教室', '图书馆',
            '作业多', '写作业', '考试周', '期中', '期末', '挂科',
            '论文', '报告', '开题', '答辩', '实验', '数据', '文献',
            '绩点', '成绩', '排名', '选课'
        ],

        # 🎮 游戏
        '游戏': list(set(
            [kw for keywords in game_keywords.values() for kw in keywords] + [
                '打游戏', '玩游戏', '开黑', '上分', '掉分', '匹配', '排位',
                '段位', '胜率', '连胜', '连败', '队友', '坑', '挂机',
                '版本', '更新', '补丁', '服务器', '国服', '国际服'
            ]
        )),

        # 🍜 饮食 / 吃喝
        '饮食': [
            '吃', '喝', '饭', '菜', '做饭', '点菜', '点外卖',
            '早餐', '午餐', '晚餐', '宵夜', '夜宵',
            '零食', '水果', '甜点',
            '火锅', '烧烤', '麻辣烫', '炸鸡', '烤肉', '拉面', '面条',
            '奶茶', '咖啡', '可乐', '饮料', '酒',
            '外卖', '饿', '好吃', '难吃', '撑了'
        ],

        # 🎬 娱乐 / 消遣
        '娱乐': [
            '电影', '电视剧', '剧', '综艺', '动漫', '番', '番剧',
            '视频', '直播', 'up主', '博主', '主播',
            'b站', 'B站', '抖音', '快手', '微博', '小红书',
            '音乐', '歌', '听歌', '单曲', '专辑',
            '演唱会', '音乐会'
        ],

        # 🏃 运动 / 身体活动
        '运动': [
            '运动', '锻炼', '健身', '健身房',
            '跑步', '慢跑', '夜跑',
            '篮球', '足球', '羽毛球', '乒乓球', '排球',
            '游泳', '骑车', '骑行', '爬山', '徒步',
            '拉伸', '力量', '有氧',
            '减肥', '瘦', '胖', '体重', '肌肉', '酸'
        ],

        # ❤️ 情感 / 心理状态
        '情感': [
            '开心', '高兴', '快乐', '幸福', '满足',
            '难过', '伤心', '失落', '低落', 'emo',
            '生气', '烦', '烦躁', '郁闷', '焦虑', '紧张',
            '害怕', '慌', '委屈', '崩溃', '累',
            '想你', '想念', '在乎', '喜欢', '爱',
            '感动', '失望', '后悔', '心烦'
        ],

        # 💼 工作 / 职业
        '工作': [
            '工作', '上班', '下班', '加班', '值班',
            '公司', '单位', '部门',
            '同事', '老板', '领导',
            '项目', '任务', '需求', '进度', '方案',
            '会议', '开会', '汇报', '总结',
            '出差', '请假', '调休',
            '工资', '薪水', '奖金', '绩效'
        ],

        # 🛒 购物 / 消费
        '购物': [
            '买', '购物', '下单', '付款', '退款',
            '淘宝', '京东', '拼多多', '闲鱼',
            '快递', '包裹', '物流', '签收',
            '衣服', '裤子', '鞋子', '外套',
            '包', '口红', '化妆品', '护肤品',
            '便宜', '贵', '划算', '打折', '促销'
        ],

        # 🏠 日常 / 生活琐事（强烈建议加）
        '生活': [
            '睡觉', '起床', '熬夜', '失眠', '困',
            '天气', '下雨', '下雪', '冷', '热',
            '回家', '出门', '在家',
            '洗澡', '洗头', '收拾', '打扫',
            '手机', '电脑', '网络', '没电'
        ]
    }

    topic_stats = {}
    for topic, keywords in topic_keywords.items():
        count = 0
        for keyword in keywords:
            count += all_text_clean.count(keyword)
        if count > 0:
            topic_stats[topic] = count

    topic_stats = dict(sorted(topic_stats.items(), key=lambda x: x[1], reverse=True))

    if topic_stats:
        total_topic_mentions = sum(topic_stats.values())
        print(f"话题关键词总计: {total_topic_mentions} 次\n")
        for topic, count in topic_stats.items():
            percentage = count / total_topic_mentions * 100
            bar_length = int(percentage / 2)
            bar = '█' * bar_length
            print(f"  {topic:6s}: {bar} {count:5d} 次 ({percentage:5.1f}%)")

    # 4. 情绪分析
    print(f"\n😄 情绪分析")
    print(f"{'-' * 60}")

    emotion_keywords = {
        '开心': {
            'keywords': ['哈哈', '嘿嘿', '嘻嘻', '哇', '耶', '棒', '赞', '好开心', '开心', '快乐', '高兴'],
            'emoji': ['/大笑', '/呲牙', '/愉快', '/开心', '/胜利']
        },
        '难过': {
            'keywords': ['呜呜', '呜呜呜', '哭', '难过', '伤心', '委屈', 'QAQ', 'T_T'],
            'emoji': ['/流泪', '/大哭', '/难过', '/委屈']
        },
        '生气': {
            'keywords': ['生气', '气死', '烦', '讨厌', '无语', '服了'],
            'emoji': ['/生气', '/愤怒', '/抓狂', '/吐血']
        },
        '惊讶': {
            'keywords': ['哇', '天哪', '我去', '卧槽', '牛', '厉害', '震惊'],
            'emoji': ['/惊讶', '/惊吓', '/吃惊', '/震惊']
        },
        '疑惑': {
            'keywords': ['？？', '啥', '什么鬼', '为啥', '为什么'],
            'emoji': ['/疑问', '/思考', '/困惑']
        },
        '无奈': {
            'keywords': ['唉', '算了', '无奈', '没办法'],
            'emoji': ['/捂脸', '/无奈', '/叹气']
        }
    }

    emotion_stats = {}
    person_emotions = {name: {} for name in df['name'].unique()}

    for emotion, patterns in emotion_keywords.items():
        total_count = 0

        for name in df['name'].unique():
            person_text = ' '.join(df[df['name'] == name]['message'].astype(str))
            count = 0

            for keyword in patterns['keywords']:
                count += person_text.count(keyword)

            for emoji in patterns['emoji']:
                count += person_text.count(emoji)

            person_emotions[name][emotion] = count
            total_count += count

        emotion_stats[emotion] = total_count

    emotion_stats = dict(sorted(emotion_stats.items(), key=lambda x: x[1], reverse=True))

    print("整体情绪分布:")
    total_emotions = sum(emotion_stats.values())
    if total_emotions > 0:
        for emotion, count in emotion_stats.items():
            percentage = count / total_emotions * 100
            print(f"  {emotion}: {count} 次 ({percentage:.1f}%)")

    print("\n个人情绪偏好:")
    for name in df['name'].unique():
        person_emotion_sorted = sorted(person_emotions[name].items(), key=lambda x: x[1], reverse=True)
        if person_emotion_sorted[0][1] > 0:
            top_emotion = person_emotion_sorted[0][0]
            print(f"  {name}: 最常表达 [{top_emotion}] 情绪 ({person_emotion_sorted[0][1]} 次)")

    return word_counter, None, topic_stats, emotion_stats, person_emotions


def generate_wordcloud(word_counter):
    """生成词云图"""
    if not word_counter:
        return None

    # Mac系统常见中文字体路径列表
    font_paths = [
        '/System/Library/Fonts/STHeiti Light.ttc',
        '/System/Library/Fonts/STHeiti Medium.ttc',
        '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
        '/Library/Fonts/Arial Unicode.ttf',
        '/System/Library/Fonts/PingFang.ttc',
    ]

    # 尝试找到可用的字体
    font_path = None
    for path in font_paths:
        import os
        if os.path.exists(path):
            font_path = path
            break

    if font_path is None:
        print("⚠️  未找到中文字体，词云可能无法显示中文")
        font_path = None  # 使用默认字体

    try:
        wordcloud = WordCloud(
            font_path=font_path,
            width=1200,
            height=600,
            background_color='white',
            colormap='viridis',
            max_words=100,
            relative_scaling=0.5,
            min_font_size=10
        ).generate_from_frequencies(word_counter)

        plt.figure(figsize=(15, 7.5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title(f'{ANALYSIS_YEAR}年度聊天词云', fontsize=20, fontweight='bold', pad=20)
        plt.tight_layout(pad=0)
        plt.savefig(f'wordcloud_{ANALYSIS_YEAR}.png', dpi=300, bbox_inches='tight', facecolor='white')
        print(f"☁️  词云图已保存")
        plt.close()
    except Exception as e:
        print(f"⚠️  词云生成失败: {e}")
        print("    继续生成其他报告...")


def create_visualizations(df, hour_dist, weekday_dist, month_dist, reply_stats, session_df, continuous_stats):
    """生成可视化图表"""
    fig = plt.figure(figsize=(18, 12))
    import matplotlib.gridspec as gridspec
    gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.3, wspace=0.3)

    fig.suptitle(f'{ANALYSIS_YEAR}年度聊天数据可视化报告', fontsize=18, fontweight='bold')

    ax1 = fig.add_subplot(gs[0, 0])
    person_counts = df['name'].value_counts()
    colors = ['#FF6B6B', '#4ECDC4']
    ax1.pie(person_counts.values, labels=person_counts.index, autopct='%1.1f%%',
            startangle=90, colors=colors)
    ax1.set_title('消息数量占比', fontweight='bold')

    ax2 = fig.add_subplot(gs[0, 1])
    ax2.bar(hour_dist.index, hour_dist.values, color='skyblue', edgecolor='navy', alpha=0.7)
    ax2.set_xlabel('小时')
    ax2.set_ylabel('消息数')
    ax2.set_title('24小时活跃度分布', fontweight='bold')
    ax2.set_xticks(range(0, 24, 2))
    ax2.grid(axis='y', alpha=0.3)

    ax3 = fig.add_subplot(gs[0, 2])
    weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    weekday_colors = ['#FF6B6B' if i < 5 else '#4ECDC4' for i in range(7)]
    ax3.bar(range(7), [weekday_dist.get(i, 0) for i in range(7)], color=weekday_colors, alpha=0.7)
    ax3.set_xlabel('星期')
    ax3.set_ylabel('消息数')
    ax3.set_title('星期活跃度分布', fontweight='bold')
    ax3.set_xticks(range(7))
    ax3.set_xticklabels(weekday_names)
    ax3.grid(axis='y', alpha=0.3)

    ax4 = fig.add_subplot(gs[1, :2])
    ax4.plot(month_dist.index, month_dist.values, marker='o', linewidth=3,
             markersize=10, color='#2ECC71', markerfacecolor='white',
             markeredgewidth=2, markeredgecolor='#2ECC71')
    ax4.fill_between(month_dist.index, month_dist.values, alpha=0.3, color='#2ECC71')
    ax4.set_xlabel('月份')
    ax4.set_ylabel('消息数')
    ax4.set_title('月度消息趋势', fontweight='bold')
    ax4.set_xticks(range(1, 13))
    ax4.grid(True, alpha=0.3)

    if reply_stats is not None and len(reply_stats) > 0:
        ax5 = fig.add_subplot(gs[1, 2])
        names = reply_stats.index
        avg_times = reply_stats['平均回复时间']
        bars = ax5.barh(names, avg_times, color=['#FF6B6B', '#4ECDC4'])
        ax5.set_xlabel('平均回复时间 (分钟)')
        ax5.set_title('回复速度对比', fontweight='bold')
        ax5.grid(axis='x', alpha=0.3)
        for i, (bar, val) in enumerate(zip(bars, avg_times)):
            ax5.text(val, i, f' {val:.1f}分', va='center')

    if session_df is not None and len(session_df) > 0:
        ax6 = fig.add_subplot(gs[2, 0])
        ax6.hist(session_df['rounds'], bins=20, color='#9B59B6', alpha=0.7, edgecolor='black')
        ax6.set_xlabel('对话轮次')
        ax6.set_ylabel('频次')
        ax6.set_title('对话轮次分布', fontweight='bold')
        ax6.axvline(session_df['rounds'].mean(), color='red', linestyle='--',
                    linewidth=2, label=f'平均: {session_df["rounds"].mean():.1f}轮')
        ax6.legend()
        ax6.grid(axis='y', alpha=0.3)

    if continuous_stats:
        ax7 = fig.add_subplot(gs[2, 1])
        names = list(continuous_stats.keys())
        init_counts = [continuous_stats[name]['init_count'] for name in names]  # 注意：你上面 return 的 dict 变量名如果改了，这里也跟着改
        bars = ax7.bar(names, init_counts, color=['#FF6B6B', '#4ECDC4'], alpha=0.7)
        ax7.set_ylabel('发起次数')
        ax7.set_title('话题主导性对比', fontweight='bold')
        ax7.grid(axis='y', alpha=0.3)
        for bar, val in zip(bars, init_counts):
            height = bar.get_height()
            ax7.text(bar.get_x() + bar.get_width() / 2., height,
                     f'{val:.1f}', ha='center', va='bottom')

    if session_df is not None and len(session_df) > 0:
        ax8 = fig.add_subplot(gs[2, 2])
        duration_data = session_df[session_df['duration'] <= 120]['duration']
        ax8.hist(duration_data, bins=30, color='#F39C12', alpha=0.7, edgecolor='black')
        ax8.set_xlabel('对话时长 (分钟)')
        ax8.set_ylabel('频次')
        ax8.set_title('单次对话时长分布', fontweight='bold')
        ax8.axvline(duration_data.mean(), color='red', linestyle='--',
                    linewidth=2, label=f'平均: {duration_data.mean():.1f}分')
        ax8.legend()
        ax8.grid(axis='y', alpha=0.3)

    plt.savefig(f'chat_analysis_{ANALYSIS_YEAR}.png', dpi=300, bbox_inches='tight')
    print(f"📊 数据图表已保存")
    plt.close()


def generate_html_report(df, person_stats, game_stats, topic_stats, emotion_stats, person_emotions, word_counter):
    """生成HTML报告"""

    total_messages = len(df)
    total_days = df['date'].nunique()
    date_range = f"{df['datetime'].min().strftime('%Y-%m-%d')} 至 {df['datetime'].max().strftime('%Y-%m-%d')}"

    # 生成词频表格
    word_table_rows = ""
    for i, (word, count) in enumerate(word_counter.most_common(20), 1):
        word_table_rows += f"<tr><td>{i}</td><td>{word}</td><td>{count}</td></tr>\n"

    # 生成游戏统计
    game_rows = ""
    if game_stats:
        total_game = sum(game_stats.values())
        for game, count in game_stats.items():
            percentage = count / total_game * 100
            game_rows += f"<tr><td>{game}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>\n"
    else:
        game_rows = '<tr><td colspan="3" style="text-align:center; color:#999;">未检测到游戏相关话题</td></tr>'

    # 生成话题统计
    topic_rows = ""
    if topic_stats:
        total_topic = sum(topic_stats.values())
        for topic, count in topic_stats.items():
            percentage = count / total_topic * 100
            bar_width = percentage
            topic_rows += f"""
            <tr>
                <td>{topic}</td>
                <td>{count}</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {bar_width}%"></div>
                        <span class="progress-text">{percentage:.1f}%</span>
                    </div>
                </td>
            </tr>"""

    # 生成情绪统计
    emotion_rows = ""
    if emotion_stats:
        total_emotion = sum(emotion_stats.values())
        emotion_colors = {
            '开心': '#FFD93D', '难过': '#6BCB77', '生气': '#FF6B6B',
            '惊讶': '#4D96FF', '疑惑': '#9D84B7', '无奈': '#95B8D1'
        }
        for emotion, count in emotion_stats.items():
            percentage = count / total_emotion * 100
            color = emotion_colors.get(emotion, '#999')
            emotion_rows += f"""
            <tr>
                <td><span class="emotion-tag" style="background-color: {color}">{emotion}</span></td>
                <td>{count}</td>
                <td>{percentage:.1f}%</td>
            </tr>"""

    # 个人统计卡片
    person_cards = ""
    for name, row in person_stats.iterrows():
        person_cards += f"""
        <div class="person-card">
            <h3>{name}</h3>
            <div class="stat-item">
                <span class="stat-label">发送消息</span>
                <span class="stat-value">{int(row['消息数'])} 条</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">占比</span>
                <span class="stat-value">{row['占比']}%</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">平均长度</span>
                <span class="stat-value">{row['平均消息长度']:.1f} 字</span>
            </div>
        </div>"""

    # 完整HTML内容
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{ANALYSIS_YEAR}年度聊天分析报告</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'PingFang SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 50px 40px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .content {{
            padding: 40px;
        }}
        .section {{
            margin-bottom: 50px;
        }}
        .section-title {{
            font-size: 1.8em;
            color: #333;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
            display: flex;
            align-items: center;
        }}
        .section-title::before {{
            content: '';
            width: 5px;
            height: 30px;
            background: #667eea;
            margin-right: 15px;
            border-radius: 3px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        .stat-card h3 {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
        }}
        .stat-card .value {{
            font-size: 2em;
            color: #667eea;
            font-weight: bold;
        }}
        .person-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}
        .person-card {{
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }}
        .person-card h3 {{
            color: #667eea;
            font-size: 1.5em;
            margin-bottom: 20px;
        }}
        .stat-item {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #f0f0f0;
        }}
        .stat-item:last-child {{
            border-bottom: none;
        }}
        .stat-label {{
            color: #666;
        }}
        .stat-value {{
            color: #333;
            font-weight: bold;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }}
        th, td {{
            padding: 15px;
            text-align: left;
        }}
        th {{
            background: #667eea;
            color: white;
            font-weight: 600;
        }}
        tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        tr:hover {{
            background: #e8f4f8;
        }}
        .progress-bar {{
            width: 100%;
            height: 25px;
            background: #e0e0e0;
            border-radius: 12px;
            overflow: hidden;
            position: relative;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.5s ease;
        }}
        .progress-text {{
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            color: #333;
            font-weight: bold;
            font-size: 0.9em;
        }}
        .emotion-tag {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            color: white;
            font-weight: bold;
        }}
        .image-container {{
            text-align: center;
            margin: 30px 0;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 15px;
        }}
        .image-container img {{
            max-width: 100%;
            border-radius: 10px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }}
        .footer {{
            background: #f8f9fa;
            padding: 30px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {ANALYSIS_YEAR}年度聊天分析报告</h1>
            <p>深度解析你们的聊天数据</p>
        </div>

        <div class="content">
            <!-- 基础统计 -->
            <div class="section">
                <h2 class="section-title">📈 基础数据</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>统计时间段</h3>
                        <div class="value" style="font-size: 1.2em;">{date_range}</div>
                    </div>
                    <div class="stat-card">
                        <h3>总消息数</h3>
                        <div class="value">{total_messages:,}</div>
                    </div>
                    <div class="stat-card">
                        <h3>聊天天数</h3>
                        <div class="value">{total_days}</div>
                    </div>
                    <div class="stat-card">
                        <h3>日均消息</h3>
                        <div class="value">{total_messages / total_days:.1f}</div>
                    </div>
                </div>
            </div>

            <!-- 个人统计 -->
            <div class="section">
                <h2 class="section-title">👥 个人数据</h2>
                <div class="person-grid">
                    {person_cards}
                </div>
            </div>

            <!-- 高频词 -->
            <div class="section">
                <h2 class="section-title">💬 高频词 TOP 20</h2>
                <table>
                    <thead>
                        <tr>
                            <th>排名</th>
                            <th>词语</th>
                            <th>出现次数</th>
                        </tr>
                    </thead>
                    <tbody>
                        {word_table_rows}
                    </tbody>
                </table>
            </div>

            <!-- 词云图 -->
            <div class="section">
                <h2 class="section-title">☁️ 词云图</h2>
                <div class="image-container">
                    <img src="wordcloud_{ANALYSIS_YEAR}.png" alt="词云图">
                </div>
            </div>

            <!-- 游戏统计 -->
            <div class="section">
                <h2 class="section-title">🎮 游戏话题统计</h2>
                <table>
                    <thead>
                        <tr>
                            <th>游戏名称</th>
                            <th>提及次数</th>
                            <th>占比</th>
                        </tr>
                    </thead>
                    <tbody>
                        {game_rows}
                    </tbody>
                </table>
            </div>

            <!-- 话题分类 -->
            <div class="section">
                <h2 class="section-title">📚 话题分类统计</h2>
                <table>
                    <thead>
                        <tr>
                            <th>话题类别</th>
                            <th>提及次数</th>
                            <th>占比</th>
                        </tr>
                    </thead>
                    <tbody>
                        {topic_rows}
                    </tbody>
                </table>
            </div>

            <!-- 情绪分析 -->
            <div class="section">
                <h2 class="section-title">😊 情绪分析</h2>
                <table>
                    <thead>
                        <tr>
                            <th>情绪类型</th>
                            <th>出现次数</th>
                            <th>占比</th>
                        </tr>
                    </thead>
                    <tbody>
                        {emotion_rows}
                    </tbody>
                </table>
            </div>

            <!-- 可视化图表 -->
            <div class="section">
                <h2 class="section-title">📊 数据可视化</h2>
                <div class="image-container">
                    <img src="chat_analysis_{ANALYSIS_YEAR}.png" alt="数据可视化图表">
                </div>
            </div>
        </div>

        <div class="footer">
            <p>🎉 报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>💝 珍惜每一次对话，记录美好时光</p>
        </div>
    </div>
</body>
</html>"""

    filename = f'chat_report_{ANALYSIS_YEAR}.html'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"🎨 HTML报告已生成")

def _pick_cjk_font(font_size: int):
    """
    尽量选择支持中文的字体。Mac 优先 PingFang，其次 Arial Unicode。
    找不到就退化到默认字体（可能不支持中文，会变方块）。
    """
    candidate_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "/Library/Fonts/Arial Unicode MS.ttf",
    ]
    for p in candidate_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, font_size)
            except Exception:
                pass
    try:
        return ImageFont.truetype("Arial Unicode MS", font_size)
    except Exception:
        return ImageFont.load_default()


def save_text_report_as_png(
    report_text: str,
    out_path: str,
    width: int = 1400,
    font_size: int = 24,
    margin: int = 50,
    line_spacing: float = 1.35,
    bg_color=(255, 255, 255),
    text_color=(0, 0, 0),
):
    """
    将控制台文本报告渲染成一张“长图PNG”
    - 自动换行（按像素宽度）
    - 自动计算高度
    """
    font = _pick_cjk_font(font_size)
    tmp_img = Image.new("RGB", (width, 100), bg_color)
    draw = ImageDraw.Draw(tmp_img)

    max_text_width = width - 2 * margin

    # 逐段处理：保留空行、分隔线等
    lines = []
    for raw_line in report_text.splitlines():
        if raw_line.strip() == "":
            lines.append("")  # 空行保留
            continue

        # 按像素宽度进行自动换行
        cur = ""
        for ch in raw_line:
            test = cur + ch
            if draw.textlength(test, font=font) <= max_text_width:
                cur = test
            else:
                lines.append(cur)
                cur = ch
        if cur:
            lines.append(cur)

    # 行高
    ascent, descent = font.getmetrics()
    base_line_h = ascent + descent
    line_h = int(base_line_h * line_spacing)

    height = margin * 2 + line_h * len(lines)
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    y = margin
    for line in lines:
        draw.text((margin, y), line, font=font, fill=text_color)
        y += line_h

    img.save(out_path)
    print(f"🖼️ 长图PNG已生成: {out_path}")



def main():
    """主函数"""
    try:
        print(f"正在加载 {ANALYSIS_YEAR} 年的聊天记录...")
        df = load_and_clean_data(FILE_PATH, ANALYSIS_YEAR)

        if len(df) == 0:
            print(f"❌ 未找到 {ANALYSIS_YEAR} 年的聊天记录！")
            return

        buf = io.StringIO()
        with redirect_stdout(buf):
            person_stats = basic_statistics(df)
            hour_dist, weekday_dist, month_dist = time_analysis(df)
            reply_stats, session_df, continuous_stats, emoji_counter = interaction_analysis(df)
            word_counter, game_stats, topic_stats, emotion_stats, person_emotions = content_deep_analysis(df)

        report_text = buf.getvalue()

        # 生成“总结长图”
        summary_png = f"chat_summary_{ANALYSIS_YEAR}.png"
        save_text_report_as_png(
            report_text=report_text,
            out_path=summary_png,
            width=1400,
            font_size=24,
            margin=50
        )

        # 你原来的可视化图、词云仍然可以保留
        print(f"\n{'=' * 60}")
        print("🎨 正在生成可视化内容...")
        generate_wordcloud(word_counter)
        create_visualizations(df, hour_dist, weekday_dist, month_dist, reply_stats, session_df, continuous_stats)

        # ====== 2) 不要HTML就注释掉 ======
        # generate_html_report(df, person_stats, game_stats, topic_stats, emotion_stats, person_emotions, word_counter)

        print(f"\n{'=' * 60}")
        print("✅ 所有分析报告生成完成！")
        print(f"{'=' * 60}")
        print("\n生成的文件:")
        print(f"  🖼️ chat_summary_{ANALYSIS_YEAR}.png - 总结长图（纯图片）")
        print(f"  📊 chat_analysis_{ANALYSIS_YEAR}.png - 数据图表")
        print(f"  ☁️  wordcloud_{ANALYSIS_YEAR}.png - 词云图")

    except FileNotFoundError:
        print(f"❌ 错误: 找不到文件 {FILE_PATH}")
        print("请检查文件路径是否正确！")
    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()