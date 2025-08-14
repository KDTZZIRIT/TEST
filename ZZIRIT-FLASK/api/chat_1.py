from flask import Blueprint, request, jsonify
import re
from gemini_handler import get_gemini_response

chat1_bp = Blueprint("chat1", __name__)

# PCB 관련 일반적인 정보 (DB 접근 없이 제공할 수 있는 정보)
PCB_INFO = {
    "components": {
        "resistor": "저항은 전류의 흐름을 제한하는 수동 소자입니다. 단위는 옴(Ω)입니다.",
        "capacitor": "커패시터는 전기 에너지를 저장하는 수동 소자입니다. 단위는 패럿(F)입니다.",
        "inductor": "인덕터는 자기 에너지를 저장하는 수동 소자입니다. 단위는 헨리(H)입니다.",
        "diode": "다이오드는 한 방향으로만 전류를 흘리는 반도체 소자입니다.",
        "ic": "IC(집적회로)는 여러 전자 부품이 하나의 칩에 집적된 소자입니다."
    },
    "sizes": {
        "0402": "0.4mm × 0.2mm 크기의 소형 SMD 패키지",
        "0604": "0.6mm × 0.4mm 크기의 SMD 패키지",
        "1008": "1.0mm × 0.8mm 크기의 SMD 패키지",
        "2015": "2.0mm × 1.5mm 크기의 SMD 패키지",
        "2520": "2.5mm × 2.0mm 크기의 SMD 패키지"
    }
}

def get_service_info(query_type):
    """서비스 관련 정보 제공"""
    service_info = {
        "login": """
🔐 **로그인 방법**
1. 우측 상단 '로그인' 버튼 클릭
2. 이메일과 비밀번호 입력
3. 로그인 완료 후 모든 기능 이용 가능

✨ **로그인 후 이용 가능한 기능:**
- 실시간 재고 조회
- 부품 상세 정보 검색
- 재고 관리 대시보드
- 부품 주문 및 관리
- 상세 분석 리포트
        """,
        
        "signup": """
📝 **회원가입 방법**
1. 우측 상단 '회원가입' 버튼 클릭
2. 이메일, 비밀번호, 이름 입력
3. 약관 동의 후 회원가입 완료
4. 바로 로그인하여 서비스 이용 시작

🎯 **회원가입 혜택:**
- 무료 재고 관리 시스템 이용
- 실시간 부품 정보 조회
- 맞춤형 재고 알림 서비스
        """,
        
        "features": """
🚀 **PCB-Manager 주요 기능**

📊 **재고 관리**
- 실시간 부품 재고 현황
- 최소 재고량 알림
- 자동 발주 제안

🔍 **부품 검색**
- 부품번호로 정확한 정보 조회
- 카테고리별 부품 분류
- 제조사별 부품 검색

📈 **분석 대시보드**
- 재고 트렌드 분석
- 사용량 통계
- 비용 최적화 제안

🔔 **알림 서비스**
- 재고 부족 알림
- 신제품 입고 알림
- 가격 변동 알림
        """,
        
        "help": """
❓ **도움이 필요하신가요?**

💬 **지금 할 수 있는 것:**
- PCB 부품에 대한 일반적인 질문
- 서비스 기능 안내
- 로그인/회원가입 방법 안내

🔒 **로그인 후 가능한 것:**
- 실제 재고 데이터 조회
- 부품 상세 정보 검색
- 재고 관리 기능 이용

📞 **문의사항:**
- 이메일: support@pcb-manager.com
- 전화: 02-1234-5678
        """,
        
        "about": """
🏢 **PCB-Manager 소개**

PCB-Manager는 전자 부품 재고 관리를 위한 스마트 솔루션입니다.

🎯 **우리의 미션**
전자 제조업체의 효율적인 부품 관리와 비용 절감을 통해 
더 나은 제품 개발에 집중할 수 있도록 돕습니다.

✨ **핵심 가치**
- 정확한 데이터 관리
- 실시간 정보 제공  
- 사용자 친화적 인터페이스
- 24/7 안정적인 서비스

👥 **대상 고객**
- 전자 제품 제조업체
- PCB 설계 엔지니어
- 부품 구매 담당자
- 재고 관리자
        """
    }
    return service_info.get(query_type, "")

def analyze_user_intent(user_input):
    """사용자 의도 분석"""
    input_lower = user_input.lower()
    
    # 로그인 관련
    if any(keyword in input_lower for keyword in ["로그인", "login", "계정", "접속", "로그인하기"]):
        return "login"
    
    # 회원가입 관련
    if any(keyword in input_lower for keyword in ["회원가입", "signup", "가입", "계정생성", "등록", "회원가입하기"]):
        return "signup"
    
    # 기능 안내
    if any(keyword in input_lower for keyword in ["기능", "특징", "feature", "서비스", "뭐", "할수있", "가능", "기능소개"]):
        return "features"
    
    # 도움말
    if any(keyword in input_lower for keyword in ["도움", "help", "어떻게", "방법", "문의", "문의사항"]):
        return "help"
    
    # 서비스 소개
    if any(keyword in input_lower for keyword in ["소개", "about", "회사", "pcb-manager", "무엇", "소개해줘"]):
        return "about"
    
    # PCB 부품 관련
    if any(keyword in input_lower for keyword in ["저항", "resistor", "커패시터", "capacitor", "인덕터", "inductor", "다이오드", "diode", "ic", "부품", "부품소개"]):
        return "pcb_info"
    
    # 사이즈 관련
    if any(keyword in input_lower for keyword in ["0402", "0604", "1008", "2015", "2520", "사이즈", "크기"]):
        return "size_info"
    
    return "general"

def get_pcb_component_info(user_input):
    """PCB 부품 관련 일반 정보 제공"""
    input_lower = user_input.lower()
    
    for component, description in PCB_INFO["components"].items():
        if component in input_lower or (component == "resistor" and "저항" in input_lower):
            return f"📱 **{component.upper()}**\n{description}"
    
    for size, description in PCB_INFO["sizes"].items():
        if size in input_lower:
            return f"📏 **{size} 패키지**\n{description}"
    
    return """
🔧 **PCB 부품 기본 정보**

**주요 부품 종류:**
• 저항 (Resistor): 전류 제한
• 커패시터 (Capacitor): 전기 에너지 저장  
• 인덕터 (Inductor): 자기 에너지 저장
• 다이오드 (Diode): 단방향 전류 흐름
• IC (Integrated Circuit): 집적회로

**일반적인 SMD 패키지:**
• 0402: 0.4mm × 0.2mm
• 0604: 0.6mm × 0.4mm  
• 1008: 1.0mm × 0.8mm
• 2015: 2.0mm × 1.5mm
• 2520: 2.5mm × 2.0mm

💡 **더 자세한 재고 정보가 필요하시면 로그인해주세요!**
    """

def create_enhanced_prompt(user_input, intent):
    """Gemini에게 보낼 향상된 프롬프트 생성"""
    
    base_context = """
당신은 PCB-Manager 서비스의 친절한 AI 어시스턴트입니다.

주요 역할:
1. PCB 부품에 대한 일반적인 정보 제공
2. 서비스 이용 방법 안내 
3. 로그인/회원가입 유도 (상세 정보 조회시)
4. 친근하고 전문적인 답변

제약사항:
- 실제 재고 데이터는 제공하지 않음 (로그인 필요)
- 구체적인 부품 가격이나 재고량은 답변하지 않음
- 로그인 후 이용 가능함을 안내

답변 스타일:
- 친근하고 도움이 되는 톤
- 이모지 적절히 사용
- 간결하면서도 정보가 풍부한 답변
- 필요시 로그인 유도 메시지 포함
"""

    if intent == "general":
        enhanced_prompt = f"""
{base_context}

사용자 질문: "{user_input}"

PCB나 전자 부품 관련 질문이라면 일반적인 정보를 제공하고,
더 자세한 정보나 실제 재고 조회가 필요한 경우 로그인을 안내해주세요.

그 외의 질문이라면 PCB-Manager 서비스와 연관지어 친근하게 답변해주세요.
"""
    else:
        enhanced_prompt = f"""
{base_context}

사용자가 "{user_input}"라고 물어봤습니다.
이는 {intent} 관련 질문으로 보입니다.

해당 주제에 대해 도움이 되는 정보를 제공하되,
PCB-Manager 서비스의 장점도 자연스럽게 언급해주세요.
"""
    
    return enhanced_prompt

# ⭐ 수정된 부분: /chat1/chat 엔드포인트 사용
@chat1_bp.route("/chat1/chat", methods=["POST", "GET"])
def chat():
    try:
        data = request.get_json()
        messages = data.get("messages", [])
        
        # 최신 사용자 메시지 추출
        user_input = next(
            (msg.get("content", "") for msg in reversed(messages) 
             if msg.get("role") == "user"), 
            ""
        )
        
        if not user_input:
            return jsonify({
                "message": {
                    "role": "assistant", 
                    "content": "안녕하세요! PCB-Manager 챗봇입니다. 무엇을 도와드릴까요? 😊"
                }
            })
        
        # 사용자 의도 분석
        intent = analyze_user_intent(user_input)
        
        # 서비스 정보 제공 (로그인, 회원가입 등)
        if intent in ["login", "signup", "features", "help", "about"]:
            service_response = get_service_info(intent)
            if service_response:
                return jsonify({
                    "message": {
                        "role": "assistant",
                        "content": service_response
                    }
                })
        
        # PCB 부품 정보 제공
        elif intent in ["pcb_info", "size_info"]:
            pcb_response = get_pcb_component_info(user_input)
            return jsonify({
                "message": {
                    "role": "assistant",
                    "content": pcb_response
                }
            })
        
        # 일반적인 질문은 Gemini에게 전달 (향상된 프롬프트 사용)
        enhanced_prompt = create_enhanced_prompt(user_input, intent)
        response = get_gemini_response(enhanced_prompt)
        
        if not response:
            response = """
죄송합니다. 현재 일시적인 오류가 발생했습니다. 😅

🔄 **다시 시도해보시거나 아래 기능을 이용해보세요:**
- "기능" 입력 → 서비스 기능 안내
- "로그인" 입력 → 로그인 방법 안내  
- "도움" 입력 → 전체 도움말 보기

💡 **PCB 부품 정보가 필요하시면:**
저항, 커패시터, 다이오드 등의 부품명을 입력해보세요!
            """
        
        return jsonify({
            "message": {
                "role": "assistant",
                "content": response
            }
        })
        
    except Exception as e:
        print(f"Chat1 API 오류: {str(e)}")
        return jsonify({
            "message": {
                "role": "assistant",
                "content": f"""
🚨 **서비스 일시 오류**

죄송합니다. 잠시 후 다시 시도해주세요.

📞 **지속적인 문제 발생시:**
- 이메일: support@pcb-manager.com
- 전화: 02-1234-5678

💡 **기본 도움말:**
"도움", "기능", "로그인", "회원가입" 등을 입력해보세요!
                """
            }
        }), 500