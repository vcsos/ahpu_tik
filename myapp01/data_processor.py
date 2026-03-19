import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tik.settings")

# 初始化 Django
django.setup()
import pandas as pd
import jieba
import pymysql
from sqlalchemy import create_engine
#from snownlp import SnowNLP


# 从 MySQL 加载数据
def load_data_from_mysql(mysql_config, table_name):
    try:
        engine = create_engine(
            f"mysql+pymysql://{mysql_config['user']}:{mysql_config['password']}@"
            f"{mysql_config['host']}:{mysql_config['port']}/"
            f"{mysql_config['database']}?charset=utf8mb4"
        )
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        print(f"从 MySQL 加载数据时发生错误：{str(e)}")
        return None


# 去重和去缺失值
def remove_duplicates_and_nans(df, column):
    return df.dropna(subset=[column]).drop_duplicates(subset=[column])


# 清洗评论
def clean_comments(df, comment_column):
    cleaned_column = '清洗评论'
    df[cleaned_column] = df[comment_column].str.replace(r'\[.*?\]', '', regex=True)
    df[cleaned_column] = df[cleaned_column].str.replace(r'[^\w\s]', '', regex=True)
    df[cleaned_column] = df[cleaned_column].str.replace(r'\s+', ' ', regex=True)
    df[cleaned_column] = df[cleaned_column].str.strip()
    df[cleaned_column] = df[cleaned_column].str.replace(r'[0-9a-zA-Z]+', '', regex=True)
    df[cleaned_column] = df[cleaned_column].replace(r'^\s*$', pd.NA, regex=True)
    df = df.dropna(subset=[cleaned_column])
    df = df.drop_duplicates(subset=[cleaned_column])
    print('数据清洗成功！')
    return df


# 处理日期
def process_date(df, date_column):
    df[date_column] = pd.to_datetime(df[date_column])
    df['time'] = df[date_column].dt.strftime('%H:%M:%S')
    df['年月日'] = df[date_column].dt.strftime('%Y-%m-%d')
    return df


# 加载停用词
def load_stopwords(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return set(f.read().split())


# 中文分词
def chinese_segment(text, stopwords):
    words = jieba.cut(text)
    filtered_words = [word for word in words if word not in stopwords and len(word) > 1]
    return ' '.join(filtered_words)


# 情感分析
# def sentiment_analysis(text):
#     s = SnowNLP(text)
#     sentiment_score = s.sentiments
#     if sentiment_score > 0.7:
#         return '积极'
#     elif sentiment_score < 0.3:
#         return '消极'
#     else:
#         return '中性'


# 新增导入热榜模型
from myapp01.models import HotBoard


def save_to_mysql(df, mysql_config, table_name):
    try:
        # 定义允许的字段列表（新增 hot_board_id 和 年月日 和 sentiment）
        allowed_columns = [
            'id', 'nickname', 'region', 'comment_date',
            'content', 'like_count', 'hot_board_id',
            '清洗评论', 'time', '分词', '年月日', 'sentiment'
        ]
        # 过滤不在白名单中的列
        df = df.loc[:, df.columns.isin(allowed_columns)]

        connection = pymysql.connect(
            host=mysql_config['host'],
            port=mysql_config['port'],
            user=mysql_config['user'],
            password=mysql_config['password'],
            database=mysql_config['database'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        # 建表语句（包含热榜关联字段和 年月日 和 sentiment）
        columns_def = [
            "`id` BIGINT",
            "`nickname` VARCHAR(255)",
            "`region` VARCHAR(255)",
            "`comment_date` DATETIME",
            "`content` TEXT",
            "`like_count` INT",
            "`hot_board_id` BIGINT",  # 热榜关联字段
            "`清洗评论` TEXT",
            "`time` VARCHAR(20)",
            "`分词` TEXT",
            "`年月日` VARCHAR(10)",
            "`sentiment` VARCHAR(10)"
        ]
        create_table_query = f"CREATE TABLE IF NOT EXISTS `{table_name}` ({', '.join(columns_def)})"

        with connection.cursor() as cursor:
            # 创建表
            cursor.execute(create_table_query)

            # 检查是否存在 年月日 列，如果不存在则添加
            cursor.execute(f"SHOW COLUMNS FROM `{table_name}` LIKE '年月日'")
            if not cursor.fetchone():
                cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN `年月日` VARCHAR(10)")

            # 检查是否存在 sentiment 列，如果不存在则添加
            cursor.execute(f"SHOW COLUMNS FROM `{table_name}` LIKE 'sentiment'")
            if not cursor.fetchone():
                cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN `sentiment` VARCHAR(10)")

            # 清空表
            cursor.execute(f"TRUNCATE TABLE `{table_name}`")

            # 插入数据
            columns = ', '.join(df.columns)
            values_placeholders = ', '.join(['%s'] * len(df.columns))
            insert_query = f"INSERT INTO `{table_name}` ({columns}) VALUES ({values_placeholders})"
            for row in df.values.tolist():
                # 验证热榜关联有效性
                hot_board_id = row[df.columns.get_loc('hot_board_id')]
                if not HotBoard.objects.filter(id=hot_board_id).exists():
                    print(f"警告：热榜ID {hot_board_id} 不存在，跳过该记录")
                    continue
                cursor.execute(insert_query, row)

        connection.commit()
        print(f"数据存储到 MySQL 表 {table_name} 成功！")
    except Exception as e:
        print(f"保存到 MySQL 时发生错误：{str(e)}")
    finally:
        if connection:
            connection.close()


# 保存清洗后的数据到 CSV 文件
def save_to_csv(df, file_name):
    try:
        df.to_csv(file_name, index=False, encoding='utf-8-sig')
        print(f"数据保存到 CSV 文件 {file_name} 成功！")
    except Exception as e:
        print(f"保存到 CSV 文件时发生错误：{str(e)}")


def main():
    mysql_config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': 'root123',
        'database': 'tik'
    }
    tables = [
        'myapp01_commenthot1',
        'myapp01_commenthot2',
        'myapp01_commenthot3',
        'myapp01_commenthot4',
        'myapp01_commenthot5'
    ]

    for table in tables:
        df = load_data_from_mysql(mysql_config, table)
        if df is None or df.empty:
            print(f"表 {table} 无数据或加载失败，跳过处理")
            continue

        # 数据清洗
        df = remove_duplicates_and_nans(df, 'content')
        df = clean_comments(df, 'content')
        df = process_date(df, 'comment_date')

        # 分词处理
        stopwords = load_stopwords('stopwords.txt')
        df['分词'] = df['清洗评论'].apply(lambda x: chinese_segment(x, stopwords))

        # 情感分析
       # df['sentiment'] = df['清洗评论'].apply(sentiment_analysis)

        # 保留热榜关联字段
        if 'hot_board_id' not in df.columns:
            print(f"表 {table} 缺少 hot_board_id 字段，无法关联热榜")
            continue

        # 保存到 CSV 文件
        # csv_file_name = f"/myapp01/data/csv/{table}_processed.csv"
        # save_to_csv(df, csv_file_name)

        # 保存到 MySQL
        new_table_name = f"{table}_processed"
        save_to_mysql(df, mysql_config, new_table_name)


if __name__ == "__main__":
    main()
