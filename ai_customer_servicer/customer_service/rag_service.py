"""
离线版RAG服务 - 无需外部模型依赖
使用传统文本相似度算法，避免网络连接问题
"""
import os
import json
import re
import jieba
import sqlite3
import hashlib
from typing import List, Dict, Tuple
from datetime import datetime
from collections import Counter
import math
import pymysql
import importlib.util

MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'ai_chat_db',
    'charset': 'utf8mb4'
}

def get_db_config():
    settings_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ai_customer_servicer', 'settings.py')
    spec = importlib.util.spec_from_file_location('settings', settings_path)
    settings = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(settings)
    db = settings.DATABASES['default']
    return {
        'host': db.get('HOST', 'localhost'),
        'port': int(db.get('PORT', 3306)),
        'user': db.get('USER', 'root'),
        'password': db.get('PASSWORD', '123456'),
        'database': db.get('NAME', 'ai_chat_db'),
        'charset': db.get('OPTIONS', {}).get('charset', 'utf8mb4')
    }

class OfflineRAGService:
    """离线RAG服务 - 不依赖外部模型"""
    
    def __init__(self):
        self.init_database()
        print("✅ 离线RAG服务初始化成功")
    
    def init_database(self):
        """初始化MySQL数据库连接"""
        self.conn = pymysql.connect(**MYSQL_CONFIG)
        print("✅ MySQL数据库连接成功")
    
    def preprocess_text(self, text: str) -> str:
        """文本预处理"""
        if not text:
            return ""
        # 移除特殊字符，保留中文、英文、数字
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', '', text)
        text = re.sub(r'\s+', ' ', text.strip())
        return text
    
    def tokenize_chinese(self, text: str) -> List[str]:
        """中文分词"""
        try:
            # 使用jieba分词
            words = list(jieba.cut(text))
            # 过滤停用词和短词
            stop_words = {'的', '了', '在', '是', '我', '你', '他', '她', '它', '们', '这', '那', '有', '无', '不', '也', '都', '很', '就', '要', '可以', '能够', '一个', '什么', '怎么', '为什么', '哪里', '时候'}
            filtered_words = [w.strip() for w in words if len(w.strip()) > 1 and w.strip() not in stop_words]
            return filtered_words
        except:
            # 如果jieba出问题，使用简单分割
            return text.split()
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度 - 使用TF-IDF余弦相似度"""
        try:
            # 分词
            tokens1 = self.tokenize_chinese(text1)
            tokens2 = self.tokenize_chinese(text2)
            
            if not tokens1 or not tokens2:
                return 0.0
            
            # 计算词频
            tf1 = Counter(tokens1)
            tf2 = Counter(tokens2)
            
            # 获取所有唯一词汇
            all_words = set(tokens1 + tokens2)
            
            # 计算TF-IDF向量
            def get_tf_idf_vector(tf_dict, all_words_set, total_docs=1000):
                vector = []
                total_words = sum(tf_dict.values())
                for word in all_words_set:
                    tf = tf_dict.get(word, 0) / total_words if total_words > 0 else 0
                    # 简化的IDF计算
                    idf = math.log(total_docs / (1 + tf_dict.get(word, 0)))
                    vector.append(tf * idf)
                return vector
            
            vector1 = get_tf_idf_vector(tf1, all_words)
            vector2 = get_tf_idf_vector(tf2, all_words)
            
            # 余弦相似度
            dot_product = sum(a * b for a, b in zip(vector1, vector2))
            magnitude1 = math.sqrt(sum(a * a for a in vector1))
            magnitude2 = math.sqrt(sum(b * b for b in vector2))
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            similarity = dot_product / (magnitude1 * magnitude2)
            
            # 额外的关键词匹配加权
            common_words = set(tokens1) & set(tokens2)
            keyword_bonus = len(common_words) / max(len(set(tokens1)), len(set(tokens2))) * 0.3
            
            return min(similarity + keyword_bonus, 1.0)
            
        except Exception as e:
            print(f"⚠️ 相似度计算出错: {e}")
            # 降级到简单字符串匹配
            return self.simple_string_similarity(text1, text2)
    
    def simple_string_similarity(self, text1: str, text2: str) -> float:
        """简单字符串相似度（降级方案）"""
        text1 = text1.lower()
        text2 = text2.lower()
        
        # 计算共同字符
        common_chars = 0
        for char in text1:
            if char in text2:
                common_chars += 1
        
        max_len = max(len(text1), len(text2))
        if max_len == 0:
            return 0.0
        
        return common_chars / max_len
    
    def categorize_question(self, question: str) -> str:
        """问题分类"""
        categories = {
            '库存查询': ['货', '库存', '有没有', '现货', '有货', '缺货', '断货'],
            '物流配送': ['发货', '快递', '物流', '到货', '配送', '什么时候', '多久', '运费', '邮费'],
            '价格咨询': ['便宜', '价格', '优惠', '折扣', '多少钱', '费用', '成本', '活动'],
            '产品质量': ['正品', '质量', '真假', '品质', '好用', '效果', '怎么样'],
            '售后服务': ['退货', '换货', '退款', '售后', '维修', '不满意', '问题', '坏了'],
            '账户服务': ['会员', '积分', '优惠券', 'VIP', '账户', '登录', '注册'],
            '订单管理': ['订单', '取消', '修改', '查询', '状态', '支付'],
            '产品咨询': ['成分', '使用', '效果', '说明书', '规格', '参数', '功能'],
            '店铺服务': ['营业时间', '地址', '联系方式', '客服', '电话']
        }
        
        question_lower = question.lower()
        scores = {}
        
        for category, keywords in categories.items():
            score = sum(1 for keyword in keywords if keyword in question_lower)
            if score > 0:
                scores[category] = score
        
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return '其他咨询'
    
    def generate_id(self, text: str) -> str:
        """生成唯一ID"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()[:16]
    
    def load_qa_data(self, qa_data: List[Dict]) -> Dict:
        """加载问答数据到MySQL（可选，通常用导入工具）"""
        if not qa_data:
            return {'success': 0, 'error': 0}
        print(f"🔄 开始加载 {len(qa_data)} 条问答数据...")
        success_count = 0
        error_count = 0
        with self.conn.cursor() as cursor:
            for qa in qa_data:
                try:
                    question = self.preprocess_text(qa.get('question', ''))
                    answer = self.preprocess_text(qa.get('answer', ''))
                    if not question or not answer:
                        error_count += 1
                        continue
                    qa_id = self.generate_id(question + answer)
                    question_tokens = ' '.join(self.tokenize_chinese(question))
                    category = qa.get('category', self.categorize_question(question))
                    cursor.execute(
                        "REPLACE INTO qa_data (id, question, answer, category, question_tokens, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
                        (qa_id, question, answer, category, question_tokens, datetime.now())
                    )
                    success_count += 1
                except Exception as e:
                    print(f"⚠️ 处理数据时出错: {e}")
                    error_count += 1
                    continue
            self.conn.commit()
        print(f"✅ 成功加载 {success_count} 条数据")
        return {
            'success': success_count,
            'error': error_count,
            'success_rate': round(success_count / len(qa_data) * 100, 2) if qa_data else 0
        }
    
    def retrieve_relevant_qa(self, user_question: str, top_k: int = 5) -> List[Dict]:
        """检索相关问答（MySQL版）"""
        try:
            processed_question = self.preprocess_text(user_question)
            if not processed_question:
                return []
            with self.conn.cursor() as cursor:
                cursor.execute('SELECT question, answer, category FROM qa_data')
                all_qa = cursor.fetchall()
            if not all_qa:
                print("⚠️ 知识库为空")
                return []
            similarities = []
            for question, answer, category in all_qa:
                similarity = self.calculate_text_similarity(processed_question, question)
                if similarity > 0.1:
                    similarities.append({
                        'question': question,
                        'answer': answer,
                        'category': category,
                        'similarity': round(similarity, 3)
                    })
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            return similarities[:top_k]
        except Exception as e:
            print(f"❌ 检索错误: {e}")
            return []
    
    def build_enhanced_prompt(self, user_question: str, relevant_qa: List[Dict]) -> str:
        """构建增强prompt"""
        if not relevant_qa:
            return f"""你是一个专业的智能客服助手，名叫'聆析智服'。请用友好、专业的语气回答用户问题。

用户问题: {user_question}

请提供有用的帮助，回答简洁明了，不超过200字。可以使用"亲亲"等亲切称谓保持友好语气。"""
        
        prompt = """你是一个专业的智能客服助手，名叫'聆析智服'。请根据以下知识库信息回答用户问题。

【参考知识库】:
"""
        
        for i, qa in enumerate(relevant_qa, 1):
            prompt += f"\n参考{i} (相似度{qa['similarity']}):\n"
            prompt += f"Q: {qa['question']}\n"
            prompt += f"A: {qa['answer']}\n"
        
        prompt += f"""
【用户问题】: {user_question}

请基于参考知识库提供准确回答，保持亲切友好的语气，可使用"亲亲"等称谓，控制在150字以内。"""
        
        return prompt
    
    def get_enhanced_response(self, user_question: str) -> Dict:
        """获取增强回复信息"""
        relevant_qa = self.retrieve_relevant_qa(user_question, top_k=3)
        enhanced_prompt = self.build_enhanced_prompt(user_question, relevant_qa)
        category = self.categorize_question(user_question)
        
        return {
            'enhanced_prompt': enhanced_prompt,
            'relevant_qa': relevant_qa,
            'has_relevant_info': len(relevant_qa) > 0,
            'best_similarity': relevant_qa[0]['similarity'] if relevant_qa else 0,
            'category': category,
            'confidence': min(len(relevant_qa) / 3.0, 1.0)
        }
    
    def get_collection_stats(self) -> Dict:
        """获取知识库统计（MySQL版）"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute('SELECT COUNT(*) FROM qa_data')
                total_count = cursor.fetchone()[0]
                cursor.execute('SELECT category, COUNT(*) FROM qa_data GROUP BY category')
                categories = dict(cursor.fetchall())
            return {
                'total_documents': total_count,
                'collection_name': 'mysql_qa_database',
                'categories': categories,
                'status': 'active',
                'db_host': MYSQL_CONFIG['host'],
                'db_name': MYSQL_CONFIG['database']
            }
        except Exception as e:
            return {
                'total_documents': 0,
                'status': 'error',
                'error': str(e)
            }
    
    def search_qa(self, keyword: str, limit: int = 10) -> List[Dict]:
        """搜索问答（MySQL版）"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    'SELECT question, answer, category FROM qa_data WHERE question LIKE %s OR answer LIKE %s LIMIT %s',
                    (f'%{keyword}%', f'%{keyword}%', limit)
                )
                results = []
                for question, answer, category in cursor.fetchall():
                    results.append({
                        'question': question,
                        'answer': answer,
                        'category': category
                    })
            return results
        except Exception as e:
            print(f"❌ 搜索错误: {e}")
            return []
    
    def close(self):
        """关闭数据库连接"""
        if hasattr(self, 'conn'):
            self.conn.close()

# 全局单例
_offline_rag_service = None

def get_rag_service():
    """获取离线RAG服务单例"""
    global _offline_rag_service
    if _offline_rag_service is None:
        _offline_rag_service = OfflineRAGService()
    return _offline_rag_service

# 测试代码
if __name__ == "__main__":
    print("🧪 测试离线RAG服务...")
    try:
        rag = get_rag_service()
        
        # 测试数据
        test_data = [
            {'question': '有货吗', 'answer': '亲亲，能下单就是在售有货的哦'},
            {'question': '什么时候发货', 'answer': '亲亲，所有商品拍下会陆续发货，最迟不超过48个小时'}
        ]
        
        # 测试加载数据
        result = rag.load_qa_data(test_data)
        print(f"📊 加载结果: {result}")
        
        # 测试检索
        response = rag.get_enhanced_response('有没有货？')
        print(f"🔍 检索结果: 相关问答 {len(response['relevant_qa'])} 条")
        
        # 统计信息
        stats = rag.get_collection_stats()
        print(f"📈 知识库统计: {stats}")
        
        print("✅ 离线RAG服务测试通过")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()