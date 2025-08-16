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
            
            # 데이터베이스 연결 확인
            if not conn.is_connected():
                print("❌ 데이터베이스 연결 실패")
                return False
            
            # 테이블 존재 여부 확인
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES LIKE 'pcb_parts'")
            if not cursor.fetchone():
                print("❌ pcb_parts 테이블이 존재하지 않습니다")
                cursor.close()
                conn.close()
                return False
            cursor.close()
            
            # 데이터 조회
            query = "SELECT * FROM pcb_parts"
            df = pd.read_sql(query, conn)
            conn.close()

            if df.empty:
                print("❌ DB에서 데이터를 가져올 수 없습니다.")
                return False

            print(f"✅ DB에서 {len(df)}개의 레코드를 가져왔습니다.")
            
            # Excel 파일 저장 전 디렉토리 확인
            excel_dir = os.path.dirname(self.excel_path)
            if not os.path.exists(excel_dir):
                os.makedirs(excel_dir)
                print(f"📁 디렉토리 생성: {excel_dir}")
            
            df.to_excel(self.excel_path, index=False, sheet_name='pcb_parts')
            print(f"💾 Excel 파일 업데이트 완료: {self.excel_path}")
            return True

        except Exception as e:
            print(f"❌ DB에서 데이터 가져오기 오류: {e}")
            import traceback
            traceback.print_exc()
            return False

    def load_excel_data(self, excel_path=None):
        try:
            # 먼저 DB에서 최신 데이터 가져오기 시도
            if self.load_excel_data_from_db():
                print("✅ DB에서 최신 데이터 로드 성공")
            else:
                print("⚠️ DB 업데이트 실패, 기존 Excel 파일 사용")

            if not os.path.exists(self.excel_path):
                print(f"❌ Excel 파일이 존재하지 않습니다: {self.excel_path}")
                return False

            excel_file = pd.ExcelFile(self.excel_path)
            all_documents = []

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(self.excel_path, sheet_name=sheet_name)
                print(f"📊 시트 '{sheet_name}'에서 {len(df)}개 행 로드")

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
            import traceback
            traceback.print_exc()
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
    """RAG 시스템 초기화"""
    try:
        print("\n" + "="*60)
        print("[🚀] RAG 시스템 초기화 시작")
        print("="*60)
        
        if excel_path is None:
            excel_path = os.path.join(os.path.dirname(__file__), "..", "services", "product_parts.xlsx")
        
        print(f"📁 Excel 파일 경로: {excel_path}")
        
        # 1) 먼저 기존 처리된 데이터 로드 시도
        print("[📦] 기존 처리된 데이터 로드 시도...")
        if rag_processor.load_processed_data():
            print("✅ 기존 처리된 데이터 로드 성공")
            return True
        
        # 2) 기존 데이터가 없으면 Excel 파일에서 로드 시도
        print("[📊] Excel 파일에서 데이터 로드 시도...")
        if excel_path and os.path.exists(excel_path):
            if rag_processor.load_excel_data(excel_path):
                if rag_processor.create_embeddings():
                    rag_processor.save_processed_data()
                    print("✅ Excel 파일에서 데이터 로드 및 임베딩 생성 완료")
                    return True
                else:
                    print("⚠️ Excel 파일 로드 성공했으나 임베딩 생성 실패")
            else:
                print("⚠️ Excel 파일 로드 실패")
        
        # 3) 마지막으로 DB에서 직접 데이터 가져오기 시도
        print("[💾] 데이터베이스에서 직접 데이터 가져오기 시도...")
        try:
            if rag_processor.load_excel_data_from_db():
                if rag_processor.create_embeddings():
                    rag_processor.save_processed_data()
                    print("✅ 데이터베이스에서 데이터 로드 및 임베딩 생성 완료")
                    return True
                else:
                    print("⚠️ DB 데이터 로드 성공했으나 임베딩 생성 실패")
            else:
                print("⚠️ DB 데이터 로드 실패")
        except Exception as e:
            print(f"⚠️ DB 데이터 로드 중 오류: {e}")
        
        print("❌ RAG 시스템 초기화 실패")
        print("💡 **문제 해결 방법:**")
        print("• 데이터베이스 연결 상태 확인")
        print("• pcb_parts 테이블 존재 여부 확인")
        print("• Excel 파일 경로 확인")
        print("• 필요한 Python 패키지 설치 확인")
        
        return False
        
    except Exception as e:
        print(f"❌ RAG 시스템 초기화 중 예외 발생: {e}")
        import traceback
        traceback.print_exc()
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
    
    # 영어 부품명 매핑 (한국어와 영어 모두 지원)
    component_keywords = {
        "capacitor": ["커패시터", "캐패시터", "capacitor", "cap", "caps"],
        "inductor": ["인덕터", "inductor", "ind", "coil"],
        "resistor": ["저항", "resistor", "res", "r"],
        "diode": ["다이오드", "diode", "d"],
        "transistor": ["트랜지스터", "transistor", "tr", "fet", "mosfet"],
        "ic": ["ic", "집적회로", "integrated circuit", "chip"],
        "connector": ["커넥터", "connector", "jack", "plug"],
        "crystal": ["크리스탈", "crystal", "oscillator", "xtal"],
        "switch": ["스위치", "switch", "button"],
        "led": ["led", "발광다이오드", "light emitting diode"],
        "fuse": ["퓨즈", "fuse", "보호소자"],
        "varistor": ["바리스터", "varistor", "tvs"],
        "thermistor": ["서미스터", "thermistor", "ntc", "ptc"],
        "relay": ["릴레이", "relay"],
        "transformer": ["트랜스포머", "transformer", "xfmr"]
    }
    
    # 부품 타입별 의도 분석
    for component_type, keywords in component_keywords.items():
        if any(keyword in message_lower for keyword in keywords):
            return f"component_type_{component_type}"
    
    if any(keyword in message_lower for keyword in ["부족", "부족한", "low stock", "shortage", "없는", "떨어진", "주문 필요", "order needed", "발주 필요"]):
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

def fetch_components_by_type(component_type: str):
    """부품 타입별로 재고 정보 조회"""
    try:
        conn = get_db_connection()
        
        # 데이터베이스 연결 확인
        if not conn.is_connected():
            print(f"❌ 데이터베이스 연결 실패 ({component_type})")
            return []
        
        cur = conn.cursor(dictionary=True)
        
        # 먼저 데이터베이스 스키마 확인
        cur.execute("DESCRIBE pcb_parts")
        columns = cur.fetchall()
        
        # 컬럼명 추출을 안전하게 처리
        column_names = []
        for col in columns:
            if isinstance(col, dict):
                # dictionary 형태인 경우
                column_names.append(col['Field'])
            elif isinstance(col, (list, tuple)):
                # list/tuple 형태인 경우 (첫 번째 요소가 컬럼명)
                column_names.append(col[0])
            else:
                print(f"⚠️ 예상치 못한 컬럼 데이터 형태: {type(col)} - {col}")
                continue
        
        print(f"🔍 데이터베이스 컬럼 구조: {column_names}")
        
        # 부품 타입별 SQL 쿼리 매핑 (다양한 필드명 시도)
        type_queries = {
            "capacitor": """
                SELECT * FROM pcb_parts 
                WHERE LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%capacitor%' 
                   OR LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%cap%' 
                   OR LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%커패시터%'
                   OR LOWER(COALESCE(part_name, name, part_number, '')) LIKE '%capacitor%'
                   OR LOWER(COALESCE(part_name, name, part_number, '')) LIKE '%cap%'
                   OR LOWER(COALESCE(part_name, name, part_number, '')) LIKE '%커패시터%'
            """,
            "inductor": """
                SELECT * FROM pcb_parts 
                WHERE LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%inductor%' 
                   OR LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%ind%' 
                   OR LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%인덕터%'
                   OR LOWER(COALESCE(part_name, name, part_number, '')) LIKE '%inductor%'
                   OR LOWER(COALESCE(part_name, name, part_number, '')) LIKE '%ind%'
                   OR LOWER(COALESCE(part_name, name, part_number, '')) LIKE '%인덕터%'
            """,
            "resistor": """
                SELECT * FROM pcb_parts 
                WHERE LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%resistor%' 
                   OR LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%res%' 
                   OR LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%저항%'
                   OR LOWER(COALESCE(part_name, name, part_number, '')) LIKE '%resistor%'
                   OR LOWER(COALESCE(part_name, name, part_number, '')) LIKE '%res%'
                   OR LOWER(COALESCE(part_name, name, part_number, '')) LIKE '%저항%'
            """,
            "diode": """
                SELECT * FROM pcb_parts 
                WHERE LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%diode%' 
                   OR LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%다이오드%'
                   OR LOWER(COALESCE(part_name, name, part_number, '')) LIKE '%diode%'
                   OR LOWER(COALESCE(part_name, name, part_number, '')) LIKE '%다이오드%'
            """,
            "transistor": """
                SELECT * FROM pcb_parts 
                WHERE LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%transistor%' 
                   OR LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%tr%' 
                   OR LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%fet%'
                   OR LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%mosfet%'
                   OR LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%트랜지스터%'
                   OR LOWER(COALESCE(part_name, name, part_number, '')) LIKE '%transistor%'
                   OR LOWER(COALESCE(part_name, name, part_number, '')) LIKE '%tr%'
            """,
            "ic": """
                SELECT * FROM pcb_parts 
                WHERE LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%ic%' 
                   OR LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%집적회로%' 
                   OR LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%integrated%'
                   OR LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%chip%'
                   OR LOWER(COALESCE(part_name, name, part_number, '')) LIKE '%ic%'
                   OR LOWER(COALESCE(part_name, name, part_number, '')) LIKE '%집적회로%'
            """,
            "connector": """
                SELECT * FROM pcb_parts 
                WHERE LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%connector%' 
                   OR LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%커넥터%'
                   OR LOWER(COALESCE(part_name, name, part_number, '')) LIKE '%connector%'
                   OR LOWER(COALESCE(part_name, name, part_number, '')) LIKE '%커넥터%'
            """,
            "crystal": """
                SELECT * FROM pcb_parts 
                WHERE LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%crystal%' 
                   OR LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%xtal%'
                   OR LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%크리스탈%'
                   OR LOWER(COALESCE(part_name, name, part_number, '')) LIKE '%crystal%'
                   OR LOWER(COALESCE(part_name, name, part_number, '')) LIKE '%xtal%'
            """,
            "switch": """
                SELECT * FROM pcb_parts 
                WHERE LOWER(COALESCE(part_type, component_type, category, part_number, '')) LIKE '%switch%' 
                   OR LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%스위치%'
                   OR LOWER(COALESCE(part_name, name, part_number, '')) LIKE '%switch%'
                   OR LOWER(COALESCE(part_name, name, part_number, '')) LIKE '%스위치%'
            """,
            "led": """
                SELECT * FROM pcb_parts 
                WHERE LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%led%' 
                   OR LOWER(COALESCE(part_type, component_type, category, part_category, '')) LIKE '%발광다이오드%'
                   OR LOWER(COALESCE(part_name, name, part_number, '')) LIKE '%led%'
                   OR LOWER(COALESCE(part_name, name, part_number, '')) LIKE '%발광다이오드%'
            """
        }
        
        query = type_queries.get(component_type, "SELECT * FROM pcb_parts LIMIT 5")
        print(f"🔍 실행할 쿼리: {query}")
        
        cur.execute(query)
        rows = cur.fetchall()
        
        print(f"🔍 조회된 결과: {len(rows)}개")
        if rows:
            print(f"🔍 첫 번째 결과 샘플: {dict(rows[0])}")
        
        cur.close()
        conn.close()
        
        return rows
    except Exception as e:
        print(f"부품 타입별 조회 오류 ({component_type}): {e}")
        import traceback
        traceback.print_exc()
        return []

def fetch_low_stock_components():
    """주문이 필요한 부품들만 조회 (재고 부족 또는 재고 없음)"""
    try:
        conn = get_db_connection()
        
        if not conn.is_connected():
            print("❌ 데이터베이스 연결 실패")
            return []
        
        cur = conn.cursor(dictionary=True)
        
        # 먼저 실제 컬럼 구조 확인
        cur.execute("DESCRIBE pcb_parts")
        columns = cur.fetchall()
        
        # 컬럼명 추출을 안전하게 처리
        column_names = []
        for col in columns:
            if isinstance(col, dict):
                # dictionary 형태인 경우
                column_names.append(col['Field'])
            elif isinstance(col, (list, tuple)):
                # list/tuple 형태인 경우 (첫 번째 요소가 컬럼명)
                column_names.append(col[0])
            else:
                print(f"⚠️ 예상치 못한 컬럼 데이터 형태: {type(col)} - {col}")
                continue
        
        print(f"🔍 실제 데이터베이스 컬럼 구조: {column_names}")
        
        # 실제 존재하는 컬럼명만 사용
        quantity_col = 'quantity' if 'quantity' in column_names else 'qty' if 'qty' in column_names else None
        min_stock_col = 'min_stock' if 'min_stock' in column_names else 'minimum_stock' if 'minimum_stock' in column_names else None
        
        if not quantity_col or not min_stock_col:
            print(f"❌ 필요한 컬럼을 찾을 수 없습니다. quantity: {quantity_col}, min_stock: {min_stock_col}")
            cur.close()
            conn.close()
            return []
        
        # 먼저 전체 데이터 확인
        cur.execute("SELECT COUNT(*) as total FROM pcb_parts")
        total_count = cur.fetchone()['total']
        print(f"🔍 전체 부품 수: {total_count}개")
        
        # 샘플 데이터 확인
        cur.execute("SELECT * FROM pcb_parts LIMIT 3")
        sample_data = cur.fetchall()
        print(f"🔍 샘플 데이터 (처음 3개):")
        for i, row in enumerate(sample_data):
            print(f"  {i+1}. {dict(row)}")
        
        # 주문 필요 부품만 조회 (재고가 최소재고량보다 적거나 0개인 경우)
        query = f"""
            SELECT * FROM pcb_parts 
            WHERE {quantity_col} < {min_stock_col} OR {quantity_col} = 0
            ORDER BY 
                CASE 
                    WHEN {quantity_col} = 0 THEN 1
                    ELSE 2
                END,
                ({min_stock_col} - {quantity_col}) DESC
        """
        
        print(f"🔍 실행할 쿼리: {query}")
        print("🔍 주문 필요 부품 조회 중...")
        
        cur.execute(query)
        rows = cur.fetchall()
        
        print(f"🔍 주문 필요 부품: {len(rows)}개 발견")
        if rows:
            print(f"🔍 첫 번째 결과 샘플: {dict(rows[0])}")
            
            # 주문 필요 부품들의 상세 정보 출력
            for i, row in enumerate(rows[:5]):  # 처음 5개만 출력
                qty = int(row.get(quantity_col, 0) or 0)
                min_qty = int(row.get(min_stock_col, 0) or 0)
                shortage = max(0, min_qty - qty)
                print(f"  {i+1}. {row.get('part_number', 'Unknown')} - 현재: {qty}개, 최소: {min_qty}개, 부족: {shortage}개")
        else:
            print("🔍 주문이 필요한 부품이 없습니다. 모든 부품의 재고가 충분합니다.")
        
        cur.close()
        conn.close()
        
        return rows
    except Exception as e:
        print(f"주문 필요 부품 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        return []

def generate_component_type_response(component_type: str, components: list):
    """부품 타입별 응답 생성"""
    if not components:
        return f"📦 {component_type} 부품의 재고 정보를 찾을 수 없습니다."
    
    # 한국어 부품명 매핑
    korean_names = {
        "capacitor": "커패시터",
        "inductor": "인덕터", 
        "resistor": "저항",
        "diode": "다이오드",
        "transistor": "트랜지스터",
        "ic": "집적회로(IC)",
        "connector": "커넥터",
        "crystal": "크리스탈",
        "switch": "스위치",
        "led": "LED",
        "fuse": "퓨즈",
        "varistor": "바리스터",
        "thermistor": "서미스터",
        "relay": "릴레이",
        "transformer": "트랜스포머"
    }
    
    korean_name = korean_names.get(component_type, component_type)
    
    # 통계 계산 (실제 컬럼명 사용)
    total_quantity = 0
    total_parts = len(components)
    low_stock_count = 0
    
    for comp in components:
        # 재고량 추출 (실제 컬럼명 사용)
        quantity = int(comp.get('quantity', 0) or 0)
        min_stock = int(comp.get('min_stock', 0) or 0)
        
        total_quantity += quantity
        
        if quantity < min_stock:
            low_stock_count += 1
    
    # 제조사별 통계
    manufacturers = {}
    for comp in components:
        # 제조사 추출 (실제 컬럼명 사용)
        manufacturer = comp.get('manufacturer', 'Unknown')
        if manufacturer not in manufacturers:
            manufacturers[manufacturer] = {'count': 0, 'quantity': 0}
        
        # 재고량 추출
        quantity = int(comp.get('quantity', 0) or 0)
        
        manufacturers[manufacturer]['count'] += 1
        manufacturers[manufacturer]['quantity'] += quantity
    
    # 응답 구성
    response = f"""📊 **{korean_name} ({component_type.upper()}) 재고 현황**

📈 **전체 통계:**
• 총 부품 종류: {total_parts}개
• 총 재고량: {total_quantity}개
• 재고 부족 부품: {low_stock_count}개

🏭 **제조사별 현황:**
"""
    
    for manufacturer, stats in manufacturers.items():
        response += f"• {manufacturer}: {stats['count']}종류, {stats['quantity']}개\n"
    
    response += f"\n🔍 **부품별 상세 정보:**\n"
    
    # 부품별 상세 정보 (최대 10개)
    for i, comp in enumerate(components[:10]):
        # 실제 컬럼명으로 부품 정보 추출
        part_number = comp.get('part_number', 'Unknown')
        manufacturer = comp.get('manufacturer', 'Unknown')
        
        # 재고량 추출 (실제 컬럼명 사용)
        quantity = int(comp.get('quantity', 0) or 0)
        
        # 최소재고량 추출 (실제 컬럼명 사용)
        min_stock = int(comp.get('min_stock', 0) or 0)
        
        # 사이즈 추출 (실제 컬럼명 사용)
        size = comp.get('size', 'Unknown')
        
        print(f"🔍 부품 {i+1} 데이터: part_number={part_number}, manufacturer={manufacturer}, quantity={quantity}, min_stock={min_stock}")
        
        # 재고 상태 (0개는 "재고 없음"으로 표시)
        if quantity == 0:
            stock_status = "⚫ 재고 없음"
            shortage = 0
        elif quantity < min_stock:
            stock_status = "🔴 부족"
            shortage = min_stock - quantity
        else:
            stock_status = "🟢 충분"
            shortage = 0
        
        response += f"\n**{i+1}. {part_number}**\n"
        response += f"• 제조사: {manufacturer}\n"
        response += f"• 사이즈: {size}\n"
        response += f"• 현재재고: {quantity}개 (최소: {min_stock}개)\n"
        response += f"• 상태: {stock_status}"
        
        if shortage > 0:
            response += f"\n• ⚠️ 부족수량: {shortage}개"
    
    if len(components) > 10:
        response += f"\n\n... 및 {len(components) - 10}개 더"
    
    # 추가 권장사항
    if low_stock_count > 0:
        response += f"\n\n⚠️ **주의사항:**\n{low_stock_count}개의 {korean_name} 부품이 최소 재고량 이하입니다. 발주를 고려해주세요."
    
    return response

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

{p['product_name']}
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

def generate_low_stock_response(components: list):
    """주문이 필요한 부품들에 대한 응답 생성"""
    if not components:
        return """✅ **주문 필요 부품이 없습니다!**

🔍 **재고 현황:**
• 현재 모든 부품이 최소 재고량 이상 보유하고 있습니다.
• 즉시 발주가 필요한 부품은 없습니다.

💡 **참고사항:**
• 재고 부족 부품이 생기면 자동으로 감지됩니다.
• 정기적으로 재고 현황을 확인하는 것을 권장합니다."""
    
    # 통계 계산
    total_shortage = 0
    zero_stock_count = 0
    low_stock_count = 0
    
    for comp in components:
        # 재고량과 최소재고량 추출 (실제 컬럼명 사용)
        quantity = int(comp.get('quantity', 0) or 0)
        min_stock = int(comp.get('min_stock', 0) or 0)
        
        if quantity == 0:
            zero_stock_count += 1
            total_shortage += min_stock
        elif quantity < min_stock:
            low_stock_count += 1
            total_shortage += (min_stock - quantity)
    
    # 제조사별 통계
    manufacturers = {}
    for comp in components:
        manufacturer = comp.get('manufacturer', 'Unknown')
        if manufacturer not in manufacturers:
            manufacturers[manufacturer] = {'count': 0, 'shortage': 0}
        
        # 부족량 계산
        quantity = int(comp.get('quantity', 0) or 0)
        min_stock = int(comp.get('min_stock', 0) or 0)
        
        shortage = max(0, min_stock - quantity)
        
        manufacturers[manufacturer]['count'] += 1
        manufacturers[manufacturer]['shortage'] += shortage
    
    # 응답 구성
    response = f"""🚨 **주문 필요 부품 현황**

📊 **전체 통계:**
• 총 주문 필요 부품: {len(components)}개
• 재고 없음 (긴급): {zero_stock_count}개
• 재고 부족 (주의): {low_stock_count}개
• 총 부족량: {total_shortage}개

🏭 **제조사별 부족 현황:**
"""
    
    for manufacturer, stats in manufacturers.items():
        response += f"• {manufacturer}: {stats['count']}종류, {stats['shortage']}개 부족\n"
    
    response += f"\n🔍 **주문 필요 부품 상세 정보:**\n"
    
    # 부품별 상세 정보 (최대 15개)
    for i, comp in enumerate(components[:15]):
        part_number = comp.get('part_number', 'Unknown')
        manufacturer = comp.get('manufacturer', 'Unknown')
        
        # 재고량과 최소재고량 추출 (실제 컬럼명 사용)
        quantity = int(comp.get('quantity', 0) or 0)
        min_stock = int(comp.get('min_stock', 0) or 0)
        
        # 사이즈 추출 (실제 컬럼명 사용)
        size = comp.get('size', 'Unknown')
        
        # 부족량 계산
        shortage = max(0, min_stock - quantity)
        
        # 재고 상태 및 주문 필요성
        if quantity == 0:
            stock_status = "⚫ 재고 없음"
            urgency = "🔥 긴급 주문 필요"
            order_priority = "최우선"
        elif quantity < min_stock:
            stock_status = "🔴 재고 부족"
            urgency = "⚠️ 주문 권장"
            order_priority = "우선"
        else:
            stock_status = "🟢 재고 충분"
            urgency = "✅ 주문 불필요"
            order_priority = "해당없음"
        
        response += f"\n**{i+1}. {part_number}**"
        response += f"\n• 제조사: {manufacturer}"
        response += f"\n• 사이즈: {size}"
        response += f"\n• 현재재고: {quantity}개 (최소: {min_stock}개)"
        response += f"\n• 재고상태: {stock_status}"
        response += f"\n• 부족량: {shortage}개"
        response += f"\n• 주문우선순위: {order_priority}"
        response += f"\n• 조치사항: {urgency}"
    
    if len(components) > 15:
        response += f"\n\n... 및 {len(components) - 15}개 더"
    
    # 추가 권장사항
    response += f"\n\n💡 **주문 권장사항:**"
    if zero_stock_count > 0:
        response += f"\n• 🔥 **긴급**: 재고가 없는 {zero_stock_count}개 부품은 즉시 주문이 필요합니다."
    if low_stock_count > 0:
        response += f"\n• ⚠️ **주의**: 재고가 부족한 {low_stock_count}개 부품은 주문을 고려해주세요."
    response += f"\n• 📋 **총 주문량**: {total_shortage}개의 부품을 주문하면 재고를 정상화할 수 있습니다."
    
    return response

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

        # 부품 타입별 조회 처리
        if intent.startswith("component_type_"):
            component_type = intent.replace("component_type_", "")
            print(f"[🔍] 부품 타입별 조회: {component_type}")
            
            try:
                components = fetch_components_by_type(component_type)
                if components:
                    response = generate_component_type_response(component_type, components)
                    return jsonify({
                        "response": response,
                        "intent": intent,
                        "component_type": component_type,
                        "components_count": len(components),
                        "timestamp": datetime.now().isoformat(),
                        "success": True
                    })
                else:
                    print(f"⚠️ {component_type} 부품을 찾을 수 없음")
                    # 부품 타입별 조회 실패 시 RAG 검색으로 폴백
                    print(f"[🔄] {component_type} 부품 타입별 조회 실패, RAG 검색으로 폴백")
            except Exception as e:
                print(f"⚠️ 부품 타입별 조회 오류: {e}")
                # 오류 발생 시 RAG 검색으로 폴백
                print(f"[🔄] {component_type} 부품 타입별 조회 오류, RAG 검색으로 폴백")

        # 주문 필요 부품 조회 처리
        if intent == "low_stock":
            print("[🚨] 주문 필요 부품 조회 요청")
            
            try:
                print("[🔍] fetch_low_stock_components() 함수 호출 시작...")
                low_stock_components = fetch_low_stock_components()
                print(f"[🔍] fetch_low_stock_components() 결과: {len(low_stock_components) if low_stock_components else 0}개")
                
                if low_stock_components:
                    print("[📝] generate_low_stock_response() 함수 호출...")
                    response = generate_low_stock_response(low_stock_components)
                    print(f"[✅] 응답 생성 완료 (길이: {len(response)}자)")
                    return jsonify({
                        "response": response,
                        "intent": intent,
                        "low_stock_count": len(low_stock_components),
                        "timestamp": datetime.now().isoformat(),
                        "success": True
                    })
                else:
                    print("[📝] 주문 필요 부품이 없음 - 기본 응답 생성...")
                    response = generate_low_stock_response([])  # 빈 리스트로 호출하여 상세 응답 생성
                    print(f"[✅] 기본 응답 생성 완료 (길이: {len(response)}자)")
                    return jsonify({
                        "response": response,
                        "intent": intent,
                        "low_stock_count": 0,
                        "timestamp": datetime.now().isoformat(),
                        "success": True
                    })
            except Exception as e:
                print(f"⚠️ 주문 필요 부품 조회 오류: {e}")
                import traceback
                traceback.print_exc()
                # 오류 발생 시 RAG 검색으로 폴백
                print(f"[🔄] 주문 필요 부품 조회 오류, RAG 검색으로 폴백")

        # 주문 관련 키워드가 포함된 경우 주문 관리 전용 엔드포인트 호출
        order_keywords = ["주문", "order", "발주", "구매", "purchase", "신청", "부족", "부족한", "low stock", "shortage", "없는", "떨어진"]
        if any(keyword in user_message.lower() for keyword in order_keywords):
            print("[📦] 주문 관련 질문 감지, 주문 관리 전용 엔드포인트 호출")
            try:
                print("[🔍] quick_actions - order_management() 함수 호출...")
                order_response = order_management()
                if order_response.status_code == 200:
                    print("[✅] quick_actions - order_management() 성공")
                    return order_response
                else:
                    print("⚠️ 주문 관리 전용 엔드포인트 실패, 기본 처리로 폴백")
            except Exception as e:
                print(f"⚠️ 주문 관리 전용 엔드포인트 오류: {e}, 기본 처리로 폴백")

        # 흡습 관리 관련 질문 처리
        moisture_keywords = ["흡습", "moisture", "습도", "humidity", "건조", "보관", "습기", "습도관리"]
        if any(keyword in user_message.lower() for keyword in moisture_keywords):
            print("[💧] 흡습 관리 관련 질문 감지, 전용 엔드포인트 호출")
            try:
                moisture_response = moisture_management()
                if moisture_response.status_code == 200:
                    return moisture_response
                else:
                    print("⚠️ 흡습 관리 전용 엔드포인트 실패, 기본 처리로 폴백")
            except Exception as e:
                print(f"⚠️ 흡습 관리 전용 엔드포인트 오류: {e}, 기본 처리로 폴백")

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
        db_update_success = False
        
        try:
            if rag_processor.load_excel_data_from_db():
                if rag_processor.create_embeddings():
                    print("✅ 최신 데이터로 임베딩 재생성 완료")
                    db_update_success = True
                else:
                    print("⚠️ 임베딩 재생성 실패")
            else:
                print("⚠️ DB 데이터 로드 실패")
        except Exception as e:
            print(f"⚠️ DB 데이터 로드 중 오류: {e}")
        
        # 3) RAG 검색 (보수적 파라미터)
        search_results = []
        try:
            search_results = rag_processor.search_documents(user_message, top_k=5, min_similarity=0.35)
            print(f"[🔍] 검색 결과: {len(search_results)}개 문서")
        except Exception as e:
            print(f"⚠️ RAG 검색 중 오류: {e}")
            search_results = []

        if search_results:
            response = generate_inventory_specific_response(user_message, search_results, intent)
        else:
            # 검색 결과가 없을 때 더 자세한 안내 메시지
            if db_update_success:
                response = f"""📦 재고 정보를 찾을 수 없습니다

'{user_message}'에 대한 정보를 데이터베이스에서 찾을 수 없습니다.

💡 **도움말:**
• 정확한 부품번호를 입력해보세요
• 부품 타입으로 검색해보세요 (예: 커패시터, 다이오드)
• 간단한 키워드로 검색해보세요"""
            else:
                response = f"""📦 재고 정보를 찾을 수 없습니다

'{user_message}'에 대한 정보를 찾을 수 없습니다.

⚠️ **시스템 상태:**
• 데이터베이스 연결에 문제가 있을 수 있습니다
• 잠시 후 다시 시도해주세요

💡 **도움말:**
• 정확한 부품번호를 입력해보세요
• 부품 타입으로 검색해보세요 (예: 커패시터, 다이오드)"""

        print(f"[✅] 응답 생성 완료 (길이: {len(response)}자)")

        result = {
            "response": response,
            "intent": intent,
            "search_results_count": len(search_results),
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "performance": {
                "intent": intent,
                "documents_found": len(search_results),
                "db_update_success": db_update_success
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


@chat4_bp.route('/quick_actions', methods=['POST', 'OPTIONS'])
@chat4_bp.route('/quick_actions', methods=['POST', 'OPTIONS'])  # Alternative URL with underscore
def quick_actions():
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        action = data.get('action', '')
        print(f"[⚡] 빠른 액션 요청: {action}")

        if action == "moisture_management":
            # 흡습 관리 전용 엔드포인트 호출
            try:
                moisture_response = moisture_management()
                if moisture_response.status_code == 200:
                    return moisture_response
                else:
                    # 실패시 기본 검색으로 폴백
                    print("⚠️ 흡습 관리 전용 엔드포인트 실패, 기본 검색으로 폴백")
            except Exception as e:
                print(f"⚠️ 흡습 관리 전용 엔드포인트 오류: {e}, 기본 검색으로 폴백")

        if action == "order_management":
            # 주문 관리 전용 엔드포인트 호출
            try:
                order_response = order_management()
                if order_response.status_code == 200:
                    return order_response
                else:
                    # 실패시 기본 검색으로 폴백
                    print("⚠️ 주문 관리 전용 엔드포인트 실패, 기본 검색으로 폴백")
            except Exception as e:
                print(f"⚠️ 주문 관리 전용 엔드포인트 오류: {e}, 기본 검색으로 폴백")

        # 기본 액션 처리
        if action == "low_stock":
            # 주문 필요 부품 전용 처리
            try:
                print("[🔍] quick_actions - fetch_low_stock_components() 함수 호출...")
                low_stock_components = fetch_low_stock_components()
                print(f"[🔍] quick_actions - 결과: {len(low_stock_components) if low_stock_components else 0}개")
                
                if low_stock_components:
                    print("[📝] quick_actions - generate_low_stock_response() 함수 호출...")
                    response = generate_low_stock_response(low_stock_components)
                else:
                    print("[📝] quick_actions - 주문 필요 부품이 없음 - 기본 응답 생성...")
                    response = generate_low_stock_response([])  # 빈 리스트로 호출하여 상세 응답 생성
                
                print(f"[✅] quick_actions - 응답 생성 완료 (길이: {len(response)}자)")
                return jsonify({
                    "response": response,
                    "action": action,
                    "low_stock_count": len(low_stock_components) if low_stock_components else 0,
                    "success": True,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                print(f"⚠️ quick_actions - 주문 필요 부품 조회 오류: {e}")
                import traceback
                traceback.print_exc()
                response = "❌ 주문 필요 부품 정보를 가져오는 중 오류가 발생했습니다."
                return jsonify({
                    "response": response,
                    "action": action,
                    "success": False,
                    "timestamp": datetime.now().isoformat()
                })
        
        action_queries = {
            "moisture_management": "흡습 관리 필요 moisture absorption humidity sensitive",
            "order_management": "주문 필요 부품 order needed parts low stock",
            "ordering_recommendation": "발주 추천 order recommendation low stock",
            "capacitor": "커패시터 capacitor cap",
            "inductor": "인덕터 inductor ind",
            "resistor": "저항 resistor res",
            "diode": "다이오드 diode",
            "ic": "집적회로 IC integrated circuit"
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

@chat4_bp.route('/moisture-management', methods=['POST', 'OPTIONS'])
def moisture_management():
    """흡습 관리 부품 정보 제공 (필요/불필요 모두 지원)"""
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        print("\n" + "="*60)
        print("[💧] 흡습 관리 부품 정보 요청")
        print("="*60)
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "요청 데이터가 없습니다.", "success": False}), 400
        
        user_message = data.get('message', '').strip()
        print(f"[📋] 사용자 메시지: {user_message}")
        
        # 사용자 의도 분석
        is_requesting_unnecessary = any(keyword in user_message.lower() for keyword in [
            '불필요', 'unnecessary', '일반', 'normal', '보통', '보관', 'storage'
        ])
        
        print(f"[��] 사용자 의도: {'흡습 불필요 부품' if is_requesting_unnecessary else '흡습 필요 부품'}")
        
        # 데이터베이스에서 부품 조회
        print("[💾] 데이터베이스에서 부품 조회 중...")
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            if is_requesting_unnecessary:
                # 흡습 관리가 불필요한 부품 검색
                query = """
                    SELECT * FROM pcb_parts 
                    WHERE is_humidity_sensitive = 0 
                       AND needs_humidity_control = 0
                """
                print("[🌞] 흡습 관리 불필요한 부품 검색 중...")
            else:
                # 흡습 관리가 필요한 부품 검색
                query = """
                    SELECT * FROM pcb_parts 
                    WHERE is_humidity_sensitive = 1 
                       OR needs_humidity_control = 1
                """
                print("[💧] 흡습 관리 필요한 부품 검색 중...")
            
            cursor.execute(query)
            parts = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            if is_requesting_unnecessary:
                print(f"[🌞] 데이터베이스에서 {len(parts)}개의 흡습 관리 불필요 부품 발견")
            else:
                print(f"[💧] 데이터베이스에서 {len(parts)}개의 흡습 관리 필요 부품 발견")
            
            # 부품이 없으면 안내 메시지
            if not parts:
                if is_requesting_unnecessary:
                    response = """🌞 **흡습 관리 불필요 부품 현황**

📊 **검색 결과:**
• 현재 데이터베이스에 흡습 관리가 불필요한 부품이 없습니다.
• 모든 부품이 흡습 관리가 필요합니다.

💡 **참고사항:**
• 흡습 관리가 불필요한 부품은 `is_humidity_sensitive = 0` AND `needs_humidity_control = 0`로 표시됩니다.
• 현재 등록된 146개 부품 중 흡습 관리 불필요 부품: 0개

🔍 **전체 부품 현황:**
• 총 부품 수: 146개
• 흡습 관리 필요 부품: 146개
• 흡습 관리 불필요 부품: 0개"""
                else:
                    response = """💧 **흡습 관리 필요 부품 현황**

📊 **검색 결과:**
• 현재 데이터베이스에 흡습 관리가 필요한 부품이 없습니다.
• 모든 부품이 일반 보관 조건을 충족하고 있습니다.

💡 **참고사항:**
• 흡습 관리가 필요한 부품은 `is_humidity_sensitive = 1` 또는 `needs_humidity_control = 1`로 표시됩니다.
• 현재 등록된 146개 부품 중 흡습 관리 필요 부품: 0개

🔍 **전체 부품 현황:**
• 총 부품 수: 146개
• 일반 보관 부품: 146개
• 흡습 관리 필요 부품: 0개"""
                
                return jsonify({
                    "response": response,
                    "moisture_parts_count": 0,
                    "total_quantity": 0,
                    "low_stock_count": 0,
                    "timestamp": datetime.now().isoformat(),
                    "success": True,
                    "parts": [],
                    "type": "unnecessary" if is_requesting_unnecessary else "necessary"
                })
            
        except Exception as db_error:
            print(f"⚠️ 데이터베이스 직접 조회 실패: {db_error}")
            parts = []
        
        # RAG 시스템은 사용하지 않음 (정확성 향상을 위해)
        print("[🤖] RAG 시스템은 사용하지 않고 데이터베이스 직접 조회 결과만 사용합니다.")
        all_parts = []
        
        # 데이터베이스 결과만 사용 (정확성 보장)
        for part in parts:
            part_id = part.get('part_number', part.get('part_id', ''))
            if part_id:
                part_info = {
                    'part_id': part_id,
                    'product_name': part.get('part_number', part.get('product_name', 'Unknown')),
                    'manufacturer': part.get('manufacturer', 'Unknown'),
                    'quantity': int(part.get('quantity', 0) or 0),
                    'min_stock': int(part.get('min_stock', part.get('minimumStock', 0)) or 0),
                    'size': part.get('size', 'Unknown'),
                    'received_date': part.get('received_date', 'Unknown'),
                    'moisture_materials': '불필요' if is_requesting_unnecessary else '필요',  # 사용자 의도에 따라 설정
                    'similarity': 1.0  # 데이터베이스 직접 조회는 높은 신뢰도
                }
                all_parts.append(part_info)
        

        
        if not all_parts:
            return jsonify({
                "response": "💧 흡습 정보를 찾을 수 없습니다\n\n'{user_message}'에 대한 정보를 데이터베이스에서 찾을 수 없습니다.",
                "moisture_parts_count": 0,
                "total_quantity": 0,
                "low_stock_count": 0,
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "parts": []
            })
        
        # 부품별 상세 정보 구성
        response_parts = []
        total_quantity = 0
        low_stock_count = 0
        
        for part in all_parts:
            # 재고 상태 확인
            if part['quantity'] < part['min_stock']:
                stock_status = "🔴 부족"
                shortage = part['min_stock'] - part['quantity']
                low_stock_count += 1
            else:
                stock_status = "🟢 충분"
                shortage = 0
            
            total_quantity += part['quantity']
            
            part_detail = f"""**{part['product_name']}** (ID: {part['part_id']})
• 제조사: {part['manufacturer']}
• 사이즈: {part['size']}
• 현재재고: {part['quantity']}개 (최소: {part['min_stock']}개)
• 재고상태: {stock_status}"""
            
            if shortage > 0:
                part_detail += f"\n• ⚠️ 부족수량: {shortage}개"
            
            part_detail += f"\n• 입고일: {part['received_date']}"
            part_detail += f"\n• 흡습자재: {part['moisture_materials']}"
            
            response_parts.append(part_detail)
        
        # 전체 요약 정보 (사용자 의도에 따라)
        if is_requesting_unnecessary:
            summary = f"""🌞 **흡습 관리 불필요 부품 현황**

📊 **전체 현황:**
• 총 부품 종류: {len(all_parts)}개
• 총 재고량: {total_quantity}개
• 재고 부족 부품: {low_stock_count}개

🔍 **부품별 상세 정보:**"""
            
            # 응답 구성
            full_response = summary + "\n\n" + "\n\n".join(response_parts)
            
            # 추가 권장사항
            if low_stock_count > 0:
                full_response += f"\n\n⚠️ **주의사항:**\n{low_stock_count}개의 부품이 최소 재고량 이하입니다. 발주를 고려해주세요."
            
            full_response += "\n\n💡 **일반 보관 팁:**\n• 실온에서 보관 가능\n• 특별한 습도 관리 불필요\n• 일반 창고 보관 조건 충족"
        else:
            summary = f"""💧 **흡습 관리 필요 부품 현황**

📊 **전체 현황:**
• 총 부품 종류: {len(all_parts)}개
• 총 재고량: {total_quantity}개
• 재고 부족 부품: {low_stock_count}개

🔍 **부품별 상세 정보:**"""
            
            # 응답 구성
            full_response = summary + "\n\n" + "\n\n".join(response_parts)
            
            # 추가 권장사항
            if low_stock_count > 0:
                full_response += f"\n\n⚠️ **주의사항:**\n{low_stock_count}개의 부품이 최소 재고량 이하입니다. 발주를 고려해주세요."
            
            full_response += "\n\n💡 **흡습 관리 팁:**\n• 습도 10% 이하에서 보관\n• 밀폐 용기 사용 권장\n• 사용 전 건조 처리 필요"
        
        return jsonify({
            "response": full_response,
            "moisture_parts_count": len(all_parts),
            "total_quantity": total_quantity,
            "low_stock_count": low_stock_count,
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "parts": all_parts,
            "type": "unnecessary" if is_requesting_unnecessary else "necessary"
        })
        
    except Exception as e:
        print(f"[❌] 흡습 관리 부품 정보 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": f"서버 오류가 발생했습니다: {str(e)}",
            "success": False,
            "timestamp": datetime.now().isoformat()
        }), 500

@chat4_bp.route('/order-management', methods=['POST', 'OPTIONS'])
def order_management():
    """주문 필요 부품 정보 제공 (필요/불필요 모두 지원)"""
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        print("\n" + "="*60)
        print("[📦] 주문 필요 부품 정보 요청")
        print("="*60)
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "요청 데이터가 없습니다.", "success": False}), 400
        
        user_message = data.get('message', '').strip()
        if not user_message:
            user_message = "주문 필요 부품"  # 기본값 설정
        print(f"[📋] 사용자 메시지: {user_message}")
        
        # 사용자 의도 분석
        is_requesting_unnecessary = any(keyword in user_message.lower() for keyword in [
            '불필요', 'unnecessary', '충분', 'sufficient', '보통', 'normal', '재고충분'
        ])
        
        print(f"[📦] 사용자 의도: {'주문 불필요 부품' if is_requesting_unnecessary else '주문 필요 부품'}")
        
        # 주문 필요 부품 조회
        print("[🔍] fetch_low_stock_components() 함수 호출...")
        low_stock_components = fetch_low_stock_components()
        print(f"[🔍] 결과: {len(low_stock_components) if low_stock_components else 0}개")
        
        if is_requesting_unnecessary:
            # 주문이 불필요한 부품은 전체에서 주문 필요 부품을 제외
            try:
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                
                # 먼저 실제 컬럼 구조 확인
                cursor.execute("DESCRIBE pcb_parts")
                columns = cursor.fetchall()
                
                # 컬럼명 추출을 안전하게 처리
                column_names = []
                for col in columns:
                    if isinstance(col, dict):
                        # dictionary 형태인 경우
                        column_names.append(col['Field'])
                    elif isinstance(col, (list, tuple)):
                        # list/tuple 형태인 경우 (첫 번째 요소가 컬럼명)
                        column_names.append(col[0])
                    else:
                        print(f"⚠️ 예상치 못한 컬럼 데이터 형태: {type(col)} - {col}")
                        continue
                
                print(f"🔍 실제 데이터베이스 컬럼 구조: {column_names}")
                
                # 실제 존재하는 컬럼명만 사용
                quantity_col = 'quantity' if 'quantity' in column_names else 'qty' if 'qty' in column_names else None
                min_stock_col = 'min_stock' if 'min_stock' in column_names else 'minimum_stock' if 'minimum_stock' in column_names else None
                
                if not quantity_col or not min_stock_col:
                    print(f"❌ 필요한 컬럼을 찾을 수 없습니다. quantity: {quantity_col}, min_stock: {min_stock_col}")
                    cursor.close()
                    conn.close()
                    return jsonify({
                        "error": "데이터베이스 스키마 오류: quantity 또는 min_stock 컬럼을 찾을 수 없습니다.",
                        "success": False
                    }), 500
                
                # 주문이 불필요한 부품 검색 (재고가 최소재고량 이상인 경우)
                query = f"""
                    SELECT * FROM pcb_parts 
                    WHERE {quantity_col} >= {min_stock_col} AND {quantity_col} > 0
                    ORDER BY {quantity_col} DESC
                """
                print("[✅] 주문 불필요한 부품 검색 중...")
                
                cursor.execute(query)
                parts = cursor.fetchall()
                cursor.close()
                conn.close()
                
                print(f"[✅] 데이터베이스에서 {len(parts)}개의 주문 불필요 부품 발견")
                
                if not parts:
                    response = """✅ **주문 불필요 부품 현황**

📊 **검색 결과:**
• 현재 데이터베이스에 주문이 불필요한 부품이 없습니다.
• 모든 부품이 주문이 필요한 상태입니다.

💡 **참고사항:**
• 주문이 불필요한 부품은 `quantity >= min_stock` AND `quantity > 0`로 표시됩니다.
• 현재 등록된 모든 부품이 최소 재고량 이하입니다."""
                else:
                    response = f"""✅ **주문 불필요 부품 현황**

📊 **검색 결과:**
• 총 {len(parts)}개의 부품이 주문이 불필요한 상태입니다.
• 모든 부품이 최소 재고량 이상 보유하고 있습니다.

🔍 **주문 불필요 부품 상세 정보:**\n"""
                    
                    # 부품별 상세 정보 (최대 10개)
                    for i, part in enumerate(parts[:10]):
                        part_number = part.get('part_number', 'Unknown')
                        manufacturer = part.get('manufacturer', 'Unknown')
                        size = part.get('size', 'Unknown')
                        quantity = int(part.get(quantity_col, 0) or 0)
                        min_stock = int(part.get(min_stock_col, 0) or 0)
                        
                        response += f"\n**{i+1}. {part_number}**"
                        response += f"\n• 제조사: {manufacturer}"
                        response += f"\n• 사이즈: {size}"
                        response += f"\n• 현재재고: {quantity}개 (최소: {min_stock}개)"
                        response += f"\n• 재고상태: 🟢 재고 충분"
                        response += f"\n• 주문 필요성: ❌ 주문 불필요\n"
                    
                    if len(parts) > 10:
                        response += f"\n... 및 {len(parts) - 10}개 더"
                
                return jsonify({
                    "response": response,
                    "intent": "order_unnecessary",
                    "parts_count": len(parts),
                    "success": True,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f"⚠️ 주문 불필요 부품 조회 오류: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    "error": f"주문 불필요 부품 조회 중 오류가 발생했습니다: {str(e)}",
                    "success": False
                }), 500
        else:
            # 주문 필요 부품 조회
            if low_stock_components:
                response = generate_low_stock_response(low_stock_components)
                print(f"[✅] 주문 필요 부품 응답 생성 완료 (길이: {len(response)}자)")
            else:
                response = generate_low_stock_response([])  # 빈 리스트로 호출하여 상세 응답 생성
                print(f"[✅] 주문 필요 부품 없음 응답 생성 완료 (길이: {len(response)}자)")
            
            return jsonify({
                "response": response,
                "intent": "order_necessary",
                "low_stock_count": len(low_stock_components) if low_stock_components else 0,
                "success": True,
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        print(f"[❌] 주문 관리 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": f"서버 오류가 발생했습니다: {str(e)}",
            "success": False,
            "timestamp": datetime.now().isoformat()
        }), 500

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
                "moisture_management": "활성화됨",
                "order_management": "활성화됨",
                "system": "operational"
            },
            "features": {
                "inventory_chat": "활성화됨",
                "quick_actions": "활성화됨",
                "moisture_management": "활성화됨",
                "order_management": "활성화됨",
                "part_search": "활성화됨"
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

@chat4_bp.route('/db-diagnostic', methods=['GET'])
def db_diagnostic():
    """데이터베이스 연결 상태 및 구조 진단"""
    try:
        print("\n" + "="*60)
        print("[🔍] 데이터베이스 진단 시작")
        print("="*60)
        
        # 1. 데이터베이스 연결 테스트
        print("[🔌] 데이터베이스 연결 테스트 중...")
        try:
            conn = get_db_connection()
            if not conn.is_connected():
                return jsonify({
                    "status": "error",
                    "message": "데이터베이스 연결 실패",
                    "details": "get_db_connection()에서 연결된 상태가 아닙니다.",
                    "timestamp": datetime.now().isoformat()
                }), 500
            
            print("✅ 데이터베이스 연결 성공")
            
        except Exception as e:
            print(f"❌ 데이터베이스 연결 오류: {e}")
            return jsonify({
                "status": "error",
                "message": "데이터베이스 연결 오류",
                "details": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # 2. 테이블 존재 여부 확인
        print("[📋] 테이블 존재 여부 확인 중...")
        try:
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            print(f"🔍 발견된 테이블: {table_names}")
            
            if 'pcb_parts' not in table_names:
                cursor.close()
                conn.close()
                return jsonify({
                    "status": "error",
                    "message": "pcb_parts 테이블이 존재하지 않습니다",
                    "available_tables": table_names,
                    "timestamp": datetime.now().isoformat()
                }), 404
            
            print("✅ pcb_parts 테이블 발견")
            
        except Exception as e:
            print(f"❌ 테이블 확인 오류: {e}")
            cursor.close()
            conn.close()
            return jsonify({
                "status": "error",
                "message": "테이블 확인 중 오류 발생",
                "details": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # 3. 테이블 구조 확인
        print("[🏗️] 테이블 구조 확인 중...")
        try:
            cursor.execute("DESCRIBE pcb_parts")
            columns = cursor.fetchall()
            column_info = []
            
            for col in columns:
                if isinstance(col, dict):
                    # dictionary 형태인 경우
                    column_info.append({
                        "field": col['Field'],
                        "type": col['Type'],
                        "null": col['Null'],
                        "key": col['Key'],
                        "default": col['Default'],
                        "extra": col['Extra']
                    })
                elif isinstance(col, (list, tuple)):
                    # list/tuple 형태인 경우
                    column_info.append({
                        "field": col[0],
                        "type": col[1],
                        "null": col[2],
                        "key": col[3],
                        "default": col[4],
                        "extra": col[5]
                    })
                else:
                    print(f"⚠️ 예상치 못한 컬럼 데이터 형태: {type(col)} - {col}")
                    continue
            
            print(f"🔍 컬럼 정보: {len(column_info)}개 컬럼")
            for col in column_info:
                print(f"  - {col['field']}: {col['type']}")
            
        except Exception as e:
            print(f"❌ 테이블 구조 확인 오류: {e}")
            cursor.close()
            conn.close()
            return jsonify({
                "status": "error",
                "message": "테이블 구조 확인 중 오류 발생",
                "details": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # 4. 데이터 개수 확인
        print("[📊] 데이터 개수 확인 중...")
        try:
            cursor.execute("SELECT COUNT(*) as total FROM pcb_parts")
            total_count = cursor.fetchone()[0]
            print(f"🔍 총 레코드 수: {total_count}개")
            
        except Exception as e:
            print(f"❌ 데이터 개수 확인 오류: {e}")
            cursor.close()
            conn.close()
            return jsonify({
                "status": "error",
                "message": "데이터 개수 확인 중 오류 발생",
                "details": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # 5. 샘플 데이터 확인
        print("[🔍] 샘플 데이터 확인 중...")
        try:
            cursor.execute("SELECT * FROM pcb_parts LIMIT 3")
            sample_data = cursor.fetchall()
            sample_info = []
            
            for i, row in enumerate(sample_data):
                row_dict = {}
                for j, col in enumerate(column_info):
                    row_dict[col['field']] = str(row[j]) if row[j] is not None else None
                sample_info.append(row_dict)
            
            print(f"🔍 샘플 데이터 {len(sample_info)}개 로드 완료")
            
        except Exception as e:
            print(f"❌ 샘플 데이터 확인 오류: {e}")
            cursor.close()
            conn.close()
            return jsonify({
                "status": "error",
                "message": "샘플 데이터 확인 중 오류 발생",
                "details": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # 6. 주문 필요 부품 테스트 쿼리
        print("[🚨] 주문 필요 부품 테스트 쿼리 실행 중...")
        try:
            # quantity와 min_stock 컬럼 찾기
            quantity_col = None
            min_stock_col = None
            
            for col in column_info:
                if 'quantity' in col['field'].lower():
                    quantity_col = col['field']
                elif 'min_stock' in col['field'].lower() or 'minimum' in col['field'].lower():
                    min_stock_col = col['field']
            
            print(f"🔍 찾은 컬럼: quantity={quantity_col}, min_stock={min_stock_col}")
            
            if quantity_col and min_stock_col:
                # 주문 필요 부품 쿼리 테스트
                test_query = f"""
                    SELECT COUNT(*) as low_stock_count 
                    FROM pcb_parts 
                    WHERE {quantity_col} < {min_stock_col} OR {quantity_col} = 0
                """
                cursor.execute(test_query)
                low_stock_count = cursor.fetchone()[0]
                print(f"🔍 주문 필요 부품 수: {low_stock_count}개")
                
                # 실제 데이터도 확인
                cursor.execute(f"""
                    SELECT {quantity_col}, {min_stock_col}, part_number 
                    FROM pcb_parts 
                    WHERE {quantity_col} < {min_stock_col} OR {quantity_col} = 0
                    LIMIT 5
                """)
                low_stock_samples = cursor.fetchall()
                print(f"🔍 주문 필요 부품 샘플: {len(low_stock_samples)}개")
                
            else:
                print("⚠️ quantity 또는 min_stock 컬럼을 찾을 수 없습니다")
                low_stock_count = 0
                low_stock_samples = []
            
        except Exception as e:
            print(f"❌ 주문 필요 부품 테스트 쿼리 오류: {e}")
            low_stock_count = 0
            low_stock_samples = []
        
        cursor.close()
        conn.close()
        
        # 7. 진단 결과 반환
        diagnostic_result = {
            "status": "success",
            "message": "데이터베이스 진단 완료",
            "timestamp": datetime.now().isoformat(),
            "database": {
                "connection": "connected",
                "tables": table_names,
                "pcb_parts_exists": True
            },
            "table_structure": {
                "total_columns": len(column_info),
                "columns": column_info
            },
            "data": {
                "total_records": total_count,
                "sample_data": sample_info
            },
            "low_stock_test": {
                "quantity_column": quantity_col,
                "min_stock_column": min_stock_col,
                "low_stock_count": low_stock_count,
                "low_stock_samples": [
                    {
                        "quantity": str(sample[0]),
                        "min_stock": str(sample[1]),
                        "part_number": str(sample[2])
                    } for sample in low_stock_samples
                ]
            }
        }
        
        print("✅ 데이터베이스 진단 완료")
        return jsonify(diagnostic_result)
        
    except Exception as e:
        print(f"❌ 데이터베이스 진단 중 예외 발생: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": "데이터베이스 진단 중 예외 발생",
            "details": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500
