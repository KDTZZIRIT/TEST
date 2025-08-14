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
            # 🔍 데이터 추출 및 검증 강화
            pcb_id = pcb_data.get('id', 'N/A')
            pcb_name = pcb_data.get('name', 'Unknown PCB')
            
            # 🔧 데이터 추출 로직 개선 - 다양한 필드명 시도
            total_inspections = (
                pcb_data.get('totalInspections') or 
                pcb_data.get('inspectionsCompleted') or 
                pcb_data.get('total_inspections') or 
                pcb_data.get('inspections_completed') or 
                0
            )
            
            total_defects = (
                pcb_data.get('totalDefects') or 
                pcb_data.get('defect_count') or 
                pcb_data.get('total_defects') or 
                pcb_data.get('defectCount') or 
                0
            )
            
            defect_rate = pcb_data.get('defectRate', '0%')
            avg_defect_rate = pcb_data.get('avgDefectRate', 0)
            confidence = pcb_data.get('confidence', 'N/A')
            completion_rate = pcb_data.get('completionRate', 'N/A')
            quality_grade = pcb_data.get('qualityGrade', 'N/A')
            
            # 🔍 디버깅: 받은 데이터 로그 (원본 데이터 포함)
            print(f"📧 받은 PCB 데이터 (원본):")
            print(f"  - 전체 데이터: {pcb_data}")
            print(f"  - ID: {pcb_id}")
            print(f"  - 이름: {pcb_name}")
            print(f"  - totalInspections: {pcb_data.get('totalInspections')}")
            print(f"  - inspectionsCompleted: {pcb_data.get('inspectionsCompleted')}")
            print(f"  - totalDefects: {pcb_data.get('totalDefects')}")
            print(f"  - defect_count: {pcb_data.get('defect_count')}")
            
            print(f"📧 처리된 데이터:")
            print(f"  - 전체 검사: {total_inspections}")
            print(f"  - 불량 개수: {total_defects}")
            print(f"  - 불량률: {defect_rate}")
            print(f"  - 평균 불량률: {avg_defect_rate}")
            print(f"  - 신뢰도: {confidence}")
            print(f"  - 완료율: {completion_rate}")
            print(f"  - 품질 등급: {quality_grade}")
            
            # 🔧 데이터 타입 변환 및 검증
            try:
                total_inspections = int(total_inspections) if total_inspections is not None else 0
            except (ValueError, TypeError):
                total_inspections = 0
                print(f"⚠️ total_inspections 변환 실패, 기본값 0 사용")
            
            try:
                total_defects = int(total_defects) if total_defects is not None else 0
            except (ValueError, TypeError):
                total_defects = 0
                print(f"⚠️ total_defects 변환 실패, 기본값 0 사용")
            
            # 🔍 상세한 데이터 검증
            data_validation = []
            
            if total_inspections == 0:
                data_validation.append("⚠️ 전체 검사 수가 0개입니다. 데이터 누락 의심")
            elif total_inspections < 0:
                data_validation.append("⚠️ 전체 검사 수가 음수입니다. 데이터 오류 의심")
            
            if total_defects < 0:
                data_validation.append("⚠️ 불량 개수가 음수입니다. 데이터 오류 의심")
            elif total_defects > total_inspections and total_inspections > 0:
                data_validation.append("⚠️ 불량 개수가 전체 검사 수보다 많습니다. 데이터 불일치")
            
            # 불량률과 실제 데이터 일치성 검증
            if defect_rate and defect_rate != '0%':
                try:
                    calculated_rate = (total_defects / total_inspections * 100) if total_inspections > 0 else 0
                    received_rate = float(defect_rate.replace('%', ''))
                    if abs(calculated_rate - received_rate) > 1.0:  # 1% 오차 허용
                        data_validation.append(f"⚠️ 불량률 불일치: 계산값 {calculated_rate:.1f}% vs 받은값 {received_rate}%")
                except ValueError:
                    data_validation.append("⚠️ 불량률 형식이 올바르지 않습니다")
            
            if not pcb_name or pcb_name == 'Unknown PCB':
                data_validation.append("⚠️ PCB 이름이 제대로 설정되지 않았습니다")
            
            # 🔧 데이터 품질 평가 개선
            data_quality = "좋음"
            if len(data_validation) > 0:
                data_quality = "주의 필요"
            if total_inspections == 0:
                data_quality = "심각한 문제"
            
            print(f"🔍 데이터 검증 결과:")
            print(f"  - 품질 등급: {data_quality}")
            print(f"  - 검증 이슈: {len(data_validation)}개")
            if data_validation:
                for issue in data_validation:
                    print(f"    - {issue}")
            
            # 🔧 LLM 프롬프트 구성 개선 - 데이터 품질에 따른 동적 조정
            llm_prompt = f"""
다음 PCB 불량 정보를 바탕으로 담당자에게 보낼 전문적이고 실용적인 이메일 보고서를 작성해주세요.

📋 PCB 상세 정보:
- PCB ID: {pcb_id}
- PCB 이름: {pcb_name}
- 전체 검사 PCB 기판 개수: {total_inspections}개
- 불량 PCB 기판 개수: {total_defects}개
- 불량률: {defect_rate}
- 평균 불량률: {avg_defect_rate}%
- 신뢰도: {confidence}%

📊 품질 지표 분석:
- 양품률: {100 - float(defect_rate.replace('%', '')) if defect_rate and defect_rate != '0%' else 'N/A'}%
- 검사 완료율: {completion_rate}
- 품질 등급: {quality_grade}

🔍 데이터 품질 상태:
- 데이터 품질: {data_quality}
- 검증 결과: {'; '.join(data_validation) if data_validation else '모든 데이터 정상'}

📧 발송 대상: {to_email}

요구사항:
1. **데이터 품질 우선 평가**: 제공된 데이터의 신뢰성과 정확성을 먼저 평가하고, 문제가 있는 경우 이를 명시
2. **전체 검사 대비 불량 개수 분석**: 검사 수량이 0개인 경우 이를 명확히 지적하고, 정확한 데이터 확보의 필요성 강조
3. **신뢰도 기반 데이터 정확성 평가**: 데이터 품질 상태를 고려한 신뢰도 평가
4. **불량률의 심각성과 긴급성**: 데이터가 유효한 경우에만 불량률 분석, 데이터 문제 시 우선순위 조정
5. **비즈니스 임팩트**: 데이터 품질에 따른 임팩트 분석의 한계점 명시
6. **품질 개선 방안**: 데이터 문제 해결을 최우선으로 하는 개선 방안 제시
7. **담당자 조치사항**: 데이터 검증부터 시작하는 단계별 조치사항 명시
8. **전문적이면서도 이해하기 쉬운 톤**: 데이터 문제를 명확하게 전달
9. **한국어로 작성**: 한국어로 작성
10. **이메일 형식**: 이메일 형식에 맞게 작성

다음 형식으로 작성해주세요:

제목: {f'[긴급] {pcb_name} 데이터 품질 문제 - 즉시 조치 필요' if data_quality == '심각한 문제' else f'[주의] {pcb_name} 불량률 {defect_rate} - 데이터 검증 필요' if data_quality == '주의 필요' else f'[정상] {pcb_name} 불량률 {defect_rate} ({total_defects}개/총 {total_inspections}개)'}

본문:

[데이터 품질 상태 및 검증 결과]
- 데이터 품질 등급: {data_quality}
- 검증 결과: {'; '.join(data_validation) if data_validation else '모든 데이터 정상'}
- 데이터 신뢰성 평가

[검사 현황 및 불량 분석]
- 전체 검사 현황: {total_inspections}개
- 불량 개수: {total_defects}개
- 불량률: {defect_rate}
- 데이터 일관성 검증 결과

[품질 지표 분석]
- 양품률: {100 - float(defect_rate.replace('%', '')) if defect_rate and defect_rate != '0%' else 'N/A'}%
- 품질 등급: {quality_grade}
- 데이터 품질에 따른 분석 한계점

[우선순위별 조치사항]
- **최우선 (즉시)**: 데이터 품질 문제 해결
- **고우선 (1-2일)**: 정확한 검사 데이터 확보
- **중간 (1주)**: 불량률 재산출 및 분석
- **장기 (1개월)**: 품질 개선 계획 수립

결론:
[데이터 품질 상태와 우선 조치사항]

다음 조치사항:
[담당자가 취해야 할 구체적인 액션 아이템들 (우선순위별)]

품질 개선 목표:
[데이터 품질 개선부터 시작하는 단계별 목표]
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
                # 🔧 LLM 실패 시 기본 템플릿 사용 (데이터 품질 고려)
                if data_quality == "심각한 문제":
                    email_content = (
                        f"🚨 [긴급] {pcb_name} 데이터 품질 문제 보고서\n\n"
                        f"PCB ID: {pcb_id}\n"
                        f"PCB 이름: {pcb_name}\n"
                        f"데이터 품질: {data_quality}\n\n"
                        f"⚠️ 주요 문제점:\n"
                        f"{chr(10).join(data_validation)}\n\n"
                        f"🔍 즉시 조치 필요사항:\n"
                        f"1. 생산 및 검사 현황 재확인\n"
                        f"2. 데이터 시스템 점검\n"
                        f"3. 정확한 불량률 재산출\n\n"
                        f"현재 제공된 데이터로는 신뢰할 수 있는 분석이 불가능합니다. "
                        f"즉시 데이터 검증 및 수정이 필요합니다."
                    )
                    subject = f"[긴급] {pcb_name} 데이터 품질 문제 - 즉시 조치 필요"
                elif data_quality == "주의 필요":
                    email_content = (
                        f"⚠️ [주의] {pcb_name} 데이터 검증 필요 보고서\n\n"
                        f"PCB ID: {pcb_id}\n"
                        f"PCB 이름: {pcb_name}\n"
                        f"전체 검사: {total_inspections}개\n"
                        f"불량 개수: {total_defects}개\n"
                        f"불량률: {defect_rate}\n"
                        f"데이터 품질: {data_quality}\n\n"
                        f"🔍 데이터 검증 이슈:\n"
                        f"{chr(10).join(data_validation)}\n\n"
                        f"📊 현재 분석 결과:\n"
                        f"• 불량률: {defect_rate}\n"
                        f"• 평균 불량률: {avg_defect_rate}%\n"
                        f"• 품질 등급: {quality_grade}\n\n"
                        f"💡 권장 조치사항:\n"
                        f"1. 데이터 검증 및 수정\n"
                        f"2. 불량률 재산출\n"
                        f"3. 품질 개선 방안 수립\n\n"
                        f"데이터 품질 개선 후 정확한 분석이 가능합니다."
                    )
                    subject = f"[주의] {pcb_name} 데이터 검증 필요 - {defect_rate}"
                else:
                    email_content = (
                        f"📊 {pcb_name} PCB 불량 정보 보고서\n\n"
                        f"PCB ID: {pcb_id}\n"
                        f"PCB 이름: {pcb_name}\n"
                        f"전체 검사: {total_inspections}개\n"
                        f"불량 개수: {total_defects}개\n"
                        f"불량률: {defect_rate}\n"
                        f"평균 불량률: {avg_defect_rate}%\n"
                        f"데이터 품질: {data_quality}\n"
                        f"품질 등급: {quality_grade}\n\n"
                        f"📈 분석 결과:\n"
                        f"• 현재 불량률: {defect_rate}\n"
                        f"• 평균 대비: {avg_defect_rate}%\n"
                        f"• 검사 완료율: {completion_rate}%\n\n"
                        f"💡 품질 개선 방안:\n"
                        f"1. 불량 원인 분석\n"
                        f"2. 공정 개선\n"
                        f"3. 품질 모니터링 강화\n\n"
                        f"전체적으로 {data_quality} 수준의 데이터 품질을 보이고 있습니다."
                    )
                    subject = f"{pcb_name} PCB 불량 정보 - {defect_rate}"
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
10. 굵은 글씨와 강조는 금지
11. *는 사용하지 않음

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
                "ai_generated": True,
                "data_quality": data_quality if 'data_quality' in locals() else "N/A",
                "data_validation": data_validation if 'data_validation' in locals() else [],
                "processed_data": {
                    "total_inspections": total_inspections if 'total_inspections' in locals() else "N/A",
                    "total_defects": total_defects if 'total_defects' in locals() else "N/A",
                    "defect_rate": defect_rate if 'defect_rate' in locals() else "N/A",
                    "pcb_name": pcb_name if 'pcb_name' in locals() else "N/A"
                }
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
                "ai_generated": True,
                "data_quality": data_quality if 'data_quality' in locals() else "N/A",
                "data_validation": data_validation if 'data_validation' in locals() else [],
                "processed_data": {
                    "total_inspections": total_inspections if 'total_inspections' in locals() else "N/A",
                    "total_defects": total_defects if 'total_defects' in locals() else "N/A",
                    "defect_rate": defect_rate if 'defect_rate' in locals() else "N/A",
                    "pcb_name": pcb_name if 'pcb_name' in locals() else "N/A"
                }
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
                "ai_generated": True,
                "data_quality": data_quality if 'data_quality' in locals() else "N/A",
                "data_validation": data_validation if 'data_validation' in locals() else [],
                "processed_data": {
                    "total_inspections": total_inspections if 'total_inspections' in locals() else "N/A",
                    "total_defects": total_defects if 'total_defects' in locals() else "N/A",
                    "defect_rate": defect_rate if 'defect_rate' in locals() else "N/A",
                    "pcb_name": pcb_name if 'pcb_name' in locals() else "N/A"
                }
            })

    except Exception as e:
        print("Email sending error:", str(e))
        return jsonify({
            "error": "이메일 발송 중 오류가 발생했습니다.",
            "details": str(e)
        }), 500
