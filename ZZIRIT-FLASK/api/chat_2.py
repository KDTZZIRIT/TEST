from flask import Blueprint, request, jsonify
from gemini_handler import get_gemini_response, get_api_status
import json
from datetime import datetime
import asyncio
import concurrent.futures
from data_crawler import crawler
import traceback
import os

chat_bp = Blueprint('chat', __name__)

# 메뉴별 프롬프트 템플릿
PROMPT_TEMPLATES = {
    "menu1": """당신은 PCB-Manager의 생산 관리 전문 AI 어시스턴트입니다.

현재 메뉴: 생산 관리 대시보드 (Menu1)

사용 가능한 데이터:
- 총 PCB 수: {total_pcbs}개
- 예약된 검사 일정: {scheduled_inspections_count}건
- 생산 현황 및 진행률
- 긴급 알림 및 알림 트렌드

사용자의 질문에 대해 위의 데이터를 바탕으로 정확하고 도움이 되는 답변을 제공해주세요.
데이터가 없는 경우 "데이터를 확인할 수 없습니다"라고 안내해주세요.

답변 형식:
- 명확하고 간결하게
- 구체적인 수치와 현황 포함
- 필요시 권장사항 제시
- 한국어로 답변""",

    "menu2": """당신은 PCB-Manager의 검사 관리 전문 AI 어시스턴트입니다.

현재 메뉴: 검사 관리 (Menu2)

사용 가능한 데이터:
- 총 검사 수: {total_inspections}건
- 검사 완료율: {completion_rate}%
- 오늘 예정된 검사: {today_inspections}건
- 검사 대상 미리 보기 정보
- 최근 검사 결과 및 불량률

사용자의 질문에 대해 위의 데이터를 바탕으로 정확하고 도움이 되는 답변을 제공해주세요.
데이터가 없는 경우 "데이터를 확인할 수 없습니다"라고 안내해주세요.

답변 형식:
- 명확하고 간결하게
- 구체적인 수치와 현황 포함
- 필요시 권장사항 제시
- 한국어로 답변""",

    "menu3": """당신은 PCB-Manager의 불량 분석 전문 AI 어시스턴트입니다.

현재 메뉴: 불량 분석 (Menu3)

사용 가능한 데이터:
- 총 검사 수: {total_inspections}건
- 총 불량 수: {total_defects}건
- 평균 불량률: {average_defect_rate}%
- 목표 불량률: {target_defect_rate}%
- 주요 불량 유형별 통계
- 불량률이 높은 PCB 상위 3개

사용자의 질문에 대해 위의 데이터를 바탕으로 정확하고 도움이 되는 답변을 제공해주세요.
데이터가 없는 경우 "데이터를 확인할 수 없습니다"라고 안내해주세요.

답변 형식:
- 명확하고 간결하게
- 구체적인 수치와 현황 포함
- 필요시 개선 방안 제시
- 한국어로 답변""",

    "inventory": """당신은 PCB-Manager의 재고 관리 전문 AI 어시스턴트입니다.

현재 메뉴: 재고 관리 (Menu4)

사용 가능한 데이터:
- 총 부품 수: {total_items}개
- 재고 부족 부품: {low_stock_items}개
- 긴급 발주 필요: {critical_items}개
- 흡습 민감 자재: {moisture_sensitive_items}개
- 부품별 상세 정보 및 검색 인덱스

사용자의 질문에 대해 위의 데이터를 바탕으로 정확하고 도움이 되는 답변을 제공해주세요.
데이터가 없는 경우 "데이터를 확인할 수 없습니다"라고 안내해주세요.

답변 형식:
- 명확하고 간결하게
- 구체적인 수치와 현황 포함
- 필요시 발주 권장사항 제시
- 한국어로 답변""",

    "mse": """당신은 PCB-Manager의 제조 시스템 환경(MSE) 전문 AI 어시스턴트입니다.

현재 메뉴: 실시간 환경 모니터링 (MSE)

사용 가능한 데이터:

🌡️ **실시간 환경 상태 모니터링:**
- 온도: {temperature_current}℃ ({temperature_status}) - 기준: {temperature_threshold}
- 습도: {humidity_current}% ({humidity_status}) - 기준: {humidity_threshold}
- PM2.5: {pm25_current}㎍/m³ ({pm25_status}) - 기준: {pm25_threshold}
- PM10: {pm10_current}㎍/m³ ({pm10_status}) - 기준: {pm10_threshold}
- CO₂: {co2_current}ppm ({co2_status}) - 기준: {co2_threshold}

💧 **습도 민감 자재 모니터링:**
- 총 자재: {moisture_total}개
- 정상 상태: {moisture_normal}개
- 주의 상태: {moisture_warning}개
- 자재별 상세 정보 (MLCC, BGA, FPC, QFN 등)

📊 **환경 데이터 이력:**
- 최근 {history_count}개 기록
- 시간 범위: {history_time_range}
- 평균 온도: {avg_temperature}℃
- 평균 습도: {avg_humidity}%

🏭 **창고별 환경 현황:**
- A동, B동, C동 창고별 온도/습도 상태
- 창고별 보관 자재 수량

사용자의 질문에 대해 위의 데이터를 바탕으로 정확하고 도움이 되는 답변을 제공해주세요.
환경 모니터링, 습도 민감 자재 관리, 창고 환경 최적화 등에 대한 전문적인 조언을 제공해주세요.

답변 형식:
- 명확하고 간결하게
- 구체적인 수치와 현황 포함
- 환경 문제 시 즉시 대응 방안 제시
- 습도 민감 자재 보관 최적화 권장사항
- 한국어로 답변""",

    "overview": """당신은 PCB-Manager의 전체 시스템 개요 전문 AI 어시스턴트입니다.

현재 메뉴: 시스템 개요 (Overview)

사용 가능한 데이터:
- 생산 관리 현황
- 검사 관리 현황  
- 불량 분석 현황
- 재고 관리 현황
- 환경 모니터링 현황

사용자의 질문에 대해 위의 데이터를 바탕으로 정확하고 도움이 되는 답변을 제공해주세요.
전체 시스템의 종합적인 현황과 주요 이슈를 파악하여 답변해주세요.

답변 형식:
- 명확하고 간결하게
- 구체적인 수치와 현황 포함
- 필요시 종합적인 권장사항 제시
- 한국어로 답변"""
}

# 전역 executor (비동기 작업용)
executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

def run_async_in_thread(coro):
    """비동기 함수를 동기 함수에서 실행하기 위한 헬퍼 (개선된 버전)"""
    try:
        # 현재 이벤트 루프가 있는지 확인
        try:
            loop = asyncio.get_running_loop()
            # 이미 실행 중인 루프가 있으면 새 스레드에서 실행
            future = executor.submit(asyncio.run, coro)
            return future.result(timeout=45)  # 타임아웃 증가 (45초)
        except RuntimeError:
            # 실행 중인 루프가 없으면 직접 실행
            return asyncio.run(coro)
    except concurrent.futures.TimeoutError:
        print("❌ 비동기 실행 타임아웃 (45초 초과)")
        return None
    except Exception as e:
        print(f"❌ 비동기 실행 오류: {e}")
        traceback.print_exc()
        return None

def get_all_menu_data_sync():
    """모든 메뉴의 데이터를 동기 방식으로 가져오기 (개선됨)"""
    try:
        print("🚀 전체 메뉴 데이터 크롤링 시작...")
        start_time = datetime.now()
        
        # MSE 메뉴를 포함한 모든 메뉴 데이터 크롤링
        all_data = run_async_in_thread(crawler.get_all_menu_data())
        
        # MSE 메뉴가 없으면 별도로 추가
        if all_data and 'mse' not in all_data:
            print("🔍 MSE 메뉴 데이터 별도 크롤링...")
            mse_data = run_async_in_thread(crawler.crawl_mse_data())
            if mse_data:
                all_data['mse'] = mse_data
                print("✅ MSE 메뉴 데이터 추가 완료")
            else:
                print("⚠️ MSE 메뉴 데이터 크롤링 실패")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if all_data:
            print(f"✅ 전체 메뉴 데이터 크롤링 성공 (소요시간: {duration:.2f}초)")
            
            # 데이터 품질 검증
            cleaned_data = {}
            data_sources = {}
            
            for menu_id, data in all_data.items():
                if data is not None:
                    cleaned_data[menu_id] = data
                    source = data.get('data_source', 'unknown') if isinstance(data, dict) else 'unknown'
                    data_sources[menu_id] = source
                    print(f"📊 {menu_id}: 데이터 소스 = {source}")
                else:
                    print(f"⚠️ {menu_id} 데이터가 None입니다.")
            
            # 메타데이터 추가
            cleaned_data['_metadata'] = {
                'crawl_time': end_time.isoformat(),
                'duration_seconds': duration,
                'data_sources': data_sources,
                'total_menus': len(all_data),
                'successful_menus': len(cleaned_data) - 1,  # _metadata 제외
                'mse_included': 'mse' in all_data
            }
            
            return cleaned_data
        else:
            print(f"❌ 전체 메뉴 데이터 크롤링 실패 (소요시간: {duration:.2f}초)")
            return None
            
    except Exception as e:
        print(f"❌ 전체 메뉴 데이터 가져오기 오류: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_menu_data_sync(menu_id):
    """동기 방식으로 메뉴 데이터 가져오기 (개선된 버전)"""
    try:
        print(f"🚀 {menu_id} 데이터 크롤링 시작...")
        start_time = datetime.now()
        
        # MSE 메뉴 특별 처리
        if menu_id == "mse":
            print("🌡️ MSE (환경 모니터링) 메뉴 데이터 크롤링...")
            data = run_async_in_thread(crawler.crawl_mse_data())
        else:
            data = run_async_in_thread(crawler.get_menu_data(menu_id))
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if data:
            source = data.get('data_source', 'unknown') if isinstance(data, dict) else 'unknown'
            print(f"✅ {menu_id} 데이터 크롤링 성공 (소요시간: {duration:.2f}초, 소스: {source})")
            
            # MSE 메뉴 데이터 검증 및 요약 출력
            if menu_id == "mse" and isinstance(data, dict):
                env_data = data.get('environment_data', {})
                moisture_summary = data.get('moisture_materials_summary', {})
                history_summary = data.get('history_summary', {})
                
                print(f"📊 MSE 데이터 요약:")
                print(f"  - 환경 센서: 온도 {env_data.get('temperature', {}).get('current', 'N/A')}℃, 습도 {env_data.get('humidity', {}).get('current', 'N/A')}%")
                print(f"  - 습도 민감 자재: {moisture_summary.get('total_materials', 0)}개 (정상: {moisture_summary.get('normal_status', 0)}개, 주의: {moisture_summary.get('warning_status', 0)}개)")
                print(f"  - 환경 이력: {history_summary.get('total_records', 0)}개 기록")
            
            return data
        else:
            print(f"❌ {menu_id} 데이터 크롤링 실패 (소요시간: {duration:.2f}초)")
            return None
            
    except Exception as e:
        print(f"❌ {menu_id} 데이터 크롤링 오류: {e}")
        traceback.print_exc()
        return None

def search_parts_in_inventory(user_message, inventory_data):
    """인벤토리에서 부품 검색 (프론트엔드 필드명 통일)"""
    try:
        import re
        
        # 부품 상세 정보와 인덱스 가져오기
        parts_details = inventory_data.get('parts_details', [])
        part_id_index = inventory_data.get('part_id_index', {})
        product_name_index = inventory_data.get('product_name_index', {})
        
        if not parts_details:
            print("❌ 부품 상세 정보가 없습니다.")
            return None
        
        print(f"🔍 검색 시작: '{user_message}'")
        print(f"📊 검색 대상 부품 수: {len(parts_details)}개")
        print(f"📊 인덱스 정보: part_id_index={len(part_id_index)}개, product_name_index={len(product_name_index)}개")
        
        # 실제 데이터 샘플 확인 (디버깅용)
        if parts_details:
            sample = parts_details[0]
            print(f"📋 데이터 샘플: partId={sample.get('partId')}, product={sample.get('product')}")
            
            # 인덱스 샘플 확인
            if part_id_index:
                sample_keys = list(part_id_index.keys())[:3]
                print(f"📋 인덱스 샘플 키: {sample_keys}")
        
        # 사용자 메시지에서 부품 ID 패턴 추출 (CL02B121KP2NNNC 형태 포함)
        part_id_patterns = [
            r'[A-Z]{2}[0-9]{2}[A-Z][0-9]{1,3}[A-Z]{1,3}[0-9]{0,2}[A-Z]{1,4}',  # CL03C1R5CA3GNNC 형태
            r'[A-Z]{2}[0-9]{2}[A-Z][0-9]{2,4}[A-Z]{1,2}[0-9]{0,2}[A-Z]{2,4}',  # CL02B121KP2NNNC 형태
            r'[A-Z]{2}[0-9]{2}[A-Z][0-9]{1,4}[A-Z]{1,4}[0-9]{0,2}[A-Z]{1,4}',  # 더 유연한 패턴
            r'[A-Z0-9]{10,20}'  # 긴 부품 ID
        ]
        
        found_part_ids = []
        for i, pattern in enumerate(part_id_patterns):
            matches = re.findall(pattern, user_message.upper())
            if matches:
                print(f"🔍 패턴 {i+1}에서 매치: {matches}")
            found_part_ids.extend(matches)
        
        # 중복 제거 및 길이순 정렬 (긴 것부터)
        found_part_ids = list(set(found_part_ids))
        found_part_ids.sort(key=len, reverse=True)
        
        print(f"🔍 최종 추출된 부품 ID: {found_part_ids}")
        
        exact_matches = []
        similar_matches = []
        search_keywords = found_part_ids.copy()
        
        # 1단계: 정확히 일치하는 부품 찾기 (우선순위)
        for part_id in found_part_ids:
            found_exact = False
            print(f"🔎 정확 검색 중: {part_id}")
            
            # part_id_index 사용한 빠른 검색
            clean_search_id = part_id.upper().strip()
            if clean_search_id in part_id_index:
                exact_matches.append(part_id_index[clean_search_id])
                print(f"✅ 인덱스에서 정확히 일치: {part_id}")
                found_exact = True
                continue
            
            # 전체 리스트에서 정확 검색 (프론트엔드 필드명 사용)
            for stored_part in parts_details:
                # ✅ 프론트엔드 필드명으로 접근
                stored_partId = str(stored_part.get('partId', '')).upper().strip()
                stored_part_id = str(stored_part.get('part_id', '')).upper().strip()  # 하위 호환성
                
                if (clean_search_id == stored_partId or 
                    clean_search_id == stored_part_id):
                    exact_matches.append(stored_part)
                    print(f"✅ 정확히 일치: {part_id} -> {stored_partId or stored_part_id}")
                    found_exact = True
                    break
            
            if found_exact:
                break  # 정확한 매치를 찾으면 더 이상 검색하지 않음
        
        # 정확한 매치를 찾았으면 유사 검색은 하지 않음
        if exact_matches:
            print(f"✅ 정확한 매치 발견: {len(exact_matches)}개")
            return {
                'exact_matches': exact_matches,
                'similar_matches': [],  # 정확한 매치가 있으면 유사 매치는 빈 배열
                'search_keywords': search_keywords,
                'total_parts_searched': len(parts_details)
            }
        
        # 2단계: 정확한 매치가 없을 때만 유사한 부품 찾기
        print("⚠️ 정확한 매치 없음, 유사 검색 시작...")
        
        for part_id in found_part_ids:
            for stored_part in parts_details:
                # ✅ 프론트엔드 필드명으로 접근
                stored_partId = str(stored_part.get('partId', '')).upper().strip()
                stored_part_id = str(stored_part.get('part_id', '')).upper().strip()
                
                # 부분 일치 확인 (90% 이상 유사성만)
                similarity1 = calculate_similarity(part_id.upper(), stored_partId)
                similarity2 = calculate_similarity(part_id.upper(), stored_part_id)
                max_similarity = max(similarity1, similarity2)
                
                if max_similarity > 0.9:  # 90% 이상 유사해야 함
                    if stored_part not in similar_matches:
                        similar_matches.append(stored_part)
                        print(f"🔎 유사 부품 발견: {part_id} -> {stored_partId or stored_part_id} (유사도: {max_similarity:.2f})")
                        
                        if len(similar_matches) >= 5:  # 최대 5개까지만
                            break
        
        # 3단계: 키워드 검색 (부품 ID가 없거나 유사 검색 결과가 적을 때)
        if not found_part_ids or len(similar_matches) < 3:
            message_lower = user_message.lower()
            additional_keywords = []
            
            if 'capacitor' in message_lower or '커패시터' in message_lower or '캐패시터' in message_lower:
                additional_keywords.append('capacitor')
            if 'murata' in message_lower or '무라타' in message_lower:
                additional_keywords.append('murata')
            if 'samsung' in message_lower or '삼성' in message_lower:
                additional_keywords.append('samsung')
            if '흡습' in message_lower or 'moisture' in message_lower:
                additional_keywords.append('moisture')
            
            search_keywords.extend(additional_keywords)
            
            # 키워드 기반 검색 (프론트엔드 필드명 사용)
            for keyword in additional_keywords:
                for stored_part in parts_details:
                    # ✅ 프론트엔드 필드명으로 접근
                    part_type = str(stored_part.get('type', '')).lower()
                    manufacturer = str(stored_part.get('manufacturer', '')).lower()
                    moisture_absorption = stored_part.get('moistureAbsorption', False)
                    
                    if (keyword == 'capacitor' and 'capacitor' in part_type) or \
                       (keyword == 'murata' and 'murata' in manufacturer) or \
                       (keyword == 'samsung' and 'samsung' in manufacturer) or \
                       (keyword == 'moisture' and moisture_absorption):
                        
                        if stored_part not in similar_matches:
                            similar_matches.append(stored_part)
                            if len(similar_matches) >= 10:  # 최대 10개까지만
                                break
        
        # 결과 반환
        if exact_matches or similar_matches or search_keywords:
            result = {
                'exact_matches': exact_matches,
                'similar_matches': similar_matches,
                'search_keywords': search_keywords,
                'total_parts_searched': len(parts_details)
            }
            
            print(f"📊 검색 결과:")
            print(f"  - 정확 매치: {len(exact_matches)}개")
            print(f"  - 유사 매치: {len(similar_matches)}개")
            print(f"  - 검색 키워드: {search_keywords}")
            
            return result
        
        print("❌ 검색 결과 없음")
        return None
        
    except Exception as e:
        print(f"❌ 부품 검색 오류: {e}")
        import traceback
        traceback.print_exc()
        return None

def calculate_similarity(str1, str2):
    """문자열 유사도 계산 (개선된 버전)"""
    try:
        if not str1 or not str2:
            return 0.0
        
        # 길이가 너무 다르면 유사도 낮춤
        len_diff = abs(len(str1) - len(str2))
        max_len = max(len(str1), len(str2))
        
        if max_len > 0 and len_diff / max_len > 0.3:  # 30% 이상 길이 차이나면 낮은 점수
            return 0.0
        
        # 순서대로 일치하는 문자 개수
        common_chars = 0
        min_len = min(len(str1), len(str2))
        
        for i in range(min_len):
            if str1[i] == str2[i]:
                common_chars += 1
            else:
                break  # 순서가 맞지 않으면 중단
        
        # 전체 문자 일치 확인
        all_match = 0
        for i in range(min_len):
            if str1[i] == str2[i]:
                all_match += 1
        
        # 가중치 적용: 앞부분 일치를 더 중요하게
        front_weight = common_chars / min_len if min_len > 0 else 0
        total_weight = all_match / max_len if max_len > 0 else 0
        
        # 최종 유사도 (앞부분 일치 70%, 전체 일치 30%)
        similarity = front_weight * 0.7 + total_weight * 0.3
        
        return similarity
        
    except Exception as e:
        print(f"❌ 유사도 계산 오류: {e}")
        return 0.0

def get_ai_response_with_context(user_message, current_menu, context_data=None):
    """컨텍스트 데이터를 활용한 AI 응답 생성 (개선된 버전)"""
    try:
        print(f"🤖 AI 응답 생성 시작 - 메뉴: {current_menu}")
        
        # 메뉴별 프롬프트 템플릿 선택
        menu_prompt = PROMPT_TEMPLATES.get(current_menu)
        if not menu_prompt:
            print(f"⚠️ 지원하지 않는 메뉴: {current_menu}")
            return f"죄송합니다. {current_menu} 메뉴는 현재 지원하지 않습니다."
        
        # 컨텍스트 데이터에서 변수 추출 및 프롬프트 치환
        if context_data and isinstance(context_data, dict):
            print(f"📊 컨텍스트 데이터 활용 - 키: {list(context_data.keys())}")
            
            # MSE 메뉴 특별 처리
            if current_menu == "mse":
                # 환경 데이터 변수 추출
                env_data = context_data.get('environment_data', {})
                temp_data = env_data.get('temperature', {})
                humidity_data = env_data.get('humidity', {})
                pm25_data = env_data.get('pm25', {})
                pm10_data = env_data.get('pm10', {})
                co2_data = env_data.get('co2', {})
                
                # 습도 민감 자재 데이터 변수 추출
                moisture_summary = context_data.get('moisture_materials_summary', {})
                
                # 환경 이력 데이터 변수 추출
                history_summary = context_data.get('history_summary', {})
                
                # 창고 상태 데이터 변수 추출
                warehouse_status = context_data.get('warehouse_status', {})
                
                # MSE 프롬프트 변수 치환
                prompt_vars = {
                    'temperature_current': temp_data.get('current', 'N/A'),
                    'temperature_status': temp_data.get('status', 'N/A'),
                    'temperature_threshold': temp_data.get('threshold', 'N/A'),
                    'humidity_current': humidity_data.get('current', 'N/A'),
                    'humidity_status': humidity_data.get('status', 'N/A'),
                    'humidity_threshold': humidity_data.get('threshold', 'N/A'),
                    'pm25_current': pm25_data.get('current', 'N/A'),
                    'pm25_status': pm25_data.get('status', 'N/A'),
                    'pm25_threshold': pm25_data.get('threshold', 'N/A'),
                    'pm10_current': pm10_data.get('current', 'N/A'),
                    'pm10_status': pm10_data.get('status', 'N/A'),
                    'pm10_threshold': pm10_data.get('threshold', 'N/A'),
                    'co2_current': co2_data.get('current', 'N/A'),
                    'co2_status': co2_data.get('status', 'N/A'),
                    'co2_threshold': co2_data.get('threshold', 'N/A'),
                    'moisture_total': moisture_summary.get('total_materials', 0),
                    'moisture_normal': moisture_summary.get('normal_status', 0),
                    'moisture_warning': moisture_summary.get('warning_status', 0),
                    'history_count': history_summary.get('total_records', 0),
                    'history_time_range': history_summary.get('time_range', 'N/A'),
                    'avg_temperature': history_summary.get('average_temperature', 'N/A'),
                    'avg_humidity': history_summary.get('average_humidity', 'N/A')
                }
                
                # 프롬프트 변수 치환
                for var_name, var_value in prompt_vars.items():
                    menu_prompt = menu_prompt.replace(f'{{{var_name}}}', str(var_value))
                
                print(f"✅ MSE 프롬프트 변수 치환 완료")
                
            else:
                # 기존 메뉴들의 변수 치환
                prompt_vars = {
                    'total_pcbs': context_data.get('total_pcbs', 0),
                    'scheduled_inspections_count': len(context_data.get('scheduled_inspections', [])),
                    'total_inspections': context_data.get('total_inspections', 0),
                    'completion_rate': context_data.get('completion_rate', 0),
                    'today_inspections': context_data.get('today_inspections', 0),
                    'total_defects': context_data.get('total_defects', 0),
                    'average_defect_rate': context_data.get('average_defect_rate', 0),
                    'target_defect_rate': context_data.get('target_defect_rate', 0),
                    'total_items': context_data.get('total_items', 0),
                    'low_stock_items': context_data.get('low_stock_items', 0),
                    'critical_items': context_data.get('critical_items', 0),
                    'moisture_sensitive_items': context_data.get('moisture_sensitive_items', 0)
                }
                
                # 프롬프트 변수 치환
                for var_name, var_value in prompt_vars.items():
                    menu_prompt = menu_prompt.replace(f'{{{var_name}}}', str(var_value))
                
                print(f"✅ {current_menu} 프롬프트 변수 치환 완료")
        else:
            print("⚠️ 컨텍스트 데이터가 없거나 올바르지 않음")
        
        # 최종 프롬프트 구성
        final_prompt = f"""
{menu_prompt}

사용자 질문: {user_message}

위의 정보를 바탕으로 사용자의 질문에 정확하고 도움이 되는 답변을 제공해주세요.
"""
        
        print(f"📝 최종 프롬프트 길이: {len(final_prompt)}자")
        
        # Gemini API 호출
        response = get_gemini_response(final_prompt, apply_format=True)
        
        if response:
            print(f"✅ AI 응답 생성 완료 - 길이: {len(response)}자")
            return response
        else:
            print("⚠️ Gemini API 응답 없음")
            return f"죄송합니다. {current_menu} 메뉴에 대한 응답을 생성할 수 없습니다. 잠시 후 다시 시도해주세요."
            
    except Exception as e:
        print(f"❌ AI 응답 생성 오류: {e}")
        import traceback
        traceback.print_exc()
        return f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}"

def generate_fallback_response(menu_id, user_message, context_data):
    """Gemini API 실패시 기본 응답 생성 (개선된 버전)"""
    try:
        # 현재 메뉴 데이터 추출
        current_data = context_data.get(menu_id) if context_data else None
        data_source = current_data.get('data_source', 'unknown') if isinstance(current_data, dict) else 'unknown'
        
        base_response = f"안녕하세요! PCB-Manager AI입니다.\n\n'{user_message}'에 대한 답변입니다:\n\n"
        
        if menu_id == "menu1":
            if current_data:
                total_pcbs = current_data.get('total_pcbs', 0)
                completed = current_data.get('production_status', {}).get('completed', 0)
                avg_progress = current_data.get('average_progress', 0)
                efficiency = current_data.get('production_efficiency', 0)
                
                # 새로운 데이터 구조 정보 추가
                scheduled_inspections = current_data.get('scheduled_inspections', [])
                production_lines = current_data.get('production_lines', {})
                emergency_alerts = current_data.get('emergency_alerts', [])
                alert_trend = current_data.get('alert_trend', {})
                
                response = base_response + f"""📊 **PCB 생산 관리 현황** (데이터 소스: {data_source})

🏭 **총 PCB 관리 현황:**
- 전체 PCB: {total_pcbs}개
- 완료된 PCB: {completed}개
- 평균 진행률: {avg_progress}%
- 생산 효율성: {efficiency}%"""

                # 예약된 검사 일정
                if scheduled_inspections:
                    response += f"\n\n📅 **예약된 검사 일정: {len(scheduled_inspections)}건**"
                    for inspection in scheduled_inspections:  # 모든 예약된 검사 일정 표시
                        pcb_name = inspection.get('pcbName', 'Unknown')
                        insp_type = inspection.get('type', 'Unknown')
                        count = inspection.get('count', 0)
                        response += f"\n- {pcb_name}: {insp_type} {count}개"
                
                # 생산 라인 부하
                if production_lines:
                    response += f"\n\n🏭 **생산 라인 부하 상태:**"
                    for line_name, line_data in production_lines.items():
                        load = line_data.get('load', 0)
                        pcbs = line_data.get('pcbs', [])
                        response += f"\n- {line_name}: {load}% 부하 ({', '.join(pcbs[:2])})"
                
                # 긴급 알림
                if emergency_alerts:
                    response += f"\n\n🚨 **긴급 알림: {len(emergency_alerts)}건**"
                    for alert in emergency_alerts[:2]:
                        message = alert.get('message', 'Unknown')
                        severity = alert.get('severity', 'medium')
                        response += f"\n- [{severity.upper()}] {message}"
                
                # 알림 현황
                if alert_trend:
                    total_today = alert_trend.get('total_today', 0)
                    response += f"\n\n📊 **오늘 발생한 알림: {total_today}건**"
                
                response += "\n\n더 자세한 정보가 필요하시면 구체적으로 질문해주세요."
            else:
                response = base_response + "생산 관리 데이터를 확인하고 있습니다. 잠시 후 다시 시도해주세요."
            
        elif menu_id == "menu2":
            if current_data:
                total_inspections = current_data.get('total_inspections', 0)
                completion_rate = current_data.get('completion_rate', 0)
                today_inspections = current_data.get('today_inspections', 0)
                
                response = base_response + f"""🔍 **검사 관리 현황** (데이터 소스: {data_source})

🧪 **검사 현황:**
- 총 검사: {total_inspections}건
- 검사 완료율: {completion_rate}%
- 오늘 예정 검사: {today_inspections}건

더 자세한 검사 정보가 필요하시면 구체적으로 질문해주세요."""
            else:
                response = base_response + "검사 관리 데이터를 확인하고 있습니다. 잠시 후 다시 시도해주세요."
                
        elif menu_id == "menu3":
            if current_data:
                avg_rate = current_data.get('average_defect_rate', 0)
                total_defects = current_data.get('total_defects', 0)
                total_inspections = current_data.get('total_inspections', 0)
                target_rate = current_data.get('target_defect_rate', 0)
                
                response = base_response + f"""📈 **불량 분석 현황** (데이터 소스: {data_source})

📊 **불량 통계:**
- 평균 불량률: {avg_rate}%
- 목표 불량률: {target_rate}%
- 총 불량: {total_defects}개
- 총 검사: {total_inspections}건"""
                
                # 상위 불량 PCB 정보 추가
                top_pcbs = current_data.get('top_defective_pcbs', [])
                if top_pcbs:
                    response += f"\n\n🏆 **상위 불량 PCB:**"
                    for i, pcb in enumerate(top_pcbs[:3], 1):
                        pcb_name = pcb.get('pcb_name', pcb.get('pcb_id', 'Unknown'))
                        defect_rate = pcb.get('defect_rate', 0)
                        response += f"\n{i}위: {pcb_name} - 불량률 {defect_rate}%"
                
                response += "\n\n더 자세한 불량 분석이 필요하시면 구체적으로 질문해주세요."
            else:
                response = base_response + "불량 분석 데이터를 확인하고 있습니다. 잠시 후 다시 시도해주세요."
                
        elif menu_id == "inventory":
            if current_data:
                total_items = current_data.get('total_items', 0)
                low_stock = current_data.get('low_stock_items', 0)
                critical_items = current_data.get('critical_items', 0)
                total_value = current_data.get('total_value', 0)
                
                response = base_response + f"""📦 **부품 재고 현황** (데이터 소스: {data_source})

🗂️ **재고 통계:**
- 총 부품 종류: {total_items}개
- 재고 부족: {low_stock}개
- 긴급 부족: {critical_items}개"""
                
                if total_value > 0:
                    response += f"\n- 총 재고 가치: {total_value:,}원"
                
                response += "\n\n더 자세한 재고 정보가 필요하시면 구체적으로 질문해주세요."
            else:
                response = base_response + "부품 재고 데이터를 확인하고 있습니다. 잠시 후 다시 시도해주세요."
                
        elif menu_id == "mse":
            if current_data:
                env_data = current_data.get('environment_data', {})
                temp_data = env_data.get('temperature', {})
                humidity_data = env_data.get('humidity', {})
                moisture_summary = current_data.get('moisture_materials_summary', {})
                history_summary = current_data.get('history_summary', {})
                warehouse_status = current_data.get('warehouse_status', {})
                
                response = base_response + f"""🌡️ **실시간 환경 모니터링 현황** (데이터 소스: {data_source})

🌡️ **환경 센서 상태:**
- 온도: {temp_data.get('current', 'N/A')}℃ ({temp_data.get('status', 'N/A')})
- 습도: {humidity_data.get('current', 'N/A')}% ({humidity_data.get('status', 'N/A')})
- 기준값: 온도 {temp_data.get('threshold', 'N/A')}, 습도 {humidity_data.get('threshold', 'N/A')}

💧 **습도 민감 자재 모니터링:**
- 총 자재: {moisture_summary.get('total_materials', 0)}개
- 정상 상태: {moisture_summary.get('normal_status', 0)}개
- 주의 상태: {moisture_summary.get('warning_status', 0)}개

📊 **환경 데이터 이력:**
- 최근 기록: {history_summary.get('total_records', 0)}개
- 평균 온도: {history_summary.get('average_temperature', 'N/A')}℃
- 평균 습도: {history_summary.get('average_humidity', 'N/A')}%"""

                # 창고별 현황 추가
                if warehouse_status:
                    response += f"\n\n🏭 **창고별 환경 현황:**"
                    for warehouse_name, warehouse_data in warehouse_status.items():
                        temp = warehouse_data.get('temperature', 'N/A')
                        humidity = warehouse_data.get('humidity', 'N/A')
                        status = warehouse_data.get('status', 'N/A')
                        response += f"\n- {warehouse_name}: 온도 {temp}℃, 습도 {humidity}% ({status})"
                
                response += "\n\n환경 모니터링이나 습도 민감 자재 관리에 대해 더 자세한 정보가 필요하시면 구체적으로 질문해주세요."
            else:
                response = base_response + "환경 모니터링 데이터를 확인하고 있습니다. 잠시 후 다시 시도해주세요."
                
        elif menu_id == "mes":
            if current_data:
                temp = current_data.get('temperature', 0)
                humidity = current_data.get('humidity', 0)
                production_count = current_data.get('production_count', 0)
                quality_score = current_data.get('quality_score', 0)
                
                response = base_response + f"""🏭 **MES 시스템 현황** (데이터 소스: {data_source})

🌡️ **환경 모니터링:**
- 현재 온도: {temp}°C
- 현재 습도: {humidity}%

📊 **생산 현황:**
- 현재 생산량: {production_count}개
- 품질 지표: {quality_score}%

더 자세한 MES 정보가 필요하시면 구체적으로 질문해주세요."""
            else:
                response = base_response + "MES 시스템 데이터를 확인하고 있습니다. 잠시 후 다시 시도해주세요."
        else:
            response = base_response + f"현재 {menu_id} 메뉴의 정보를 확인하고 있습니다. 더 구체적인 질문을 해주시면 도움을 드리겠습니다."
            
        return response
        
    except Exception as e:
        print(f"❌ 기본 응답 생성 오류: {e}")
        return f"안녕하세요! PCB-Manager AI입니다.\n\n'{user_message}'에 대한 질문을 받았습니다. 현재 시스템을 점검 중이니 잠시 후 다시 시도해주세요.\n\n오류 정보: {str(e)}"

@chat_bp.route('/llm', methods=['POST'])
def llm_chat():
    """HTTP API 엔드포인트 (Socket.IO 대체용) - 개선된 버전"""
    try:
        print("\n" + "="*60)
        print("[📝] LLM API 호출 시작")
        print("="*60)
        
        data = request.get_json()
        if not data:
            print("[❌] 요청 데이터가 없습니다.")
            return jsonify({"error": "요청 데이터가 없습니다.", "success": False}), 400
            
        message = data.get('message')
        menu = data.get('menu')
        context = data.get('context', {})
        
        print(f"[📋] 요청 정보:")
        print(f"  - 메뉴: {menu}")
        print(f"  - 메시지: {message[:100] if message else 'None'}...")
        print(f"  - 컨텍스트: {'있음' if context else '없음'}")
        print(f"  - 요청 시간: {datetime.now().isoformat()}")
        
        if not message or not menu:
            print("[❌] 메시지 또는 메뉴 정보가 누락되었습니다.")
            return jsonify({"error": "메시지와 메뉴 정보가 필요합니다.", "success": False}), 400
        
        # 메뉴별 프롬프트 확인
        menu_mapping = {
            "overview": "menu1",
            "defects": "menu2", 
            "analytics": "menu3",
            "inventory": "inventory",
            "mse": "mse",
            "mes": "mes"
        }
        
        menu_id = menu_mapping.get(menu, menu)
        menu_prompt = PROMPT_TEMPLATES.get(menu_id)
        if not menu_prompt:
            print(f"[❌] 지원하지 않는 메뉴: {menu}")
            return jsonify({"error": f"지원하지 않는 메뉴입니다: {menu}", "success": False}), 400
        
        # Gemini API 상태 확인
        api_status = get_api_status()
        print(f"[🤖] Gemini API 상태: {api_status}")
        
        if not api_status.get('ready', False):
            print("[⚠️] Gemini API가 준비되지 않았습니다.")
            return jsonify({
                "error": "AI 시스템이 일시적으로 사용할 수 없습니다. 잠시 후 다시 시도해주세요.",
                "success": False,
                "api_status": api_status
            }), 503
        
        # 컨텍스트에 데이터가 없으면 크롤링 수행
        all_menu_data = None
        crawling_info = {"attempted": False, "success": False, "duration": 0}
        
        if not context or not context.get('allMenuData'):
            print("[📊] 실시간 데이터 크롤링 시작...")
            crawling_start = datetime.now()
            crawling_info["attempted"] = True
            
            all_menu_data = get_all_menu_data_sync()
            
            crawling_end = datetime.now()
            crawling_info["duration"] = (crawling_end - crawling_start).total_seconds()
            crawling_info["success"] = all_menu_data is not None
            
            print(f"[📊] 크롤링 완료: {crawling_info}")
        else:
            print("[📊] 기존 컨텍스트 데이터 사용")
            all_menu_data = context.get('allMenuData')
        
        # AI 응답 생성
        print(f"[🤖] AI 응답 생성 시작...")
        ai_start = datetime.now()
        
        response = get_ai_response_with_context(message, menu, all_menu_data)
        
        ai_end = datetime.now()
        ai_duration = (ai_end - ai_start).total_seconds()
        
        print(f"[✅] 응답 완료")
        print(f"  - AI 응답 시간: {ai_duration:.2f}초")
        print(f"  - 응답 길이: {len(response)}자")
        print(f"  - 응답 미리보기: {response[:100]}...")
        
        # 응답 메타데이터 구성
        metadata = {}
        if all_menu_data and isinstance(all_menu_data, dict):
            metadata = all_menu_data.get('_metadata', {})
        
        result = {
            "response": response,
            "allMenuData": all_menu_data,
            "menu": menu,
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "performance": {
                "crawling": crawling_info,
                "ai_response_time": ai_duration,
                "total_time": crawling_info["duration"] + ai_duration
            },
            "api_status": api_status,
            "data_metadata": metadata
        }
        
        return jsonify(result)
        
    except Exception as e:
        print(f"[❌ LLM API 오류]: {e}")
        traceback.print_exc()
        return jsonify({
            "error": f"서버 오류가 발생했습니다: {str(e)}",
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "api_status": get_api_status()
        }), 500

@chat_bp.route('/chat', methods=['POST'])
def chat():
    """프론트엔드 챗봇용 엔드포인트 (개선된 버전)"""
    try:
        print("\n" + "="*60)
        print("[📝] 챗봇 API 호출 시작")
        print("="*60)
        
        data = request.get_json()
        if not data:
            print("[❌] 요청 데이터가 없습니다.")
            return jsonify({"error": "요청 데이터가 없습니다.", "success": False}), 400
            
        messages = data.get('messages', [])
        
        if not messages:
            print("[❌] 메시지가 없습니다.")
            return jsonify({"error": "메시지가 필요합니다.", "success": False}), 400
        
        # 마지막 사용자 메시지 추출
        user_messages = [msg for msg in messages if msg.get('role') == 'user']
        if not user_messages:
            print("[❌] 사용자 메시지가 없습니다.")
            return jsonify({"error": "사용자 메시지가 필요합니다.", "success": False}), 400
        
        user_message = user_messages[-1]['content']
        
        print(f"[📋] 사용자 메시지: {user_message[:100]}...")
        print(f"[📋] 전체 대화 기록: {len(messages)}개 메시지")
        
        # 현재 메뉴 자동 감지 (사용자 메시지 기반)
        current_menu = "defects"  # 기본값
        
        # 메시지 내용을 기반으로 메뉴 자동 감지
        user_message_lower = user_message.lower()
        
        if any(keyword in user_message_lower for keyword in ['생산', 'pcb', '라인', '진행률', '완료']):
            current_menu = "menu1"
        elif any(keyword in user_message_lower for keyword in ['검사', 'inspection', 'aoi', '수동검사']):
            current_menu = "menu2"
        elif any(keyword in user_message_lower for keyword in ['불량', 'defect', '품질', '분석']):
            current_menu = "menu3"
        elif any(keyword in user_message_lower for keyword in ['재고', '부품', 'inventory', 'stock', '발주']):
            current_menu = "inventory"
        elif any(keyword in user_message_lower for keyword in ['환경', '온도', '습도', '센서', '모니터링', '창고', '자재']):
            current_menu = "mse"
        elif any(keyword in user_message_lower for keyword in ['mes', '시스템', '생산량']):
            current_menu = "mes"
        
        print(f"[🎯] 감지된 메뉴: {current_menu}")
        
        # 컨텍스트 데이터 크롤링
        print("[📊] 실시간 데이터 크롤링 시작...")
        crawling_start = datetime.now()
        
        all_menu_data = get_all_menu_data_sync()
        
        crawling_end = datetime.now()
        crawling_duration = (crawling_end - crawling_start).total_seconds()
        print(f"[📊] 크롤링 완료: {bool(all_menu_data)} (소요시간: {crawling_duration:.2f}초)")
        
        # AI 응답 생성
        print(f"[🤖] AI 응답 생성 시작...")
        ai_start = datetime.now()
        
        response = get_ai_response_with_context(user_message, current_menu, all_menu_data)
        
        ai_end = datetime.now()
        ai_duration = (ai_end - ai_start).total_seconds()
        
        print(f"[✅] 응답 완료 (AI 응답시간: {ai_duration:.2f}초)")
        print(f"  - 응답 길이: {len(response)}자")
        
        result = {
            "message": {
                "content": response,
                "role": "assistant"
            },
            "allMenuData": all_menu_data,
            "menu": current_menu,
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "performance": {
                "crawling_time": crawling_duration,
                "ai_response_time": ai_duration,
                "total_time": crawling_duration + ai_duration
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        print(f"[❌ 챗봇 API 오류]: {e}")
        traceback.print_exc()
        return jsonify({
            "error": f"서버 오류가 발생했습니다: {str(e)}",
            "success": False,
            "timestamp": datetime.now().isoformat()
        }), 500

@chat_bp.route('/health', methods=['GET'])
def health_check():
    """헬스 체크 엔드포인트 (개선된 버전)"""
    try:
        health_start = datetime.now()
        
        # 1. Gemini API 상태 확인
        api_status = get_api_status()
        
        # 2. 크롤러 연결 테스트
        try:
            test_data = get_menu_data_sync("overview")
            crawler_status = "working" if test_data else "limited"
            crawler_error = None
        except Exception as e:
            crawler_status = "error"
            crawler_error = str(e)
        
        # 3. 성능 테스트
        health_end = datetime.now()
        health_duration = (health_end - health_start).total_seconds()
        
        # 4. 환경 정보
        env_info = {
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            "server_time": health_end.isoformat(),
            "uptime_check": "OK"
        }
        
        return jsonify({
            "status": "healthy" if api_status.get('ready') and crawler_status != "error" else "degraded",
            "message": "LLM API 서버가 정상 작동 중입니다.",
            "timestamp": health_end.isoformat(),
            "performance": {
                "health_check_time": health_duration,
                "status": "good" if health_duration < 5.0 else "slow"
            },
            "components": {
                "gemini_api": {
                    "status": "healthy" if api_status.get('ready') else "unhealthy",
                    "details": api_status
                },
                "crawler": {
                    "status": crawler_status,
                    "error": crawler_error
                },
                "server": {
                    "status": "healthy",
                    "environment": env_info
                }
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"서버 상태 확인 중 오류: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "error_details": str(e)
        }), 500

@chat_bp.route('/test-crawler', methods=['GET'])
def test_crawler():
    """크롤러 테스트 엔드포인트 (개선된 버전)"""
    try:
        print("🧪 크롤러 종합 테스트 시작...")
        test_start = datetime.now()
        
        # 1. API 엔드포인트 테스트
        endpoint_results = crawler.test_all_endpoints()
        
        # 2. 개별 메뉴 테스트
        menu_results = {}
        for menu_id in ["overview", "defects", "analytics", "inventory", "mes"]:
            print(f"테스트 중: {menu_id}")
            menu_start = datetime.now()
            
            try:
                data = get_menu_data_sync(menu_id)
                menu_end = datetime.now()
                menu_duration = (menu_end - menu_start).total_seconds()
                
                menu_results[menu_id] = {
                    "success": data is not None,
                    "data_type": type(data).__name__ if data else None,
                    "data_keys": list(data.keys()) if isinstance(data, dict) else None,
                    "data_source": data.get('data_source') if isinstance(data, dict) else None,
                    "duration": menu_duration
                }
            except Exception as e:
                menu_results[menu_id] = {
                    "success": False,
                    "error": str(e),
                    "duration": 0
                }
        
        # 3. 전체 데이터 테스트
        print("전체 데이터 크롤링 테스트...")
        all_data_start = datetime.now()
        
        try:
            all_data = get_all_menu_data_sync()
            all_data_end = datetime.now()
            all_data_duration = (all_data_end - all_data_start).total_seconds()
            
            all_data_result = {
                "success": all_data is not None,
                "menus_count": len(all_data) if all_data else 0,
                "duration": all_data_duration,
                "metadata": all_data.get('_metadata') if isinstance(all_data, dict) else None
            }
        except Exception as e:
            all_data_result = {
                "success": False,
                "error": str(e),
                "duration": 0
            }
        
        test_end = datetime.now()
        total_duration = (test_end - test_start).total_seconds()
        
        # 결과 요약
        successful_endpoints = sum(1 for result in endpoint_results['results'].values() if result.get('success'))
        successful_menus = sum(1 for result in menu_results.values() if result.get('success'))
        
        return jsonify({
            "status": "completed",
            "timestamp": test_end.isoformat(),
            "summary": {
                "total_duration": total_duration,
                "endpoints_success_rate": f"{endpoint_results['success_rate']}%",
                "menus_success_rate": f"{(successful_menus / len(menu_results) * 100):.1f}%",
                "overall_health": "good" if successful_endpoints > 0 and successful_menus > 0 else "poor"
            },
            "results": {
                "endpoints": endpoint_results,
                "individual_menus": menu_results,
                "all_data": all_data_result
            }
        })
        
    except Exception as e:
        print(f"❌ 크롤러 테스트 오류: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@chat_bp.route('/test-endpoints', methods=['GET'])
def test_endpoints():
    """실제 API 엔드포인트들이 동작하는지 테스트 (신규 추가)"""
    try:
        print("🔍 API 엔드포인트 테스트 시작...")
        
        # 크롤러의 엔드포인트 테스트 기능 사용
        results = crawler.test_all_endpoints()
        
        return jsonify(results)
        
    except Exception as e:
        print(f"❌ 엔드포인트 테스트 오류: {e}")
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@chat_bp.route('/debug', methods=['GET'])
def debug_info():
    """디버깅 정보 제공 엔드포인트 (신규 추가)"""
    try:
        debug_info = {
            "server_info": {
                "base_url": crawler.base_url,
                "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}",
                "timestamp": datetime.now().isoformat()
            },
            "gemini_status": get_api_status(),
            "environment_vars": {
                "GEMINI_API_KEY": "설정됨" if os.getenv("GEMINI_API_KEY") else "설정 안됨",
                "PORT": os.getenv("PORT", "기본값"),
                "FLASK_ENV": os.getenv("FLASK_ENV", "기본값")
            },
            "prompt_templates": list(PROMPT_TEMPLATES.keys()),
            "available_endpoints": [
                "/api/llm",
                "/api/chat", 
                "/api/health",
                "/api/test-crawler",
                "/api/test-endpoints",
                "/api/debug"
            ]
        }
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500