"""
完全兼容的RAG服务 - 支持原有的导入方式
"""
import os
import json
import re
import sqlite3
import hashlib
from typing import List, Dict, Tuple
from datetime import datetime
from collections import Counter
import math

class RAGService:
    """RAG服务 - 兼容原有接口"""
    
    def __init__(self, collection_name="customer_service_qa"):
        self.collection_name = collection_name
        self.db_path = "./rag_data.db"
        self.init_database()
        print("✅ RAG服务初始化成功")
    
    def init_database(self):
        """初始化SQLite数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS qa_data (
                    id TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    category TEXT,
                    question_tokens TEXT,
                    created_at TEXT
                )
            ''')
            self.conn.commit()
            print(f"✅ 数据库初始化完成: {self.db_path}")
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
            raise
    
    def preprocess_text(self, text: str) -> str:
        """文本预处理"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text.strip())
        return text
    
    def simple_tokenize(self, text: str) -> List[str]:
        """简单分词"""
        # 尝试导入jieba，如果失败则使用简单分割
        try:
            import jieba
            words = list(jieba.cut(text))
            stop_words = {'的', '了', '在', '是', '我', '你', '他', '她', '它', '们', '这', '那', '有', '无', '不', '也', '都', '很', '就', '要', '可以', '能够', '一个', '什么', '怎么', '为什么', '哪里', '时候'}
            filtered_words = [w.strip() for w in words if len(w.strip()) > 1 and w.strip() not in stop_words]
            return filtered_words
        except ImportError:
            # 降级到简单分割
            return self.fallback_tokenize(text)
    
    def fallback_tokenize(self, text: str) -> List[str]:
        """降级分词方案"""
        # 移除标点符号
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', ' ', text)
        words = text.split()
        return [w for w in words if len(w) > 1]
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算相似度"""
        try:
            text1_clean = self.preprocess_text(text1.lower())
            text2_clean = self.preprocess_text(text2.lower())
            
            if not text1_clean or not text2_clean:
                return 0.0
            
            tokens1 = self.simple_tokenize(text1_clean)
            tokens2 = self.simple_tokenize(text2_clean)
            
            if not tokens1 or not tokens2:
                return self.character_similarity(text1_clean, text2_clean)
            
            # 计算词汇交集
            set1 = set(tokens1)
            set2 = set(tokens2)
            
            intersection = set1 & set2
            union = set1 | set2
            
            if not union:
                return 0.0
            
            # Jaccard相似度
            jaccard = len(intersection) / len(union)
            
            # 字符级相似度作为补充
            char_sim = self.character_similarity(text1_clean, text2_clean)
            
            # 组合相似度
            return min(jaccard * 0.7 + char_sim * 0.3, 1.0)
            
        except Exception:
            return self.character_similarity(text1, text2)
    
    def character_similarity(self, text1: str, text2: str) -> float:
        """字符级相似度"""
        if not text1 or not text2:
            return 0.0
        
        # 简单的字符重叠度
        chars1 = set(text1)
        chars2 = set(text2)
        
        intersection = chars1 & chars2
        union = chars1 | chars2
        
        return len(intersection) / len(union) if union else 0.0
    
    def categorize_question(self, question: str) -> str:
        """问题分类"""
        categories = {
            '库存查询': ['货', '库存', '有没有', '现货', '有货'],
            '物流配送': ['发货', '快递', '物流', '到货', '配送', '什么时候'],
            '价格咨询': ['便宜', '价格', '优惠', '折扣', '多少钱'],
            '产品质量': ['正品', '质量', '真假', '品质'],
            '售后服务': ['退货', '换货', '退款', '售后'],
            '账户服务': ['会员', '积分', '优惠券'],
            '订单管理': ['订单', '取消', '修改', '查询'],
            '产品咨询': ['成分', '使用', '效果', '说明书'],
        }
        
        question_lower = question.lower()
        for category, keywords in categories.items():
            if any(keyword in question_lower for keyword in keywords):
                return category
        return '其他咨询'
    
    def load_qa_data(self, qa_data: List[Dict]) -> Dict:
        """加载问答数据"""
        if not qa_data:
            return {'success': 0, 'error': 0}
        
        print(f"🔄 开始加载 {len(qa_data)} 条问答数据...")
        
        success_count = 0
        error_count = 0
        
        for qa in qa_data:
            try:
                question = self.preprocess_text(qa.get('question', ''))
                answer = self.preprocess_text(qa.get('answer', ''))
                
                if not question or not answer:
                    error_count += 1
                    continue
                
                qa_id = hashlib.md5((question + answer).encode('utf-8')).hexdigest()[:16]
                category = qa.get('category', self.categorize_question(question))
                
                self.conn.execute('''
                    INSERT OR REPLACE INTO qa_data 
                    (id, question, answer, category, question_tokens, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (qa_id, question, answer, category, '', datetime.now().isoformat()))
                
                success_count += 1
                
            except Exception as e:
                print(f"⚠️ 处理数据时出错: {e}")
                error_count += 1
        
        self.conn.commit()
        print(f"✅ 成功加载 {success_count} 条数据")
        
        return {
            'success': success_count,
            'error': error_count,
            'success_rate': round(success_count / len(qa_data) * 100, 2) if qa_data else 0
        }
    
    def retrieve_relevant_qa(self, user_question: str, top_k: int = 5) -> List[Dict]:
        """检索相关问答"""
        try:
            processed_question = self.preprocess_text(user_question)
            if not processed_question:
                return []
            
            cursor = self.conn.execute('SELECT question, answer, category FROM qa_data')
            all_qa = cursor.fetchall()
            
            if not all_qa:
                return []
            
            similarities = []
            for question, answer, category in all_qa:
                similarity = self.calculate_similarity(processed_question, question)
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

请提供有用的帮助，回答简洁明了，不超过200字。"""
        
        prompt = """你是一个专业的智能客服助手，名叫'聆析智服'。请根据以下知识库信息回答用户问题。

【参考知识库】:
"""
        
        for i, qa in enumerate(relevant_qa, 1):
            prompt += f"\n参考{i}: Q: {qa['question']}\nA: {qa['answer']}\n"
        
        prompt += f"""
【用户问题】: {user_question}

请基于参考知识库提供准确回答，保持友好语气，控制在150字以内。"""
        
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
        """获取知识库统计"""
        try:
            cursor = self.conn.execute('SELECT COUNT(*) FROM qa_data')
            total_count = cursor.fetchone()[0]
            
            cursor = self.conn.execute('SELECT category, COUNT(*) FROM qa_data GROUP BY category')
            categories = dict(cursor.fetchall())
            
            return {
                'total_documents': total_count,
                'collection_name': self.collection_name,
                'categories': categories,
                'status': 'active'
            }
        except Exception as e:
            return {
                'total_documents': 0,
                'status': 'error',
                'error': str(e)
            }

# 全局单例
_rag_service = None

def get_rag_service():
    """获取RAG服务单例"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service

# 测试代码
if __name__ == "__main__":
    print("🧪 测试RAG服务...")
    try:
        rag = RAGService()
        
        test_data = [
            {'question': '有货吗', 'answer': '亲亲，能下单就是在售有货的哦'},
            {'question': '什么时候发货', 'answer': '亲亲，所有商品拍下会陆续发货，最迟不超过48个小时'}
        ]
        
        result = rag.load_qa_data(test_data)
        print(f"📊 加载结果: {result}")
        
        response = rag.get_enhanced_response('有没有货？')
        print(f"🔍 检索结果: 相关问答 {len(response['relevant_qa'])} 条")
        
        stats = rag.get_collection_stats()
        print(f"📈 知识库统计: {stats}")
        
        print("✅ RAG服务测试通过")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()