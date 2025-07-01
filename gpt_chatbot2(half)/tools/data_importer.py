#!/usr/bin/env python3
"""
快速修复版数据导入工具
解决模块导入问题
"""
import sys
import os
import re
import argparse

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print(f"📁 项目根目录: {project_root}")
print(f"🔍 Python路径: {sys.path[:3]}")

# 检查并导入RAG服务
try:
    from services.rag_service import get_rag_service
    print("✅ RAG服务导入成功")
    RAG_AVAILABLE = True
except ImportError as e:
    print(f"❌ RAG服务导入失败: {e}")
    print("💡 请确保已按照指南创建了 services/rag_service.py 文件")
    RAG_AVAILABLE = False

def check_environment():
    """检查环境和依赖"""
    print("\n🔍 环境检查:")
    
    # 检查目录结构
    required_dirs = ['services', 'tools', 'templates', 'static']
    for dir_name in required_dirs:
        dir_path = os.path.join(project_root, dir_name)
        if os.path.exists(dir_path):
            print(f"✅ 目录存在: {dir_name}/")
        else:
            print(f"❌ 目录缺失: {dir_name}/")
    
    # 检查关键文件
    key_files = ['app.py', 'services/rag_service.py']
    for file_name in key_files:
        file_path = os.path.join(project_root, file_name)
        if os.path.exists(file_path):
            print(f"✅ 文件存在: {file_name}")
        else:
            print(f"❌ 文件缺失: {file_name}")
    
    # 检查依赖包
    required_packages = ['chromadb', 'sentence_transformers', 'jieba']
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ 包已安装: {package}")
        except ImportError:
            print(f"❌ 包未安装: {package}")
    
    return RAG_AVAILABLE

def parse_qa_text(text_content: str):
    """解析问答文本格式"""
    qa_pairs = []
    lines = text_content.split('\n')
    current_q = None
    current_a = None
    
    print(f"🔍 开始解析文本，共 {len(lines)} 行")
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        
        # 跳过空行和注释
        if not line or line.startswith('#'):
            continue
        
        # 匹配问题行 - 支持多种格式
        if re.match(r'^问[：:]', line) or re.match(r'^Q[：:]', line, re.IGNORECASE):
            # 保存之前的问答对
            if current_q and current_a:
                qa_pairs.append({
                    'question': current_q.strip(),
                    'answer': current_a.strip()
                })
            
            # 提取新问题
            current_q = re.sub(r'^[问Q][：:]', '', line, flags=re.IGNORECASE).strip()
            current_a = None
            
        # 匹配答案行
        elif re.match(r'^答[：:]', line) or re.match(r'^A[：:]', line, re.IGNORECASE):
            current_a = re.sub(r'^[答A][：:]', '', line, flags=re.IGNORECASE).strip()
            
        # 续行处理
        elif current_a is not None and line:
            current_a += " " + line
        elif current_q is not None and current_a is None and line:
            current_q += " " + line
    
    # 处理最后一对问答
    if current_q and current_a:
        qa_pairs.append({
            'question': current_q.strip(),
            'answer': current_a.strip()
        })
    
    print(f"✅ 解析完成，共找到 {len(qa_pairs)} 对问答")
    
    # 显示前3个问答作为预览
    if qa_pairs:
        print("\n📝 数据预览:")
        for i, qa in enumerate(qa_pairs[:3], 1):
            print(f"{i}. Q: {qa['question'][:50]}...")
            print(f"   A: {qa['answer'][:50]}...")
        if len(qa_pairs) > 3:
            print(f"   ... 还有 {len(qa_pairs) - 3} 条数据")
    
    return qa_pairs

def parse_json_file(file_path: str):
    """解析JSON文件"""
    import json
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
        
        # 标准化字段名
        standardized_data = []
        for item in qa_data:
            if isinstance(item, dict):
                question = (item.get('question') or 
                          item.get('q') or 
                          item.get('问题') or "")
                
                answer = (item.get('answer') or 
                        item.get('a') or 
                        item.get('答案') or "")
                
                if question and answer:
                    standardized_data.append({
                        'question': str(question).strip(),
                        'answer': str(answer).strip(),
                        'category': item.get('category', item.get('类别', ''))
                    })
        
        print(f"✅ JSON解析完成，有效问答对: {len(standardized_data)}")
        return standardized_data
        
    except Exception as e:
        print(f"❌ JSON解析失败: {e}")
        return []

def parse_csv_file(file_path: str):
    """解析CSV文件"""
    try:
        import pandas as pd
        
        # 尝试不同编码
        encodings = ['utf-8', 'gbk', 'gb2312']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                print(f"✅ 使用编码 {encoding} 读取CSV文件成功")
                break
            except UnicodeDecodeError:
                continue
        
        if df is None:
            print("❌ 无法读取CSV文件")
            return []
        
        qa_data = []
        
        # 列名映射
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
            print(f"❌ CSV文件缺少必要列")
            print(f"可用列: {list(df.columns)}")
            return []
        
        for _, row in df.iterrows():
            question = str(row[question_col]).strip()
            answer = str(row[answer_col]).strip()
            
            if question != 'nan' and answer != 'nan' and question and answer:
                qa_data.append({
                    'question': question,
                    'answer': answer
                })
        
        print(f"✅ CSV解析完成，有效问答对: {len(qa_data)}")
        return qa_data
        
    except ImportError:
        print("❌ 需要安装pandas: pip install pandas")
        return []
    except Exception as e:
        print(f"❌ CSV解析失败: {e}")
        return []

def import_to_rag(qa_data):
    """导入数据到RAG系统"""
    if not RAG_AVAILABLE:
        print("❌ RAG服务不可用，无法导入数据")
        return False
    
    try:
        print(f"🚀 开始导入 {len(qa_data)} 条数据到RAG系统...")
        rag_service = get_rag_service()
        result = rag_service.load_qa_data(qa_data)
        
        print(f"\n🎉 导入完成！")
        print(f"✅ 成功导入: {result['success']} 条")
        print(f"❌ 导入失败: {result['error']} 条")
        
        # 显示知识库统计
        stats = rag_service.get_collection_stats()
        print(f"📊 知识库统计:")
        print(f"   总文档数: {stats['total_documents']}")
        print(f"   状态: {stats['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 导入RAG系统失败: {e}")
        return False

def save_parsed_data(qa_data, output_file):
    """保存解析后的数据"""
    import json
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(qa_data, f, ensure_ascii=False, indent=2)
        print(f"💾 数据已保存到: {output_file}")
    except Exception as e:
        print(f"❌ 保存数据失败: {e}")

def main():
    parser = argparse.ArgumentParser(description='快速数据导入工具')
    parser.add_argument('file_path', help='数据文件路径')
    parser.add_argument('--type', choices=['text', 'json', 'csv', 'auto'], 
                       default='auto', help='文件类型')
    parser.add_argument('--check-env', action='store_true', help='只检查环境')
    parser.add_argument('--save-parsed', help='保存解析后的数据到指定文件')
    parser.add_argument('--dry-run', action='store_true', help='只解析不导入')
    
    args = parser.parse_args()
    
    # 环境检查
    print("🔧 快速数据导入工具")
    env_ok = check_environment()
    
    if args.check_env:
        return
    
    # 检查文件
    if not os.path.exists(args.file_path):
        print(f"❌ 文件不存在: {args.file_path}")
        return
    
    print(f"\n📁 处理文件: {args.file_path}")
    
    # 自动检测文件类型
    file_ext = os.path.splitext(args.file_path)[1].lower()
    if args.type == 'auto':
        if file_ext == '.json':
            args.type = 'json'
        elif file_ext == '.csv':
            args.type = 'csv'
        else:
            args.type = 'text'
        print(f"🔍 自动检测文件类型: {args.type}")
    
    # 解析数据
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
    
    # 保存解析后的数据
    if args.save_parsed:
        save_parsed_data(qa_data, args.save_parsed)
    
    # 导入到RAG系统
    if not args.dry_run:
        if env_ok:
            success = import_to_rag(qa_data)
            if success:
                print("\n✅ 数据导入成功！您现在可以测试AI客服的增强效果了。")
        else:
            print("\n⚠️ 环境未就绪，跳过RAG导入")
            print("💡 请先按照指南创建必要的文件")
    else:
        print("\n🔍 这是预览模式，数据未实际导入")

if __name__ == "__main__":
    main()