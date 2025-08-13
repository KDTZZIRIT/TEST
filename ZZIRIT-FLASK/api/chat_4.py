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
from datetime import datetime

chat4_bp = Blueprint("chat4", __name__)

# 모델 및 데이터 로드
MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'LLM_model'))
EXCEL_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'excel_data'))

def load_pickle(filename):
    with open(os.path.join(MODEL_DIR, filename), "rb") as f:
        return pickle.load(f)

def save_pickle(data, filename):
    with open(os.path.join(MODEL_DIR, filename), "wb") as f:
        pickle.dump(data, f)

# 임베딩 모델
embedding_model = SentenceTransformer('jhgan/ko-sroberta-multitask')

# Excel/RAG 프로세서
class ExcelRAGProcessor:
    excel_path = os.path.join(os.path.dirname(__file__), "..", "services", "product_parts.xlsx")

    def __init__(self):
        self.documents = []
        self.embeddings = None
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000)
        self.tfidf_matrix = None

    def load_excel_data_from_db(self):
        try:
            print("🔄 DB에서 최신 데이터를 가져오는 중...")
            conn = get_db_connection()
            query = "SELECT * FROM pcb_parts"
            df = pd.read_sql(query, conn)
            conn.close()

            if df.empty:
                print("❌ DB에서 데이터를 가져올 수 없습니다.")
                return False

            print(f"✅ DB에서 {len(df)}개의 레코드를 가져왔습니다.")
            df.to_excel(self.excel_path, index=False, sheet_name='pcb_parts')
            print(f"💾 Excel 파일 업데이트 완료: {self.excel_path}")
            return True

        except Exception as e:
            print(f"❌ DB에서 데이터 가져오기 오류: {e}")
            return False

    def load_excel_data(self, excel_path=None):
        try:
            if not self.load_excel_data_from_db():
                print("⚠️ DB 업데이트 실패, 기존 Excel 파일 사용")

            if not os.path.exists(self.excel_path):
                print(f"❌ Excel 파일이 존재하지 않습니다: {self.excel_path}")
                return False

            excel_file = pd.ExcelFile(self.excel_path)
            all_documents = []

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(self.excel_path, sheet_name=sheet_name)

                for idx, row in df.iterrows():
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
        if not self.documents:
            print("문서가 없습니다. 먼저 EXCEL 파일을 로드하세요.")
            return False
        try:
            texts = [doc['content'] for doc in self.documents]
            cleaned_texts = [self.clean_text(text) for text in texts]
            print("임베딩 생성 중...")
            self.embeddings = embedding_model.encode(cleaned_texts)
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(cleaned_texts)
            print(f"임베딩 생성 완료: {self.embeddings.shape}")
            return True
        except Exception as e:
            print(f"임베딩 생성 오류: {e}")
            return False

    def clean_text(self, text):
        text = str(text).lower()
        # 하이픈(-) 보존: 부품번호 매칭 정확도 향상
        text = re.sub(r"[^\w\s가-힣\-]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def search_documents(self, query, top_k=5, min_similarity=0.35):
        if self.embeddings is None:
            return []
        try:
            query_cleaned = self.clean_text(query)
            query_embedding = embedding_model.encode([query_cleaned])

            similarities = cosine_similarity(query_embedding, self.embeddings)[0]
            query_tfidf = self.tfidf_vectorizer.transform([query_cleaned])
            tfidf_similarities = (self.tfidf_matrix * query_tfidf.T).toarray().flatten()

            combined_scores = 0.7 * similarities + 0.3 * tfidf_similarities

            # 부품번호 패턴 감지 시 부분일치 가중치 부여
            m = re.search(r'[A-Z0-9\-]{6,}', query.upper())
            if m:
                qpart = m.group(0)
                for i, doc in enumerate(self.documents):
                    pn = str(doc['metadata'].get('part_number', '')).upper()
                    if pn and qpart in pn:
                        combined_scores[i] += 0.3

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

# 전역 RAG 인스턴스
rag_processor = ExcelRAGProcessor()

def initialize_rag_system(excel_path=None):
    if excel_path is None:
        excel_path = os.path.join(os.path.dirname(__file__), "..", "services", "product_parts.xlsx")
    if rag_processor.load_processed_data():
        return True
    if excel_path and os.path.exists(excel_path):
        if rag_processor.load_excel_data(excel_path):
            if rag_processor.create_embeddings():
                rag_processor.save_processed_data()
                return True
    print("RAG 시스템 초기화 실패")
    return False

def generate_rag_response(query, search_results):
    if not search_results:
        return "관련된 정보를 찾을 수 없습니다."
    context_parts = []
    for i, result in enumerate(search_results[:3]):
        doc = result['document']
        similarity = result['similarity']
        context_parts.append(
            f"[문서 {i+1}] (유사도: {similarity:.3f})\n"
            f"시트: {doc['sheet']}\n"
            f"내용: {doc['content'][:500]}...\n"
        )
    context = "\n".join(context_parts)
    prompt = f"""
다음은 EXCEL 데이터베이스에서 검색된 관련 정보입니다:

{context}

사용자 질문: {query}

위의 검색된 정보를 바탕으로 사용자의 질문에 정확하고 도움이 되는 답변을 제공해주세요. 
검색된 데이터의 구체적인 내용을 인용하여 답변하되, 자연스럽고 이해하기 쉽게 설명해주세요.
"""
    return get_gemini_response(prompt, apply_format=True)

@chat4_bp.route("/chat4", methods=["POST"])
def chat4():
    data = request.get_json()
    messages = data.get("messages", [])
    user_input = next(
        (msg.get("content", "") for msg in reversed(messages) if msg.get("role") == "user"),
        ""
    )

    if not user_input:
        return jsonify({"message": {"role": "assistant", "content": "질문을 입력해 주세요."}})

    try:
        print("🔄 채팅 요청 - DB에서 최신 데이터 가져오는 중...")
        if rag_processor.load_excel_data_from_db():
            if rag_processor.load_excel_data():
                if rag_processor.create_embeddings():
                    print("✅ 최신 데이터로 임베딩 재생성 완료")
                else:
                    print("⚠️ 임베딩 재생성 실패")

        search_results = rag_processor.search_documents(user_input, top_k=5, min_similarity=0.35)

        if search_results:
            response = generate_rag_response(user_input, search_results)
        else:
            response = get_gemini_response(user_input, apply_format=True)

        return jsonify({"message": {"role": "assistant", "content": response}})

    except Exception as e:
        return jsonify({"message": {"role": "assistant", "content": f"처리 중 오류가 발생했습니다: {str(e)}"}})

# 재고 관리 특화 프롬프트 (미사용 설명용)
INVENTORY_PROMPT_TEMPLATE = """당신은 PCB-Manager의 재고 관리 전문 AI 어시스턴트입니다.
... 생략 ...
"""

def analyze_inventory_intent(user_message):
    message_lower = user_message.lower()
    if any(keyword in message_lower for keyword in ["부족", "부족한", "low stock", "shortage", "없는", "떨어진"]):
        return "low_stock"
    if any(keyword in message_lower for keyword in ["흡습", "moisture", "습도", "humidity", "건조", "보관"]):
        return "moisture_management"
    if any(keyword in message_lower for keyword in ["발주", "주문", "order", "구매", "purchase", "신청"]):
        return "ordering"
    if re.search(r'[A-Z]{2}[0-9]{2}[A-Z0-9\-]{6,}', user_message.upper()):
        return "part_search"
    if any(keyword in message_lower for keyword in ["삼성", "samsung", "무라타", "murata", "tdk", "kemet"]):
        return "manufacturer_search"
    if any(keyword in message_lower for keyword in ["현황", "상태", "status", "재고량", "수량", "현재"]):
        return "inventory_status"
    if any(keyword in message_lower for keyword in ["통계", "분석", "analysis", "statistics", "총", "전체", "평균"]):
        return "statistics"
    return "general"

# 정확 일치 우선 조회
def fetch_exact_part(part_no: str):
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM pcb_parts WHERE part_number=%s", (part_no,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row
    except Exception as e:
        print("exact match 조회 오류:", e)
        return None

def generate_inventory_specific_response(user_message, search_results, intent):
    if not search_results:
        return f"""📦 재고 정보를 찾을 수 없습니다

'{user_message}'에 대한 정보를 데이터베이스에서 찾을 수 없습니다.
"""

    total_parts = len(search_results)
    context_parts = []

    for i, result in enumerate(search_results[:5]):
        doc = result['document']
        metadata = doc.get('metadata', {})
        similarity = result['similarity']

        # 컬럼 매핑 수정
        part_id = metadata.get('part_id', metadata.get('partId', 'Unknown'))
        product_name = metadata.get('part_number', metadata.get('product_name', metadata.get('product', 'Unknown')))
        manufacturer = metadata.get('manufacturer', 'Unknown')
        quantity = int(metadata.get('quantity', 0) or 0)
        min_stock = int(metadata.get('min_stock', metadata.get('minimumStock', 0)) or 0)
        moisture_absorption = bool(metadata.get('is_humidity_sensitive', metadata.get('moisture_absorption', False)))

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

    if intent == "part_search" and context_parts:
        p = context_parts[0]
        resp = f"""🔍 부품 검색 결과

**{p['product_name']}**
- 제조사: {p['manufacturer']}
- 현재재고: {p['quantity']}개 (최소: {p['min_stock']}개)
- 상태: {p['stock_status']}
- 보관조건: {p['moisture_status']}
- 검색 정확도: {p['similarity']:.1%}
"""
        if p['shortage'] > 0:
            resp += f"⚠️ 발주 필요: {p['shortage']}개 부족\n"
        return resp

    # 기타 의도 처리 간단 버전
    summary = [f"{i+1}. {p['product_name']} - {p['quantity']}개 ({p['stock_status']})"
               for i, p in enumerate(context_parts[:3])]
    return "📊 재고 분석 결과\n\n" + "\n".join(summary)

@chat4_bp.route('/inventory-chat', methods=['POST'])
def inventory_chat():
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

        intent = analyze_inventory_intent(user_message)
        print(f"[🧠] 분석된 의도: {intent}")

        # 1) 정확 일치 우선 반환
        exact = fetch_exact_part(user_message)
        if exact:
            moisture_status = "💧 흡습관리필요" if exact.get('is_humidity_sensitive') else "🌞 일반보관"
            return jsonify({
                "response": f"""🔍 부품 검색 결과

**{exact.get('part_number','-')}**
- 제조사: {exact.get('manufacturer','-')}
- 사이즈: {exact.get('size','-')}
- 입고일: {exact.get('received_date','-')}
- 현재재고: {int(exact.get('quantity',0))}개 (최소: {int(exact.get('min_stock',0))}개)
- 보관조건: {moisture_status}
""",
                "intent": "part_search",
                "search_results_count": 1,
                "timestamp": datetime.now().isoformat(),
                "success": True
            })

        # 2) 최신 데이터 로드 및 임베딩
        print("[📊] DB에서 최신 재고 데이터 가져오는 중...")
        if rag_processor.load_excel_data_from_db():
            if rag_processor.load_excel_data():
                if rag_processor.create_embeddings():
                    print("✅ 최신 데이터로 임베딩 재생성 완료")
            else:
                print("⚠️ 임베딩 재생성 실패")

        # 3) RAG 검색 (보수적 파라미터)
        search_results = rag_processor.search_documents(user_message, top_k=5, min_similarity=0.35)
        print(f"[🔍] 검색 결과: {len(search_results)}개 문서")

        if search_results:
            response = generate_inventory_specific_response(user_message, search_results, intent)
        else:
            response = f"""📦 재고 정보를 찾을 수 없습니다

'{user_message}'에 대한 정보를 찾을 수 없습니다.
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


@chat4_bp.route('/quick_actions', methods=['POST', 'OPTIONS'])  # Alternative URL with underscore
def quick_actions():
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        action = data.get('action', '')
        print(f"[⚡] 빠른 액션 요청: {action}")

        action_queries = {
            "low_stock": "부족한 재고 부품 minimum stock shortage",
            "moisture_management": "흡습 관리 필요 moisture absorption humidity sensitive",
            "ordering_recommendation": "발주 추천 order recommendation low stock"
        }
        query = action_queries.get(action, action)

        if rag_processor.load_excel_data():
            rag_processor.create_embeddings()

        search_results = rag_processor.search_documents(query, top_k=10, min_similarity=0.3)
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
        return jsonify({"error": str(e), "success": False}), 500

@chat4_bp.route('/health', methods=['GET'])
def inventory_health():
    try:
        has_documents = len(rag_processor.documents) > 0
        has_embeddings = rag_processor.embeddings is not None

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

# 앱 시작시 초기화
initialize_rag_system()
