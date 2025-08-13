from flask import Blueprint, request, jsonify
import os
import boto3
from dotenv import load_dotenv
from gemini_handler import get_gemini_response

# .env 파일 로드 (있는 경우)
load_dotenv()

email_bp = Blueprint("email", __name__)

# 환경변수에서 AWS 설정 불러오기
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
VERIFIED_EMAIL = os.getenv("AWS_SES_VERIFIED_EMAIL", "bigdata054@gmail.com")

# 환경변수 상태 출력 (디버깅용)
print(f"AWS_ACCESS_KEY_ID: {'설정됨' if AWS_ACCESS_KEY_ID else '설정되지 않음'}")
print(f"AWS_SECRET_ACCESS_KEY: {'설정됨' if AWS_SECRET_ACCESS_KEY else '설정되지 않음'}")
print(f"AWS_REGION: {AWS_REGION}")
print(f"VERIFIED_EMAIL: {VERIFIED_EMAIL}")

# SES 클라이언트 생성 (실제 발송 모드)
ses_client = None
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY and AWS_REGION:
    try:
        ses_client = boto3.client(
            "ses",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        print("✅ AWS SES 클라이언트 생성 성공")
    except Exception as e:
        print(f"❌ AWS SES 클라이언트 생성 실패: {e}")
        ses_client = None
else:
    print("⚠️ AWS SES 자격증명이 설정되지 않았습니다")

@email_bp.route("/send-email", methods=["POST"])
def send_email():
    try:
        data = request.get_json()
        pcb_data = data.get("pcbData", None)

        to_email = "bigdata5us@gmail.com"  # 고정 수신 이메일

        # LLM을 사용하여 이메일 본문 생성
        if pcb_data:
            # LLM 프롬프트 구성
            llm_prompt = f"""
다음 PCB 불량 정보를 바탕으로 담당자에게 보낼 전문적이고 실용적인 이메일 보고서를 작성해주세요.

📋 PCB 상세 정보:
- PCB ID: {pcb_data.get('id')}
- PCB 이름: {pcb_data.get('name')}
- 전체 검사 PCB 기판 개수: {pcb_data.get('totalInspections', 'N/A')}개
- 불량 PCB 기판 개수: {pcb_data.get('totalDefects')}개
- 불량률: {pcb_data.get('defectRate')}
- 평균 불량률: {pcb_data.get('avgDefectRate')}%
- 신뢰도: {pcb_data.get('confidence', 'N/A')}%

📊 품질 지표 분석:
- 양품률: {100 - float(pcb_data.get('defectRate', '0').replace('%', '')) if pcb_data.get('defectRate') else 'N/A'}%
- 검사 완료율: {pcb_data.get('completionRate', 'N/A')}%
- 품질 등급: {pcb_data.get('qualityGrade', 'N/A')}

📧 발송 대상: {to_email}

요구사항:
1. 전체 검사 대비 불량 개수의 비율과 절대적 수치를 모두 고려한 분석
2. 신뢰도를 고려한 데이터의 정확성 평가
3. 불량률의 심각성과 긴급성을 정량적으로 분석
4. 비즈니스 임팩트를 구체적인 수치로 계산 (손실 금액, 생산 지연 등)
5. 품질 개선을 위한 구체적이고 실행 가능한 방안 제시
6. 담당자가 취해야 할 즉시 조치사항과 장기적 개선 계획 명시
7. 전문적이면서도 이해하기 쉬운 톤으로 작성
8. 한국어로 작성
9. 이메일 형식에 맞게 작성

다음 형식으로 작성해주세요:
제목: [긴급] [PCB 이름] 불량률 {pcb_data.get('defectRate')} ({pcb_data.get('totalDefects')}개/총 {pcb_data.get('totalInspections', 'N/A')}개) - 즉시 조치 필요

본문:
[검사 현황 및 불량 분석]
- 전체 검사 현황
- 불량 개수와 비율 분석
- 신뢰도 기반 데이터 품질 평가

[품질 지표 분석]
- 양품률 및 품질 등급
- 업계 평균 대비 성과
- 주요 불량 유형 분석

[비즈니스 임팩트 분석]
- 생산성 손실 추정
- 비용 영향 분석
- 고객 만족도 영향

[구체적인 개선 방안]
- 단기 조치사항 (1-2주)
- 중기 개선 계획 (1-3개월)
- 장기 품질 관리 전략 (3-6개월)

결론:
[핵심 요약 및 우선순위]

다음 조치사항:
[담당자가 취해야 할 구체적인 액션 아이템들 (우선순위별)]

품질 개선 목표:
[구체적인 목표 수치와 달성 기간]
"""
            
            try:
                # LLM으로 이메일 내용 생성
                llm_response = get_gemini_response(llm_prompt)
                
                # LLM 응답이 오류인 경우 기본 템플릿 사용
                if llm_response.startswith("[오류]") or llm_response.startswith("[❌]"):
                    raise Exception("LLM 응답 오류")
                
                # LLM 응답에서 제목과 본문 분리
                lines = llm_response.strip().split('\n')
                subject = ""
                email_content = ""
                
                for line in lines:
                    if line.startswith("제목:") or line.startswith("제목 :"):
                        subject = line.replace("제목:", "").replace("제목 :", "").strip()
                    else:
                        email_content += line + "\n"
                
                # 제목이 없으면 기본 제목 사용
                if not subject:
                    subject = f"{pcb_data.get('name')} PCB 불량 분석 보고서"
                
                # 본문이 없으면 기본 본문 사용
                if not email_content.strip():
                    email_content = llm_response
                    
            except Exception as llm_error:
                print(f"LLM 처리 오류: {llm_error}")
                # LLM 실패 시 기본 템플릿 사용
                email_content = (
                    f"PCB 불량 정보 보고서\n\n"
                    f"PCB ID: {pcb_data.get('id')}\n"
                    f"PCB 이름: {pcb_data.get('name')}\n"
                    f"불량률: {pcb_data.get('defectRate')}\n"
                    f"총 불량품: {pcb_data.get('totalDefects')}개\n"
                    f"평균 불량률: {pcb_data.get('avgDefectRate')}%\n\n"
                    f"분석: 현재 불량률이 {pcb_data.get('avgDefectRate')}%로 나타나고 있습니다. "
                    f"품질 개선을 위한 추가 분석이 필요합니다."
                )
                subject = f"{pcb_data.get('name')} PCB 불량 정보"
        else:
            # 전체 대시보드 보고서
            llm_prompt = f"""
PCB 불량 관리 대시보드에 대한 담당자용 종합 보고서를 작성해주세요.

📧 발송 대상: {to_email}

요구사항:
1. 담당자 관점에서 전체 시스템 현황을 한눈에 파악할 수 있도록 작성
2. 주요 불량 이슈와 우선순위 제시
3. 비즈니스 임팩트와 손실 분석
4. 구체적인 개선 방안과 실행 계획 제시
5. 담당자가 취해야 할 전략적 조치사항 명시
6. KPI 개선 목표와 달성 방안
7. 전문적이면서도 실용적인 톤으로 작성
8. 한국어로 작성
9. 이메일 형식에 맞게 작성

다음 형식으로 작성해주세요:
제목: [월간 보고서] PCB 불량 관리 시스템 종합 분석 - 담당자용

본문:
[전체 시스템 현황 및 주요 지표]

[주요 불량 이슈 및 우선순위]

[비즈니스 임팩트 분석]

[전략적 개선 방안]

결론:
[핵심 요약 및 권장사항]

다음 조치사항:
[담당자가 취해야 할 전략적 액션 아이템들]

KPI 개선 목표:
[구체적인 목표 수치와 달성 방안]
"""
            
            try:
                llm_response = get_gemini_response(llm_prompt)
                
                if llm_response.startswith("[오류]") or llm_response.startswith("[❌]"):
                    raise Exception("LLM 응답 오류")
                
                lines = llm_response.strip().split('\n')
                subject = ""
                email_content = ""
                
                for line in lines:
                    if line.startswith("제목:") or line.startswith("제목 :"):
                        subject = line.replace("제목:", "").replace("제목 :", "").strip()
                    else:
                        email_content += line + "\n"
                
                if not subject:
                    subject = "PCB 불량 관리 시스템 종합 보고서"
                if not email_content.strip():
                    email_content = llm_response
                    
            except Exception as llm_error:
                print(f"LLM 처리 오류: {llm_error}")
                email_content = "PCB 불량 관리 대시보드 보고서\n\n현재 시스템의 불량 관리 현황을 종합적으로 분석한 보고서입니다."
                subject = "PCB 불량 관리 보고서"

        # AWS SES 자격증명 없으면 테스트 모드
        if not ses_client:
            print("AWS SES 자격 증명이 없습니다. 테스트 모드로 실행됩니다.")
            return jsonify({
                "message": "✅ 테스트 모드: AI 분석 이메일 발송 성공!",
                "to": to_email,
                "subject": subject,
                "content": email_content,
                "note": "실제 이메일 발송을 위해서는 AWS SES 설정이 필요합니다.",
                "ai_generated": True
            })

        # 실제 이메일 발송
        try:
            response = ses_client.send_email(
                Source=VERIFIED_EMAIL,
                Destination={
                    "ToAddresses": [to_email]
                },
                Message={
                    "Subject": {
                        "Data": subject,
                        "Charset": "UTF-8"
                    },
                    "Body": {
                        "Text": {
                            "Data": email_content,
                            "Charset": "UTF-8"
                        }
                    }
                }
            )
            
            print(f"✅ 실제 이메일 발송 성공: {response['MessageId']}")
            return jsonify({
                "message": "✅ AI 분석 이메일 발송 성공",
                "messageId": response["MessageId"],
                "to": to_email,
                "subject": subject,
                "content": email_content,
                "pcbData": pcb_data,
                "ai_generated": True
            })
            
        except Exception as ses_error:
            print(f"❌ AWS SES 이메일 발송 실패: {ses_error}")
            # SES 실패 시 테스트 모드로 폴백
            return jsonify({
                "message": "⚠️ AWS SES 오류로 테스트 모드로 실행됩니다",
                "to": to_email,
                "subject": subject,
                "content": email_content,
                "note": f"AWS SES 오류: {str(ses_error)}",
                "ai_generated": True
            })

    except Exception as e:
        print("Email sending error:", str(e))
        return jsonify({
            "error": "이메일 발송 중 오류가 발생했습니다.",
            "details": str(e)
        }), 500
