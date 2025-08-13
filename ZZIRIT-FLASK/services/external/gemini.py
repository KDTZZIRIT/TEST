import google.generativeai as genai
import os
import logging
from typing import Optional
from dotenv import load_dotenv
import sys
from pathlib import Path
import time
import json

# 현재 파일 위치: ZZIRIT-FLASK/api/gemini_handler.py
# .env 파일 위치: ZZIRIT-FLASK/.env

# 프로젝트 루트 디렉토리 찾기
current_file = Path(__file__).resolve()
api_dir = current_file.parent
root_dir = api_dir.parent
env_path = root_dir / '.env'

# 디버깅 정보 출력
print(f"🔍 현재 파일: {current_file}")
print(f"🔍 API 디렉토리: {api_dir}")
print(f"🔍 루트 디렉토리: {root_dir}")
print(f"🔍 .env 경로: {env_path}")
print(f"🔍 .env 존재: {'✅' if env_path.exists() else '❌'}")

# .env 파일 로드
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"✅ .env 파일 로드 성공: {env_path}")
else:
    print(f"⚠️ {env_path}에서 .env를 찾을 수 없음")
    print(f"현재 작업 디렉토리에서 시도: {os.getcwd()}")
    load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 환경변수에서 API 키 가져오기
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 디버깅: API 키 확인
print(f"🔑 환경변수 GEMINI_API_KEY: {'✅ 설정됨' if GEMINI_API_KEY else '❌ 설정 안됨'}")
if GEMINI_API_KEY:
    print(f"🔑 API 키 앞 10자리: {GEMINI_API_KEY[:10]}...")
else:
    print(f"🔑 현재 환경변수들: {[k for k in os.environ.keys() if 'GEMINI' in k.upper()]}")

# 전역 변수
model = None
chat_session = None
READY = False
INITIALIZATION_ATTEMPTS = 0
MAX_RETRIES = 3
REQUEST_COUNT = 0
SUCCESSFUL_REQUESTS = 0
FAILED_REQUESTS = 0
LAST_REQUEST_TIME = None

def initialize_gemini(retry_count=0):
    """Gemini 초기화 (개선된 버전)"""
    global model, chat_session, READY, INITIALIZATION_ATTEMPTS
    
    INITIALIZATION_ATTEMPTS += 1
    
    try:
        if not GEMINI_API_KEY:
            logger.error("❌ GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
            print("❌ GEMINI_API_KEY 환경변수를 설정해주세요.")
            print(f"💡 .env 파일 경로: {env_path}")
            print(f"💡 .env 파일 존재: {'Yes' if env_path.exists() else 'No'}")
            
            if env_path.exists():
                print("💡 .env 파일 내용 확인:")
                try:
                    with open(env_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')
                        for line in lines:
                            if line.strip() and not line.startswith('#'):
                                if 'GEMINI_API_KEY' in line:
                                    key, value = line.split('=', 1)
                                    print(f"    {key}={value[:10] + '...' if len(value) > 10 else value}")
                                else:
                                    print(f"    {line}")
                except Exception as e:
                    print(f"💡 .env 파일 읽기 오류: {e}")
            
            READY = False
            return False
        
        print(f"🤖 Gemini 설정 시작... (시도 {INITIALIZATION_ATTEMPTS}회)")
        
        # Gemini 설정
        genai.configure(api_key=GEMINI_API_KEY)
        
        # 모델 생성 설정 (개선된 버전)
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,
            "response_mime_type": "text/plain"
        }
        
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        # 모델 생성
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
            safety_settings=safety_settings,
            system_instruction="당신은 PCB 제조 및 관리 전문가입니다. 한국어로 정확하고 도움이 되는 답변을 제공해주세요."
        )
        
        print("🧪 Gemini 연결 테스트...")
        
        # 연결 테스트 (간단한 프롬프트)
        test_prompt = "안녕하세요. 'OK'라고 간단히 답변해주세요."
        test_response = model.generate_content(test_prompt)
        
        if test_response and test_response.text:
            # 채팅 세션 초기화
            chat_session = model.start_chat()
            
            logger.info("✅ Gemini 초기화 성공")
            print("✅ Gemini API 연결 성공")
            print(f"✅ 테스트 응답: {test_response.text.strip()[:50]}...")
            print(f"✅ 모델: {model.model_name}")
            READY = True
            return True
        else:
            raise Exception("테스트 응답이 비어있습니다.")
            
    except Exception as e:
        logger.error(f"❌ Gemini 초기화 실패 (시도 {INITIALIZATION_ATTEMPTS}회): {e}")
        print(f"❌ Gemini 초기화 실패: {e}")
        
        # 구체적인 오류 정보 제공
        error_str = str(e).lower()
        
        if "api_key" in error_str or "key" in error_str or "authentication" in error_str:
            print("💡 API 키 관련 오류입니다. API 키를 확인해주세요.")
            print("   - API 키가 올바른지 확인")
            print("   - API 키에 Gemini API 권한이 있는지 확인")
            print("   - Google AI Studio에서 API 키 상태 확인")
            
        elif "quota" in error_str or "limit" in error_str:
            print("💡 할당량 초과 오류입니다.")
            print("   - API 사용량 한도를 확인해주세요")
            print("   - 잠시 후 다시 시도해주세요")
            
        elif "network" in error_str or "connection" in error_str:
            print("💡 네트워크 연결 오류입니다.")
            print("   - 인터넷 연결을 확인해주세요")
            print("   - 방화벽 설정을 확인해주세요")
            
        elif "timeout" in error_str:
            print("💡 응답 시간 초과 오류입니다.")
            print("   - 네트워크 상태를 확인해주세요")
            print("   - 잠시 후 다시 시도해주세요")
            
        # 재시도 로직
        if retry_count < MAX_RETRIES:
            wait_time = (retry_count + 1) * 2  # 2, 4, 6초 대기
            print(f"🔄 {wait_time}초 후 재시도... ({retry_count + 1}/{MAX_RETRIES})")
            time.sleep(wait_time)
            return initialize_gemini(retry_count + 1)
        else:
            print(f"❌ 최대 재시도 횟수({MAX_RETRIES})를 초과했습니다.")
        
        READY = False
        return False

def get_gemini_response(prompt: str, use_chat_session: bool = False, max_retries: int = 3) -> str:
    """
    Gemini API로부터 응답 받기 (개선된 버전)
    """
    global model, chat_session, READY, REQUEST_COUNT, SUCCESSFUL_REQUESTS, FAILED_REQUESTS, LAST_REQUEST_TIME
    
    REQUEST_COUNT += 1
    LAST_REQUEST_TIME = time.time()
    
    # 초기화 확인
    if not READY or model is None:
        logger.warning("Gemini가 준비되지 않음, 재초기화 시도")
        if not initialize_gemini():
            FAILED_REQUESTS += 1
            return "[오류] Gemini가 준비되지 않았습니다. API 키와 네트워크 연결을 확인해주세요."
    
    if not prompt or not prompt.strip():
        FAILED_REQUESTS += 1
        return "[오류] 입력 프롬프트가 비어있습니다."
    
    # 프롬프트 길이 제한 확인
    if len(prompt) > 30000:  # 약 30KB 제한
        logger.warning(f"프롬프트가 너무 깁니다 ({len(prompt)} 문자). 자르기 진행...")
        prompt = prompt[:30000] + "\n\n[프롬프트가 길어서 일부 생략됨]"
    
    # 응답 시도
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"🤖 Gemini 요청 (시도 {attempt + 1}/{max_retries + 1}): {prompt[:100]}...")
            start_time = time.time()
            
            if use_chat_session and chat_session:
                # 채팅 세션 사용 (컨텍스트 유지)
                response = chat_session.send_message(prompt)
            else:
                # 일반 생성 (매번 새로운 컨텍스트)
                response = model.generate_content(prompt)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response and response.text:
                result = response.text.strip()
                
                # 응답 품질 검증
                if len(result) < 10:
                    logger.warning(f"응답이 너무 짧습니다: {result}")
                
                SUCCESSFUL_REQUESTS += 1
                logger.info(f"✅ Gemini 응답 성공 (시도 {attempt + 1}, {response_time:.2f}초): {result[:100]}...")
                
                return result
            else:
                raise Exception("빈 응답을 받았습니다.")
        
        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"❌ Gemini 응답 실패 (시도 {attempt + 1}): {e}")
            
            # 치명적인 오류인 경우 즉시 중단
            if "api_key" in error_msg or "permission" in error_msg or "forbidden" in error_msg:
                FAILED_REQUESTS += 1
                logger.error(f"❌ Gemini 권한 오류: {e}")
                return "[오류] API 키 권한이 없습니다. API 키를 확인해주세요."
            
            # 마지막 시도가 아니면 재시도
            if attempt < max_retries:
                wait_time = min((attempt + 1) * 2, 10)  # 최대 10초 대기
                print(f"🔄 {wait_time}초 후 재시도... ({attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            
            # 구체적인 오류 메시지 제공 (마지막 시도에서만)
            FAILED_REQUESTS += 1
            
            if "quota" in error_msg or "limit" in error_msg:
                logger.error(f"❌ Gemini 할당량 초과: {e}")
                return "[오류] API 사용량 한도를 초과했습니다. 잠시 후 다시 시도해주세요."
            elif "network" in error_msg or "connection" in error_msg:
                logger.error(f"❌ Gemini 네트워크 오류: {e}")
                return "[오류] 네트워크 연결에 문제가 있습니다. 인터넷 연결을 확인해주세요."
            elif "safety" in error_msg or "blocked" in error_msg:
                logger.error(f"❌ Gemini 안전 필터: {e}")
                return "[오류] 안전 정책에 위반되는 내용으로 판단되어 응답을 생성할 수 없습니다."
            elif "timeout" in error_msg:
                logger.error(f"❌ Gemini 응답 시간 초과: {e}")
                return "[오류] 응답 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
            else:
                logger.error(f"❌ Gemini 일반 오류: {e}")
                return f"[오류] Gemini 응답 실패: 서버에 일시적인 문제가 있을 수 있습니다. 잠시 후 다시 시도해주세요. (상세: {str(e)[:100]})"
    
    FAILED_REQUESTS += 1
    return "[오류] 최대 재시도 횟수를 초과했습니다."

def test_gemini_connection() -> bool:
    """Gemini API 연결 테스트 (개선된 버전)"""
    try:
        test_prompts = [
            "안녕하세요. 간단한 테스트입니다. '테스트 성공'이라고 답변해주세요.",
            "PCB는 무엇의 약자인가요? 간단히 답변해주세요.",
            "1+1은 얼마인가요?"
        ]
        
        success_count = 0
        
        for i, test_prompt in enumerate(test_prompts, 1):
            print(f"🧪 연결 테스트 {i}/{len(test_prompts)}: {test_prompt[:30]}...")
            
            response = get_gemini_response(test_prompt)
            
            if not response.startswith("[오류]"):
                print(f"✅ 테스트 {i} 성공: {response[:50]}...")
                success_count += 1
            else:
                print(f"❌ 테스트 {i} 실패: {response}")
        
        success_rate = success_count / len(test_prompts)
        
        if success_rate >= 0.8:  # 80% 이상 성공
            print(f"✅ Gemini 연결 테스트 성공 (성공률: {success_rate*100:.1f}%)")
            return True
        else:
            print(f"❌ Gemini 연결 테스트 실패 (성공률: {success_rate*100:.1f}%)")
            return False
            
    except Exception as e:
        print(f"❌ Gemini 테스트 중 오류: {e}")
        return False

def reset_chat_session():
    """채팅 세션 재설정"""
    global chat_session, model
    try:
        if model:
            chat_session = model.start_chat()
            print("🔄 채팅 세션이 재설정되었습니다.")
            return True
    except Exception as e:
        print(f"❌ 채팅 세션 재설정 실패: {e}")
        return False

def get_api_status() -> dict:
    """API 상태 정보 반환 (개선된 버전)"""
    global LAST_REQUEST_TIME
    
    last_request_formatted = None
    if LAST_REQUEST_TIME:
        last_request_formatted = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(LAST_REQUEST_TIME))
    
    return {
        "ready": READY,
        "api_key_set": bool(GEMINI_API_KEY),
        "api_key_length": len(GEMINI_API_KEY) if GEMINI_API_KEY else 0,
        "model_loaded": model is not None,
        "chat_session_active": chat_session is not None,
        "env_path": str(env_path),
        "env_exists": env_path.exists(),
        "initialization_attempts": INITIALIZATION_ATTEMPTS,
        "model_name": model.model_name if model else None,
        "statistics": {
            "total_requests": REQUEST_COUNT,
            "successful_requests": SUCCESSFUL_REQUESTS,
            "failed_requests": FAILED_REQUESTS,
            "success_rate": round((SUCCESSFUL_REQUESTS / REQUEST_COUNT * 100), 2) if REQUEST_COUNT > 0 else 0,
            "last_request_time": last_request_formatted
        }
    }

def get_usage_stats() -> dict:
    """사용 통계 반환"""
    global REQUEST_COUNT, SUCCESSFUL_REQUESTS, FAILED_REQUESTS, LAST_REQUEST_TIME
    
    return {
        "total_requests": REQUEST_COUNT,
        "successful_requests": SUCCESSFUL_REQUESTS,
        "failed_requests": FAILED_REQUESTS,
        "success_rate": round((SUCCESSFUL_REQUESTS / REQUEST_COUNT * 100), 2) if REQUEST_COUNT > 0 else 0,
        "last_request_time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(LAST_REQUEST_TIME)) if LAST_REQUEST_TIME else None,
        "api_health": "good" if SUCCESSFUL_REQUESTS > FAILED_REQUESTS else "poor" if REQUEST_COUNT > 0 else "unknown"
    }

def reset_statistics():
    """통계 초기화"""
    global REQUEST_COUNT, SUCCESSFUL_REQUESTS, FAILED_REQUESTS, LAST_REQUEST_TIME
    
    REQUEST_COUNT = 0
    SUCCESSFUL_REQUESTS = 0
    FAILED_REQUESTS = 0
    LAST_REQUEST_TIME = None
    
    print("📊 통계가 초기화되었습니다.")

def force_reinitialize():
    """강제 재초기화"""
    global READY, model, chat_session, INITIALIZATION_ATTEMPTS
    
    print("🔄 Gemini 강제 재초기화 시작...")
    
    READY = False
    model = None
    chat_session = None
    INITIALIZATION_ATTEMPTS = 0
    
    success = initialize_gemini()
    
    if success:
        print("✅ 강제 재초기화 성공")
    else:
        print("❌ 강제 재초기화 실패")
    
    return success

# 모듈 로드시 자동 초기화
try:
    print("🚀 Gemini 모듈 초기화 시작...")
    success = initialize_gemini()
    if success:
        print("🎉 Gemini 모듈 초기화 완료!")
    else:
        print("⚠️ Gemini 모듈 초기화 실패 - 기본 모드로 동작")
except Exception as e:
    logger.error(f"모듈 로드 중 Gemini 초기화 실패: {e}")
    print("⚠️ Gemini 모듈 로드 중 오류 발생 - 기본 모드로 동작")

if __name__ == "__main__":
    # 직접 실행시 종합 테스트 수행
    print("=" * 80)
    print("🧪 Gemini API 종합 테스트 시작...")
    print("=" * 80)
    
    # 1. 상태 확인
    print("\n1️⃣ API 상태 확인:")
    status = get_api_status()
    for key, value in status.items():
        if key == "statistics":
            continue  # 통계는 별도로 출력
        icon = "✅" if value else "❌"
        print(f"   {icon} {key}: {value}")
    
    # 통계 정보 출력
    print("\n📊 통계 정보:")
    stats = status.get("statistics", {})
    for key, value in stats.items():
        print(f"   📈 {key}: {value}")
    
    # 2. 연결 테스트
    print(f"\n2️⃣ 연결 테스트:")
    if status['ready']:
        success = test_gemini_connection()
        if success:
            print("🎉 Gemini API가 정상적으로 작동합니다!")
            
            # 3. 기능 테스트
            print(f"\n3️⃣ 기능 테스트:")
            test_questions = [
                "PCB 생산 관리에서 가장 중요한 요소는 무엇인가요?",
                "재고 관리 시스템의 핵심 기능을 설명해주세요.",
                "불량률을 줄이기 위한 방법을 알려주세요."
            ]
            
            for i, question in enumerate(test_questions, 1):
                print(f"\n질문 {i}: {question}")
                start_time = time.time()
                response = get_gemini_response(question)
                end_time = time.time()
                response_time = end_time - start_time
                
                if response.startswith("[오류]"):
                    print(f"❌ 오류: {response}")
                else:
                    print(f"✅ 답변 ({response_time:.2f}초): {response[:200]}{'...' if len(response) > 200 else ''}")
            
            # 4. 채팅 세션 테스트
            print(f"\n4️⃣ 채팅 세션 테스트:")
            chat_response1 = get_gemini_response("제 이름을 김철수라고 기억해주세요.", use_chat_session=True)
            print(f"1차 응답: {chat_response1[:100]}...")
            
            chat_response2 = get_gemini_response("제 이름이 뭐라고 했나요?", use_chat_session=True)
            print(f"2차 응답: {chat_response2[:100]}...")
            
            # 5. 성능 테스트
            print(f"\n5️⃣ 성능 테스트:")
            performance_start = time.time()
            for i in range(3):
                test_response = get_gemini_response(f"간단한 성능 테스트 {i+1}번째입니다. 'OK'라고 답변해주세요.")
                if not test_response.startswith("[오류]"):
                    print(f"   테스트 {i+1}: 성공")
                else:
                    print(f"   테스트 {i+1}: 실패")
            
            performance_end = time.time()
            performance_time = performance_end - performance_start
            print(f"   성능 테스트 완료 (총 {performance_time:.2f}초)")
            
        else:
            print("💥 Gemini API 설정을 확인해주세요.")
    else:
        print("💥 Gemini API 초기화에 실패했습니다.")
        print("\n📋 문제 해결 방법:")
        print("1. .env 파일에 GEMINI_API_KEY가 설정되어 있는지 확인")
        print("2. API 키가 유효한지 Google AI Studio에서 확인")
        print("3. 네트워크 연결 상태 확인")
        print("4. 방화벽 설정 확인")
    
    # 최종 상태 및 통계
    print(f"\n📊 최종 상태 및 통계:")
    final_status = get_api_status()
    final_stats = final_status.get("statistics", {})
    
    print(f"   - 준비 상태: {'✅' if final_status['ready'] else '❌'}")
    print(f"   - 초기화 시도 횟수: {final_status['initialization_attempts']}회")
    print(f"   - 총 요청: {final_stats.get('total_requests', 0)}회")
    print(f"   - 성공률: {final_stats.get('success_rate', 0)}%")
    print("=" * 80)