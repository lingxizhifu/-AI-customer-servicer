#!/usr/bin/env python3
"""
MySQL版数据导入工具
支持txt/json/csv格式问答数据导入到MySQL数据库
"""
import sys
import os
import re
import argparse
import json
import hashlib
from datetime import datetime
import importlib.util

# 依赖pymysql
try:
    import pymysql
except ImportError:
    print("❌ 需要安装pymysql: pip install pymysql")
    sys.exit(1)
try:
    import jieba
except ImportError:
    print("❌ 需要安装jieba: pip install jieba")
    sys.exit(1)

# ================== 数据解析 ==================
def parse_qa_text(text_content: str):
    """解析问答文本格式"""
    qa_pairs = []
    lines = text_content.split('\n')
    current_q = None
    current_a = None
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if re.match(r'^问[：:]', line) or re.match(r'^Q[：:]', line, re.IGNORECASE):
            if current_q and current_a:
                qa_pairs.append({'question': current_q.strip(), 'answer': current_a.strip()})
            current_q = re.sub(r'^[问Q][：:]', '', line, flags=re.IGNORECASE).strip()
            current_a = None
        elif re.match(r'^答[：:]', line) or re.match(r'^A[：:]', line, re.IGNORECASE):
            current_a = re.sub(r'^[答A][：:]', '', line, flags=re.IGNORECASE).strip()
        elif current_a is not None and line:
            current_a += " " + line
        elif current_q is not None and current_a is None and line:
            current_q += " " + line
    if current_q and current_a:
        qa_pairs.append({'question': current_q.strip(), 'answer': current_a.strip()})
    return qa_pairs

def parse_json_file(file_path: str):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        qa_data = []
        if isinstance(data, list):
            qa_data = data
        elif isinstance(data, dict):
            if 'qa_pairs' in data:
                qa_data = data['qa_pairs']
            elif 'data' in data:
                qa_data = data['data']
            else:
                qa_data = [data]
        standardized_data = []
        for item in qa_data:
            if isinstance(item, dict):
                question = (item.get('question') or item.get('q') or item.get('问题') or "")
                answer = (item.get('answer') or item.get('a') or item.get('答案') or "")
                if question and answer:
                    standardized_data.append({
                        'question': str(question).strip(),
                        'answer': str(answer).strip(),
                        'category': item.get('category', item.get('类别', ''))
                    })
        return standardized_data
    except Exception as e:
        print(f"❌ JSON解析失败: {e}")
        return []

def parse_csv_file(file_path: str):
    try:
        import pandas as pd
        encodings = ['utf-8', 'gbk', 'gb2312']
        df = None
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        if df is None:
            print("❌ 无法读取CSV文件")
            return []
        qa_data = []
        question_cols = ['question', '问题', 'q', 'Question']
        answer_cols = ['answer', '答案', 'a', 'Answer']
        question_col = None
        answer_col = None
        for col in df.columns:
            if col in question_cols:
                question_col = col
            if col in answer_cols:
                answer_col = col
        if not question_col or not answer_col:
            print(f"❌ CSV文件缺少必要列, 可用列: {list(df.columns)}")
            return []
        for _, row in df.iterrows():
            question = str(row[question_col]).strip()
            answer = str(row[answer_col]).strip()
            if question != 'nan' and answer != 'nan' and question and answer:
                qa_data.append({'question': question, 'answer': answer})
        return qa_data
    except ImportError:
        print("❌ 需要安装pandas: pip install pandas")
        return []
    except Exception as e:
        print(f"❌ CSV解析失败: {e}")
        return []

# ================== MySQL导入 ==================
def ensure_table_exists(conn, table):
    with conn.cursor() as cursor:
        cursor.execute(f"""
CREATE TABLE IF NOT EXISTS {table} (
    id VARCHAR(32) PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(64),
    question_tokens TEXT,
    tone_id INT,
    created_at DATETIME
)
""")
    conn.commit()

def ensure_question_tokens_column(conn, table):
    with conn.cursor() as cursor:
        cursor.execute(f"SHOW COLUMNS FROM {table} LIKE 'question_tokens'")
        if not cursor.fetchone():
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN question_tokens TEXT")
            print(f"✅ 已自动添加 question_tokens 字段")
    conn.commit()

def import_to_mysql(qa_data, mysql_config, table, tone_id):
    conn = pymysql.connect(**mysql_config)
    ensure_table_exists(conn, table)
    ensure_question_tokens_column(conn, table)
    with conn.cursor() as cursor:
        for qa in qa_data:
            question = qa.get('question', '').strip()
            answer = qa.get('answer', '').strip()
            category = qa.get('category', '')
            if not question or not answer:
                continue
            qa_id = hashlib.md5((question + answer).encode('utf-8')).hexdigest()[:16]
            tokens = ' '.join([w for w in jieba.cut(question) if len(w.strip()) > 1])
            cursor.execute(
                f"REPLACE INTO {table} (id, question, answer, category, question_tokens, tone_id, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (qa_id, question, answer, category, tokens, tone_id, datetime.now())
            )
    conn.commit()
    print(f"✅ 成功导入 {len(qa_data)} 条数据到MySQL表 {table}")
    conn.close()

# ================== 主流程 ==================
def main():
    parser = argparse.ArgumentParser(description='MySQL数据导入工具')
    parser.add_argument('file_path', help='数据文件路径')
    parser.add_argument('--type', choices=['text', 'json', 'csv', 'auto'], default='auto', help='文件类型')
    parser.add_argument('--mysql-host', default='localhost')
    parser.add_argument('--mysql-port', type=int, default=3306)
    parser.add_argument('--mysql-user', default='root')
    parser.add_argument('--mysql-password', default='')
    parser.add_argument('--mysql-db', default='ragdb')
    parser.add_argument('--mysql-table', default='qa_data')
    parser.add_argument('--tone-id', type=int, default=None, help='指定语气id')
    args = parser.parse_args()

    if not os.path.exists(args.file_path):
        print(f"❌ 文件不存在: {args.file_path}")
        return
    file_ext = os.path.splitext(args.file_path)[1].lower()
    if args.type == 'auto':
        if file_ext == '.json':
            args.type = 'json'
        elif file_ext == '.csv':
            args.type = 'csv'
        else:
            args.type = 'text'
        print(f"🔍 自动检测文件类型: {args.type}")
    qa_data = []
    if args.type == 'text':
        with open(args.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        qa_data = parse_qa_text(content)
    elif args.type == 'json':
        qa_data = parse_json_file(args.file_path)
    elif args.type == 'csv':
        qa_data = parse_csv_file(args.file_path)
    if not qa_data:
        print("❌ 没有解析到有效数据")
        return
    mysql_config = {
        'host': args.mysql_host,
        'port': args.mysql_port,
        'user': args.mysql_user,
        'password': args.mysql_password,
        'database': args.mysql_db,
        'charset': 'utf8mb4'
    }
    import_to_mysql(qa_data, mysql_config, args.mysql_table, args.tone_id)

if __name__ == "__main__":
    main() 