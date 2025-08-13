from flask import Blueprint, request, jsonify
import pandas as pd
import numpy as np
from services.db_handler import get_db_connection
import re
import os
import pickle
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from gemini_handler import get_gemini_response

chat3_bp = Blueprint("chat3", __name__)

# ✅ 모델 및 데이터 로드
MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'LLM_model'))
EXCEL_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'excel_data'))

def load_pickle(filename):
    """피클 파일 로드"""
    with open(os.path.join(MODEL_DIR, filename), "rb") as f:
        return pickle.load(f)

def save_pickle(data, filename):
    """피클 파일 저장"""
    with open(os.path.join(MODEL_DIR, filename), "wb") as f:
        pickle.dump(data, f)

# 임베딩 모델 로드
embedding_model = SentenceTransformer('jhgan/ko-sroberta-multitask')

# ✅ EXCEL 데이터 처리 및 임베딩 수정부분
class ExcelRAGProcessor:
    excel_path = os.path.join(os.path.dirname(__file__), "..", "services", "product_parts.xlsx")

    def __init__(self):
        self.documents = []
        self.embeddings = None
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000)
        self.tfidf_matrix = None
        
    def load_excel_data_from_db(self):
        """DB에서 최신 데이터를 가져와서 Excel 파일 업데이트"""
        try:
            print("🔄 DB에서 최신 데이터를 가져오는 중...")
            
            # DB 연결
            conn = get_db_connection()
            
            # DB에서 모든 데이터 조회
            query = "SELECT * FROM pcb_parts"
            df = pd.read_sql(query, conn)
            conn.close()
            
            if df.empty:
                print("❌ DB에서 데이터를 가져올 수 없습니다.")
                return False
            
            print(f"✅ DB에서 {len(df)}개의 레코드를 가져왔습니다.")
            
            # Excel 파일로 저장
            df.to_excel(self.excel_path, index=False, sheet_name='pcb_parts')
            print(f"💾 Excel 파일 업데이트 완료: {self.excel_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ DB에서 데이터 가져오기 오류: {e}")
            return False
        
    def load_excel_data(self, excel_path=None):
        """EXCEL 파일을 로드하고 문서로 변환 (DB에서 최신 데이터로 업데이트 후)"""
        try:
            # 먼저 DB에서 최신 데이터로 Excel 파일 업데이트
            if not self.load_excel_data_from_db():
                print("⚠️ DB 업데이트 실패, 기존 Excel 파일 사용")
            
            # Excel 파일 읽기
            if not os.path.exists(self.excel_path):
                print(f"❌ Excel 파일이 존재하지 않습니다: {self.excel_path}")
                return False
                
            excel_file = pd.ExcelFile(self.excel_path)
            all_documents = []
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(self.excel_path, sheet_name=sheet_name)
                
                # 각 행을 문서로 변환
                for idx, row in df.iterrows():
                    # NaN 값 제거하고 텍스트로 변환
                    row_text = " ".join([
                        f"{col}: {str(val)}" 
                        for col, val in row.items() 
                        if pd.notna(val)
                    ])
                    
                    document = {
                        'content': row_text,
                        'sheet': sheet_name,
                        'row_index': idx,
                        'metadata': row.to_dict()
                    }
                    all_documents.append(document)
            
            self.documents = all_documents
            print(f"📊 로드된 문서 수: {len(self.documents)}")
            return True
            
        except Exception as e:
            print(f"❌ EXCEL 파일 로드 오류: {e}")
            return False
    
    def create_embeddings(self):
        """문서들의 임베딩 생성"""
        if not self.documents:
            print("문서가 없습니다. 먼저 EXCEL 파일을 로드하세요.")
            return False
        
        try:
            # 문서 텍스트 추출
            texts = [doc['content'] for doc in self.documents]
            
            # 텍스트 전처리
            cleaned_texts = [self.clean_text(text) for text in texts]
            
            # Sentence Transformer 임베딩 생성
            print("임베딩 생성 중...")
            self.embeddings = embedding_model.encode(cleaned_texts)
            
            # TF-IDF 벡터화
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(cleaned_texts)
            
            print(f"임베딩 생성 완료: {self.embeddings.shape}")
            return True
            
        except Exception as e:
            print(f"임베딩 생성 오류: {e}")
            return False
    
    def clean_text(self, text):
        """텍스트 전처리"""
        text = str(text).lower()
        text = re.sub(r"[^\w\s가-힣]", " ", text)  # 한글 지원
        text = re.sub(r"\s+", " ", text)
        return text.strip()
    
    def search_documents(self, query, top_k=5, min_similarity=0.3):
        """유사도 기반 문서 검색"""
        if self.embeddings is None:
            return []
        
        try:
            # 쿼리 임베딩 생성
            query_cleaned = self.clean_text(query)
            query_embedding = embedding_model.encode([query_cleaned])
            
            # 코사인 유사도 계산
            similarities = cosine_similarity(query_embedding, self.embeddings)[0]
            
            # TF-IDF 유사도도 계산
            query_tfidf = self.tfidf_vectorizer.transform([query_cleaned])
            tfidf_similarities = (self.tfidf_matrix * query_tfidf.T).toarray().flatten()
            
            # 두 유사도 점수 결합 (가중평균)
            combined_scores = 0.7 * similarities + 0.3 * tfidf_similarities
            
            # 상위 k개 문서 선택
            top_indices = np.argsort(combined_scores)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                if combined_scores[idx] >= min_similarity:
                    results.append({
                        'document': self.documents[idx],
                        'similarity': float(combined_scores[idx]),
                        'semantic_sim': float(similarities[idx]),
                        'tfidf_sim': float(tfidf_similarities[idx])
                    })
            
            return results
            
        except Exception as e:
            print(f"문서 검색 오류: {e}")
            return []
    
    def save_processed_data(self):
        """처리된 데이터 저장"""
        try:
            save_pickle(self.documents, "excel_documents.pkl")
            save_pickle(self.embeddings, "excel_embeddings.pkl")
            save_pickle(self.tfidf_vectorizer, "excel_tfidf_vectorizer.pkl")
            save_pickle(self.tfidf_matrix, "excel_tfidf_matrix.pkl")
            print("처리된 데이터 저장 완료")
            return True
        except Exception as e:
            print(f"데이터 저장 오류: {e}")
            return False
    
    def load_processed_data(self):
        """처리된 데이터 로드"""
        try:
            self.documents = load_pickle("excel_documents.pkl")
            self.embeddings = load_pickle("excel_embeddings.pkl")
            self.tfidf_vectorizer = load_pickle("excel_tfidf_vectorizer.pkl")
            self.tfidf_matrix = load_pickle("excel_tfidf_matrix.pkl")
            print(f"처리된 데이터 로드 완료: {len(self.documents)}개 문서")
            return True
        except Exception as e:
            print(f"데이터 로드 오류: {e}")
            return False

# ✅ 전역 RAG 프로세서 인스턴스
rag_processor = ExcelRAGProcessor()

def initialize_rag_system(excel_path=None):
    if excel_path is None:
        excel_path = os.path.join(os.path.dirname(__file__), "..", "services", "product_parts.xlsx")
    """RAG 시스템 초기화"""
    # 기존 처리된 데이터가 있는지 확인
    if rag_processor.load_processed_data():
        return True
    
    # 새로 EXCEL 파일 처리
    if excel_path and os.path.exists(excel_path):
        if rag_processor.load_excel_data(excel_path):
            if rag_processor.create_embeddings():
                rag_processor.save_processed_data()
                return True
    
    print("RAG 시스템 초기화 실패")
    return False

def generate_rag_response(query, search_results):
    """검색 결과를 바탕으로 RAG 응답 생성"""
    if not search_results:
        return "관련된 정보를 찾을 수 없습니다."
    
    # 컨텍스트 구성
    context_parts = []
    for i, result in enumerate(search_results[:3]):  # 상위 3개만 사용
        doc = result['document']
        similarity = result['similarity']
        
        context_parts.append(
            f"[문서 {i+1}] (유사도: {similarity:.3f})\n"
            f"시트: {doc['sheet']}\n"
            f"내용: {doc['content'][:500]}...\n"
        )
    
    context = "\n".join(context_parts)
    
    # Gemini에 전달할 프롬프트 구성
    prompt = f"""
다음은 EXCEL 데이터베이스에서 검색된 관련 정보입니다:

{context}

사용자 질문: {query}

위의 검색된 정보를 바탕으로 사용자의 질문에 정확하고 도움이 되는 답변을 제공해주세요. 
검색된 데이터의 구체적인 내용을 인용하여 답변하되, 자연스럽고 이해하기 쉽게 설명해주세요.
"""
    
    return get_gemini_response(prompt, apply_format=True)

@chat3_bp.route("/chat", methods=["POST"])
def chat():
    """RAG 기반 채팅 엔드포인트 (매번 DB에서 최신 데이터 가져오기)"""
    data = request.get_json()
    messages = data.get("messages", [])
    user_input = next(
        (msg.get("content", "") for msg in reversed(messages) if msg.get("role") == "user"), 
        ""
    )

    if not user_input:
        return jsonify({
            "message": {"role": "assistant", "content": "질문을 입력해 주세요."}
        })

    try:
        # 매번 DB에서 최신 데이터로 Excel 파일 업데이트
        print("🔄 채팅 요청 - DB에서 최신 데이터 가져오는 중...")
        if rag_processor.load_excel_data():
            # 임베딩 재생성 (새로운 데이터에 맞게)
            if rag_processor.create_embeddings():
                print("✅ 최신 데이터로 임베딩 재생성 완료")
            else:
                print("⚠️ 임베딩 재생성 실패")
        
        # RAG 검색 수행
        search_results = rag_processor.search_documents(user_input, top_k=5)
        
        if search_results:
            # 검색 결과 기반 응답 생성
            response = generate_rag_response(user_input, search_results)
            
            final_response = response
        else:
            # 검색 결과가 없을 때 일반 응답
            final_response = get_gemini_response(user_input, apply_format=True)
        
        return jsonify({
            "message": {"role": "assistant", "content": final_response}
        })
        
    except Exception as e:
        return jsonify({
            "message": {"role": "assistant", "content": f"처리 중 오류가 발생했습니다: {str(e)}"}
        })

# 재고 관리 특화 프롬프트 템플릿
INVENTORY_PROMPT_TEMPLATE = """당신은 PCB-Manager의 재고 관리 전문 AI 어시스턴트입니다.

**주요 역할:**
1. 부품 재고 현황 조회 및 분석
2. 재고 부족 알림 및 발주 제안
3. 흡습 관리가 필요한 부품 식별
4. 부품 상세 정보 제공
5. 재고 최적화 조언

**응답 규칙:**
- 친근하고 전문적인 톤으로 답변
- 구체적인 수치와 데이터 포함
- 재고 관리에 실질적으로 도움이 되는 정보 제공
- 필요시 발주 제안이나 주의사항 안내
- 이모지를 적절히 사용하여 가독성 향상

**중요 정보:**
- 재고량이 최소 재고량보다 낮으면 '부족' 상태
- 흡습 관리가 필요한 부품은 별도 보관 필요
- 부품 ID는 정확한 매칭이 중요함
"""

def analyze_inventory_intent(user_message):
    """사용자 의도 분석 (재고 관리 특화)"""
    message_lower = user_message.lower()
    
    # 부족 재고 관련
    if any(keyword in message_lower for keyword in ["부족", "부족한", "low stock", "shortage", "없는", "떨어진"]):
        return "low_stock"
    
    # 흡습 관리 관련
    if any(keyword in message_lower for keyword in ["흡습", "moisture", "습도", "humidity", "건조", "보관"]):
        return "moisture_management"
    
    # 발주 관련
    if any(keyword in message_lower for keyword in ["발주", "주문", "order", "구매", "purchase", "신청"]):
        return "ordering"
    
    # 특정 부품 검색
    if re.search(r'[A-Z]{2}[0-9]{2}[A-Z0-9]{6,}', user_message.upper()):
        return "part_search"
    
    # 제조사 검색
    if any(keyword in message_lower for keyword in ["삼성", "samsung", "무라타", "murata", "tdk", "kemet"]):
        return "manufacturer_search"
    
    # 재고 현황
    if any(keyword in message_lower for keyword in ["현황", "상태", "status", "재고량", "수량", "현재"]):
        return "inventory_status"
    
    # 통계 및 분석
    if any(keyword in message_lower for keyword in ["통계", "분석", "analysis", "statistics", "총", "전체", "평균"]):
        return "statistics"
    
    return "general"

def generate_inventory_specific_response(user_message, search_results, intent):
    """재고 관리에 특화된 응답 생성"""
    if not search_results:
        return f"""📦 **재고 정보를 찾을 수 없습니다**

'{user_message}'에 대한 정보를 데이터베이스에서 찾을 수 없습니다.

💡 **다시 시도해보세요:**
- 정확한 부품 ID 입력 (예: CL02B121KP2NNNC)
- 제조사 이름 확인 (삼성, 무라타 등)
- "재고 현황", "부족한 부품" 등으로 질문

🔍 **지원 가능한 질문:**
- "부족한 재고 알려줘"
- "흡습 관리 필요한 부품"
- "삼성 커패시터 현황"
- "전체 재고 통계"
"""
    
    # 검색된 데이터 분석
    total_parts = len(search_results)
    context_parts = []
    
    for i, result in enumerate(search_results[:5]):  # 상위 5개
        doc = result['document']
        metadata = doc.get('metadata', {})
        similarity = result['similarity']
        
        # 부품 정보 추출
        part_id = metadata.get('part_id', metadata.get('partId', 'Unknown'))
        product_name = metadata.get('product_name', metadata.get('product', 'Unknown'))
        manufacturer = metadata.get('manufacturer', 'Unknown')
        quantity = metadata.get('quantity', 0)
        min_stock = metadata.get('min_stock', metadata.get('minimumStock', 0))
        moisture_absorption = metadata.get('moisture_absorption', metadata.get('moistureAbsorption', False))
        
        # 재고 상태 판단
        if quantity < min_stock:
            stock_status = "🔴 부족"
            shortage = min_stock - quantity
        else:
            stock_status = "🟢 충분"
            shortage = 0
        
        moisture_status = "💧 흡습관리필요" if moisture_absorption else "🌞 일반보관"
        
        context_parts.append({
            'part_id': part_id,
            'product_name': product_name,
            'manufacturer': manufacturer,
            'quantity': quantity,
            'min_stock': min_stock,
            'stock_status': stock_status,
            'shortage': shortage,
            'moisture_status': moisture_status,
            'similarity': similarity
        })
    
    # 의도별 특화 응답 생성
    if intent == "low_stock":
        low_stock_parts = [p for p in context_parts if "부족" in p['stock_status']]
        
        response = f"📦 **재고 부족 현황 분석**\n\n"
        response += f"🔍 **검색된 부품**: {total_parts}개\n"
        response += f"🔴 **부족 부품**: {len(low_stock_parts)}개\n\n"
        
        if low_stock_parts:
            response += "**즉시 발주가 필요한 부품들:**\n"
            for part in low_stock_parts[:3]:
                response += f"""
• **{part['part_id']}** ({part['product_name']})
  - 현재: {part['quantity']}개 | 최소: {part['min_stock']}개
  - 부족량: {part['shortage']}개 | 제조사: {part['manufacturer']}
  - {part['moisture_status']}
"""
        else:
            response += "✅ **양호**: 검색된 부품들의 재고가 충분합니다!"
    
    elif intent == "moisture_management":
        moisture_parts = [p for p in context_parts if "흡습관리필요" in p['moisture_status']]
        
        response = f"💧 **흡습 관리 현황**\n\n"
        response += f"🔍 **검색된 부품**: {total_parts}개\n"
        response += f"💧 **흡습 관리 대상**: {len(moisture_parts)}개\n\n"
        
        if moisture_parts:
            response += "**흡습 관리가 필요한 부품:**\n"
            for part in moisture_parts:
                response += f"""
• **{part['part_id']}** ({part['product_name']})
  - 현재 재고: {part['quantity']}개 | {part['stock_status']}
  - 제조사: {part['manufacturer']}
  - ⚠️ 습도 관리 필수
"""
            
            response += f"""
📋 **흡습 관리 체크리스트:**
- ✅ 건조제와 함께 밀폐 보관
- ✅ 습도 30% 이하 유지
- ✅ 개봉 후 8시간 내 사용
- ✅ 재건조 주기 준수

🚨 **주의사항:** 흡습된 부품은 PCB 불량의 주요 원인이 됩니다.
"""
    
    elif intent == "part_search":
        if context_parts:
            part = context_parts[0]  # 가장 유사한 부품
            response = f"""🔍 **부품 검색 결과**

**{part['part_id']}**
- 제품명: {part['product_name']}
- 제조사: {part['manufacturer']}
- 현재재고: {part['quantity']}개 (최소: {part['min_stock']}개)
- 상태: {part['stock_status']}
- 보관조건: {part['moisture_status']}
- 검색 정확도: {part['similarity']:.1%}

"""
            
            if part['shortage'] > 0:
                response += f"⚠️ **발주 필요**: {part['shortage']}개 부족\n"
            
            # 유사한 다른 부품들도 표시
            if len(context_parts) > 1:
                response += f"\n🔎 **유사한 부품들:**\n"
                for similar_part in context_parts[1:3]:
                    response += f"- {similar_part['part_id']} ({similar_part['manufacturer']}) - {similar_part['quantity']}개\n"
    
    else:  # 일반 응답
        response = f"""📊 **재고 분석 결과**

🔍 **검색된 부품**: {total_parts}개

**상위 부품 현황:**
"""
        
        for i, part in enumerate(context_parts[:3], 1):
            response += f"""
{i}. **{part['part_id']}** ({part['product_name']})
   - 재고: {part['quantity']}개 | {part['stock_status']}
   - 제조사: {part['manufacturer']} | {part['moisture_status']}
"""
        
        low_stock_count = len([p for p in context_parts if "부족" in p['stock_status']])
        moisture_count = len([p for p in context_parts if "흡습관리필요" in p['moisture_status']])
        
        response += f"""
📈 **요약:**
- 🔴 부족 부품: {low_stock_count}개
- 💧 흡습 관리: {moisture_count}개
- 🟢 정상 재고: {total_parts - low_stock_count}개
"""
    
    return response

@chat3_bp.route('/inventory-chat', methods=['POST'])
def inventory_chat():
    """재고 관리 전용 챗봇 엔드포인트 (RAG 기반)"""
    try:
        print("\n" + "="*60)
        print("[📝] 재고 챗봇 API 호출 시작")
        print("="*60)
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "요청 데이터가 없습니다.", "success": False}), 400
        
        user_message = data.get('message', '').strip()
        context = data.get('context', {})
        
        print(f"[📋] 사용자 메시지: {user_message}")
        print(f"[📋] 요청 시간: {datetime.now().isoformat()}")
        
        if not user_message:
            return jsonify({"error": "메시지가 필요합니다.", "success": False}), 400
        
        # 사용자 의도 분석
        intent = analyze_inventory_intent(user_message)
        print(f"[🧠] 분석된 의도: {intent}")
        
        # DB에서 최신 데이터로 업데이트
        print("[📊] DB에서 최신 재고 데이터 가져오는 중...")
        if rag_processor.load_excel_data():
            if rag_processor.create_embeddings():
                print("✅ 최신 데이터로 임베딩 재생성 완료")
            else:
                print("⚠️ 임베딩 재생성 실패")
        
        # RAG 검색 수행
        search_results = rag_processor.search_documents(user_message, top_k=10, min_similarity=0.1)
        
        print(f"[🔍] 검색 결과: {len(search_results)}개 문서")
        
        # 재고 관리 특화 응답 생성
        if search_results:
            # 검색 결과 기반 특화 응답
            response = generate_inventory_specific_response(user_message, search_results, intent)
        else:
            # 검색 결과가 없을 때 기본 응답
            response = f"""📦 **재고 정보를 찾을 수 없습니다**

'{user_message}'에 대한 정보를 찾을 수 없습니다.

💡 **다시 시도해보세요:**
- 정확한 부품 ID 입력
- 제조사 이름 확인  
- "재고 현황", "부족한 부품" 등으로 질문

🔧 **지원 가능한 기능:**
- 부품 재고 확인
- 재고 부족 알림
- 흡습 관리 부품 조회
- 발주 추천
"""
        
        print(f"[✅] 응답 생성 완료 (길이: {len(response)}자)")
        
        result = {
            "response": response,
            "intent": intent,
            "search_results_count": len(search_results),
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "performance": {
                "intent": intent,
                "documents_found": len(search_results)
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        print(f"[❌] 재고 챗봇 API 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": f"서버 오류가 발생했습니다: {str(e)}",
            "success": False,
            "timestamp": datetime.now().isoformat()
        }), 500

@chat3_bp.route('/quick-actions', methods=['POST'])
def quick_actions():
    """빠른 액션 처리 (부족재고, 흡습관리, 발주추천 등)"""
    try:
        data = request.get_json()
        action = data.get('action', '')
        
        print(f"[⚡] 빠른 액션 요청: {action}")
        
        # 액션별 검색 쿼리 매핑
        action_queries = {
            "low_stock": "부족한 재고 부품 minimum stock shortage",
            "moisture_management": "흡습 관리 필요 moisture absorption humidity sensitive",
            "ordering_recommendation": "발주 추천 order recommendation low stock"
        }
        
        query = action_queries.get(action, action)
        
        # DB에서 최신 데이터로 업데이트
        if rag_processor.load_excel_data():
            rag_processor.create_embeddings()
        
        # RAG 검색 수행
        search_results = rag_processor.search_documents(query, top_k=20, min_similarity=0.05)
        intent = action.replace('_', ' ')
        
        # 특화 응답 생성
        response = generate_inventory_specific_response(query, search_results, action)
        
        return jsonify({
            "response": response,
            "action": action,
            "search_results_count": len(search_results),
            "success": True,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"[❌] 빠른 액션 오류: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@chat3_bp.route('/health', methods=['GET'])
def inventory_health():
    """재고 챗봇 헬스 체크"""
    try:
        # RAG 시스템 상태 확인
        has_documents = len(rag_processor.documents) > 0
        has_embeddings = rag_processor.embeddings is not None
        
        # DB 연결 테스트
        try:
            conn = get_db_connection()
            conn.close()
            db_status = "connected"
        except:
            db_status = "disconnected"
        
        return jsonify({
            "status": "healthy" if has_documents and has_embeddings and db_status == "connected" else "degraded",
            "message": "재고 관리 챗봇이 정상 작동 중입니다.",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "database": db_status,
                "rag_documents": f"{len(rag_processor.documents)}개 로드됨" if has_documents else "문서 없음",
                "embeddings": "준비됨" if has_embeddings else "준비 안됨",
                "system": "operational"
            }
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

#✅ RAG 시스템 초기화 (앱 시작시 호출)
from datetime import datetime
initialize_rag_system()