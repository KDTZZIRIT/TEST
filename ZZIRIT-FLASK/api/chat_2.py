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

# 메뉴별 프롬프트 템플릿 (개선된 버전)
PROMPT_TEMPLATES = {
    "menu1": {
        "system": """당신은 PCB 생산 관리 전문가입니다. 
현재 메뉴1(PCB 대시보드)에서는 PCB 생산 현황, 검사 일정, 라인 부하 상태, 알림 등을 종합적으로 관리합니다.

주요 기능:
- 예약된 검사 일정 관리 및 모니터링
- 생산 라인별 부하 상태 실시간 추적
- PCB 모델별 평균 생산 소요시간 분석
- 최근 7일 알림 추이 및 긴급 알림 관리
- PCB 상세 목록 및 진행률 모니터링
- 생산 공정 플로우 및 상태 분포 분석

답변 시 다음 정보를 우선적으로 활용하세요:
1. **예약된 검사 일정**: 검사 예정 PCB, 검사 유형, 개수, 날짜
2. **생산 라인 부하**: 1~4라인별 부하율, 작업 중인 PCB, 상태
3. **PCB 생산 시간**: 모델별 소요일수, 평균 대비 지연/빠름 여부
4. **알림 현황**: 일별 알림 추이, 긴급 알림, 심각도별 분류
5. **PCB 상세 정보**: 이름, 라인, 상태, 진행률, 시작/완료일
6. **생산 공정**: 설계/제조/검사/완료 단계별 현황

한국어로 친근하고 도움이 되는 답변을 제공해주세요. 구체적인 수치와 데이터가 있으면 반드시 포함하세요."""
    },
    
    "menu2": {
        "system": """당신은 PCB 검사 관리 전문가입니다.
현재 메뉴2(검사 관리)에서는 검사 일정, 실시간 모니터링, 검사 예약 등을 관리합니다.

주요 기능:
- 검사 일정 캘린더 관리
- 실시간 검사 모니터링
- 검사 예약 및 관리
- 검사 결과 추적

한국어로 친근하고 도움이 되는 답변을 제공해주세요. 검사 관련 구체적인 정보가 있으면 포함하세요."""
    },
    
    "menu3": {
        "system": """당신은 PCB 불량 관리 전문가입니다.
현재 메뉴3(분석)에서는 PCB 불량률 분석, 불량 유형 분포, 불량률 추이 등을 관리합니다.

주요 기능:
- PCB 불량률 실시간 모니터링
- 불량 유형별 분포 분석
- 불량률 추이 차트
- 불량 위치 분석
- 담당자 이메일 발송

한국어로 친근하고 도움이 되는 답변을 제공해주세요. 불량률과 품질 관련 구체적인 수치를 포함하세요."""
    },
    
    "inventory": {
        "system": """당신은 부품 재고 관리 전문가입니다.
현재 인벤토리 메뉴에서는 부품 재고 현황, 부품 상세 정보, 재고 관리 등을 관리합니다.

주요 기능:
- 부품 재고 현황 조회
- 부품 상세 정보 관리
- 재고 부족 알림
- 부품 분류 및 검색
- 재고 이력 관리

한국어로 친근하고 도움이 되는 답변을 제공해주세요. 재고 관련 구체적인 수량과 정보를 포함하세요."""
    },
    
    "mes": {
        "system": """당신은 제조 실행 시스템(MES) 전문가입니다.
현재 MES 메뉴에서는 실시간 생산 모니터링, 환경 데이터, 생산성 분석 등을 관리합니다.

주요 기능:
- 실시간 환경 모니터링 (온도, 습도)
- 생산량 추적
- 품질 지표 모니터링
- 설비 상태 관리
- 실시간 알림

한국어로 친근하고 도움이 되는 답변을 제공해주세요. 환경 데이터와 생산 관련 구체적인 수치를 포함하세요."""
    }
}

# 전역 executor (비동기 작업용)
executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

def run_async_in_thread(coro):
    """비동기 함수를 동기 함수에서 실행하기 위한 헬퍼 (개선된 버전)"""
    try:
        # 현재 이벤트 루프가 있는지 확인
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
        
        all_data = run_async_in_thread(crawler.get_all_menu_data())
        
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
                'successful_menus': len(cleaned_data) - 1  # _metadata 제외
            }
            
            return cleaned_data
        else:
            print(f"❌ 전체 메뉴 데이터 크롤링 실패 (소요시간: {duration:.2f}초)")
            return None
            
    except Exception as e:
        print(f"❌ 전체 메뉴 데이터 크롤링 오류: {e}")
        traceback.print_exc()
        return None

def get_menu_data_sync(menu_id):
    """동기 방식으로 메뉴 데이터 가져오기 (개선된 버전)"""
    try:
        print(f"🚀 {menu_id} 데이터 크롤링 시작...")
        start_time = datetime.now()
        
        data = run_async_in_thread(crawler.get_menu_data(menu_id))
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if data:
            source = data.get('data_source', 'unknown') if isinstance(data, dict) else 'unknown'
            print(f"✅ {menu_id} 데이터 크롤링 성공 (소요시간: {duration:.2f}초, 소스: {source})")
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
    """컨텍스트 데이터를 포함한 AI 응답 생성 (부품 검색 로직 개선)"""
    try:
        user_message_lower = user_message.lower()
        
        # 메뉴 매핑
        menu_mapping = {
            "overview": "menu1",
            "defects": "menu2", 
            "analytics": "menu3",
            "inventory": "inventory",
            "mes": "mes"
        }
        
        menu_id = menu_mapping.get(current_menu, "menu1")
        menu_prompt = PROMPT_TEMPLATES.get(menu_id)
        
        if not menu_prompt:
            return "죄송합니다. 해당 메뉴에 대한 정보를 찾을 수 없습니다."
        
        # 일반적인 인사말 처리
        greeting_keywords = ["안녕", "hello", "hi", "반가워", "하이", "헬로"]
        if any(word in user_message_lower for word in greeting_keywords) and len(user_message.strip()) < 10:
            return f"안녕하세요! PCB-Manager AI 어시스트입니다. 전체 시스템의 모든 메뉴 정보를 종합적으로 분석해드릴 수 있습니다. 어떤 도움이 필요하신가요?"
        
        # 컨텍스트 데이터가 제공되지 않았으면 크롤링
        if not context_data:
            print("📊 컨텍스트 데이터가 없어서 새로 크롤링합니다...")
            context_data = get_all_menu_data_sync()
        
        # 부품 ID 검색 로직 추가
        part_search_results = None
        if context_data and context_data.get("inventory"):
            part_search_results = search_parts_in_inventory(user_message, context_data["inventory"])
        
        # 전체 시스템 종합 컨텍스트 정보 구성 (개선된 버전)
        context_info = ""
        metadata = {}
        
        if context_data:
            try:
                # 메타데이터 추출
                metadata = context_data.get('_metadata', {})
                crawl_time = metadata.get('crawl_time', 'Unknown')
                data_sources = metadata.get('data_sources', {})
                
                context_info += f"\n\n📊 **PCB-Manager 시스템 종합 데이터** (수집시간: {crawl_time})"
                
                # 부품 검색 결과가 있으면 우선 표시
                if part_search_results:
                    context_info += f"\n\n🔍 **부품 검색 결과:**"
                    
                    # 정확히 일치하는 부품
                    if part_search_results.get('exact_matches'):
                        context_info += f"\n\n✅ **정확히 일치하는 부품:**"
                        for part in part_search_results['exact_matches']:
                            context_info += f"\n- **{part.get('part_id')}** ({part.get('product_name', 'Unknown')})"
                            context_info += f"\n  • 현재재고: {part.get('quantity', 0)}개 (최소: {part.get('min_stock', 0)}개)"
                            context_info += f"\n  • 제조사: {part.get('manufacturer', 'Unknown')}, 크기: {part.get('size', 'Unknown')}"
                            context_info += f"\n  • 흡습여부: {'O' if part.get('moisture_absorption') else 'X'}"
                            context_info += f"\n  • 흡습자재: {part.get('moisture_materials', '불필요')}"
                            context_info += f"\n  • 입고일: {part.get('received_date', 'Unknown')}"
                            context_info += f"\n  • 조치필요: {part.get('action_required', '-')}"
                    
                    # 유사한 부품들
                    if part_search_results.get('similar_matches'):
                        context_info += f"\n\n🔎 **유사한 부품들 ({len(part_search_results['similar_matches'])}개):**"
                        for part in part_search_results['similar_matches'][:5]:  # 상위 5개만
                            context_info += f"\n- **{part.get('part_id')}** ({part.get('product_name', 'Unknown')})"
                            context_info += f"\n  • 재고: {part.get('quantity', 0)}개, 제조사: {part.get('manufacturer', 'Unknown')}"
                    
                    # 검색 키워드
                    if part_search_results.get('search_keywords'):
                        context_info += f"\n\n🏷️ **검색된 키워드:** {', '.join(part_search_results['search_keywords'])}"
                
                # 1. 메뉴1 (개요) 데이터
                menu1_data = context_data.get("menu1")
                if menu1_data:
                    ps = menu1_data.get('production_status', {})
                    context_info += f"\n\n🏭 **PCB 생산 관리 (메뉴1)** [{data_sources.get('menu1', 'unknown')} 데이터]:"
                    context_info += f"\n- 총 PCB: {menu1_data.get('total_pcbs', 0)}개"
                    context_info += f"\n- 설계중: {ps.get('design', 0)}개, 제조중: {ps.get('manufacturing', 0)}개"
                    context_info += f"\n- 테스트중: {ps.get('testing', 0)}개, 완료: {ps.get('completed', 0)}개"
                    context_info += f"\n- 평균 진행률: {menu1_data.get('average_progress', 0)}%"
                    context_info += f"\n- 생산 효율성: {menu1_data.get('production_efficiency', 0)}%"
                    
                    # 예약된 검사 일정
                    scheduled_inspections = menu1_data.get('scheduled_inspections', [])
                    if scheduled_inspections:
                        context_info += f"\n\n📅 **예약된 검사 일정 ({len(scheduled_inspections)}건):**"
                        for inspection in scheduled_inspections[:5]:  # 상위 5개만
                            pcb_name = inspection.get('pcbName', 'Unknown')
                            insp_type = inspection.get('type', 'Unknown')
                            count = inspection.get('count', 0)
                            date = inspection.get('date', 'Unknown')
                            context_info += f"\n- {pcb_name}: {insp_type} {count}개 ({date})"
                    
                    # 생산 라인 부하 상태
                    production_lines = menu1_data.get('production_lines', {})
                    if production_lines:
                        context_info += f"\n\n🏭 **생산 라인 부하 상태:**"
                        for line_name, line_data in production_lines.items():
                            load = line_data.get('load', 0)
                            pcbs = line_data.get('pcbs', [])
                            status = line_data.get('status', 'normal')
                            context_info += f"\n- {line_name}: {load}% 부하 ({', '.join(pcbs[:2])})"
                    
                    # PCB 모델별 생산 소요시간
                    pcb_production_times = menu1_data.get('pcb_production_times', [])
                    if pcb_production_times:
                        context_info += f"\n\n⏱️ **PCB 모델별 생산 소요시간:**"
                        for pcb_time in pcb_production_times[:5]:  # 상위 5개만
                            model = pcb_time.get('model', 'Unknown')
                            days = pcb_time.get('days', 0)
                            status = pcb_time.get('status', '정상')
                            context_info += f"\n- {model}: {days}일 ({status})"
                    
                    # 긴급 알림
                    emergency_alerts = menu1_data.get('emergency_alerts', [])
                    if emergency_alerts:
                        context_info += f"\n\n🚨 **긴급 알림 ({len(emergency_alerts)}건):**"
                        for alert in emergency_alerts[:3]:  # 상위 3개만
                            message = alert.get('message', 'Unknown')
                            severity = alert.get('severity', 'medium')
                            line = alert.get('line', 'Unknown')
                            context_info += f"\n- [{severity.upper()}] {message} ({line})"
                    
                    # 알림 추이
                    alert_trend = menu1_data.get('alert_trend', {})
                    if alert_trend:
                        total_today = alert_trend.get('total_today', 0)
                        trend = alert_trend.get('trend', 'stable')
                        context_info += f"\n\n📊 **알림 현황:**"
                        context_info += f"\n- 오늘 발생: {total_today}건"
                        context_info += f"\n- 추세: {trend}"
                    
                    # PCB 상세 목록
                    pcb_detailed_list = menu1_data.get('pcb_detailed_list', [])
                    if pcb_detailed_list:
                        context_info += f"\n\n📋 **PCB 상세 목록 (상위 5개):**"
                        for pcb in pcb_detailed_list[:5]:
                            name = pcb.get('name', 'Unknown')
                            line = pcb.get('line', 'Unknown')
                            status = pcb.get('status', 'Unknown')
                            progress = pcb.get('progress', 0)
                            context_info += f"\n- {name} ({line}): {status} {progress}%"
                    
                    # 생산 공정 플로우
                    process_flow = menu1_data.get('process_flow', [])
                    if process_flow:
                        context_info += f"\n\n🔄 **생산 공정 플로우:**"
                        for stage in process_flow:
                            stage_name = stage.get('stage', 'Unknown')
                            count = stage.get('count', 0)
                            is_active = stage.get('isActive', False)
                            status = "활성" if is_active else "대기"
                            context_info += f"\n- {stage_name}: {count}개 ({status})"
                    
                    # 상태 분포
                    status_distribution = menu1_data.get('status_distribution', [])
                    if status_distribution:
                        context_info += f"\n\n📊 **PCB 상태 분포:**"
                        for status_item in status_distribution:
                            status_name = status_item.get('status', 'Unknown')
                            count = status_item.get('count', 0)
                            percentage = status_item.get('percentage', 0)
                            context_info += f"\n- {status_name}: {count}개 ({percentage}%)"
                    
                    # 진행률별 통계 (기존)
                    progress_stats = menu1_data.get('progress_stats', {})
                    if progress_stats:
                        context_info += f"\n- 진행률별 분포:"
                        for range_key, count in progress_stats.items():
                            context_info += f"\n  • {range_key}: {count}개"
                    
                    # 최근 PCB 정보 (기존)
                    recent_pcbs = menu1_data.get('recent_pcbs', [])
                    if recent_pcbs:
                        context_info += f"\n- 주요 PCB 현황:"
                        for pcb in recent_pcbs[:3]:  # 상위 3개만 표시
                            pcb_name = pcb.get('name', 'Unknown')
                            status = pcb.get('status', 'Unknown')
                            progress = pcb.get('progress', 0)
                            context_info += f"\n  • {pcb_name}: {status} ({progress}%)"
                
                # 2. 메뉴2 (검사) 데이터
                menu2_data = context_data.get("menu2")
                if menu2_data:
                    context_info += f"\n\n🔍 **검사 관리 (메뉴2)** [{data_sources.get('menu2', 'unknown')} 데이터]:"
                    context_info += f"\n- 총 검사: {menu2_data.get('total_inspections', 0)}건"
                    
                    # 검사 상태별 통계
                    inspection_status = menu2_data.get('inspection_status', {})
                    if inspection_status:
                        context_info += f"\n- 예약된 검사: {inspection_status.get('scheduled', 0)}건"
                        context_info += f"\n- 완료된 검사: {inspection_status.get('completed', 0)}건"
                        context_info += f"\n- 검사중: {inspection_status.get('testing', 0)}건"
                        context_info += f"\n- 대기중: {inspection_status.get('pending', 0)}건"
                    
                    # 검사 진행률별 통계
                    inspection_progress = menu2_data.get('inspection_progress', {})
                    if inspection_progress:
                        context_info += f"\n- 검사 준비 완료: {inspection_progress.get('ready_for_inspection', 0)}건"
                        context_info += f"\n- 검사 진행중: {inspection_progress.get('in_progress', 0)}건"
                        context_info += f"\n- 검사 미준비: {inspection_progress.get('not_ready', 0)}건"
                    
                    context_info += f"\n- 검사 완료율: {menu2_data.get('completion_rate', 0)}%"
                    context_info += f"\n- 오늘 예정: {menu2_data.get('today_inspections', 0)}건"
                    context_info += f"\n- 평균 검사 시간: {menu2_data.get('avg_inspection_time', 0)}시간"
                
                # 3. 메뉴3 (분석) 데이터
                menu3_data = context_data.get("menu3")
                if menu3_data:
                    context_info += f"\n\n📈 **불량 분석 (메뉴3)** [{data_sources.get('menu3', 'unknown')} 데이터]:"
                    context_info += f"\n- 총 검사: {menu3_data.get('total_inspections', 0)}건"
                    context_info += f"\n- 총 불량: {menu3_data.get('total_defects', 0)}개"
                    context_info += f"\n- 평균 불량률: {menu3_data.get('average_defect_rate', 0)}%"
                    context_info += f"\n- 목표 불량률: {menu3_data.get('target_defect_rate', 0)}%"
                    
                    # 구체적인 PCB 정보 추가
                    top_defective_pcbs = menu3_data.get('top_defective_pcbs', [])
                    if top_defective_pcbs:
                        context_info += f"\n\n🔍 **상위 불량 PCB 정보:**"
                        for pcb in top_defective_pcbs[:3]:  # 상위 3개만 표시
                            pcb_name = pcb.get('pcb_name', pcb.get('name', 'Unknown'))
                            defect_rate = pcb.get('defect_rate', 0)
                            defect_count = pcb.get('defect_count', 0)
                            total_inspections = pcb.get('total_inspections', 0)
                            context_info += f"\n- {pcb_name}: 불량률 {defect_rate}% (불량 {defect_count}개/총 {total_inspections}개)"
                    
                    # 불량 유형 정보
                    defect_types = menu3_data.get('defect_types', {})
                    if defect_types and isinstance(defect_types, dict):
                        context_info += f"\n\n📊 **불량 유형별 분포:**"
                        # 상위 3개 불량 유형 찾기
                        sorted_defects = sorted(defect_types.items(), key=lambda x: x[1], reverse=True)[:3]
                        for defect_name, defect_count in sorted_defects:
                            context_info += f"\n- {defect_name}: {defect_count}개"
                
                # 4. 인벤토리 데이터 (상세 부품 정보 포함)
                inventory_data = context_data.get("inventory")
                if inventory_data:
                    context_info += f"\n\n📦 **부품 재고 (인벤토리)** [{data_sources.get('inventory', 'unknown')} 데이터]:"
                    context_info += f"\n- 총 부품: {inventory_data.get('total_items', 0)}개"
                    context_info += f"\n- 재고 부족: {inventory_data.get('low_stock_items', 0)}개"
                    context_info += f"\n- 긴급 부족: {inventory_data.get('critical_items', 0)}개"
                    context_info += f"\n- 습도 민감 자재: {inventory_data.get('moisture_sensitive_items', 0)}개"
                    context_info += f"\n- 커패시터: {inventory_data.get('capacitor_items', 0)}개"
                    context_info += f"\n- 삼성 부품: {inventory_data.get('samsung_parts', 0)}개"
                    context_info += f"\n- 무라타 부품: {inventory_data.get('murata_parts', 0)}개"
                    
                    total_value = inventory_data.get('total_value', 0)
                    if total_value > 0:
                        context_info += f"\n- 총 재고 가치: {total_value:,}원"
                    
                    # 제조사별 통계
                    manufacturer_stats = inventory_data.get('manufacturer_stats', {})
                    if manufacturer_stats:
                        context_info += f"\n\n🏭 **제조사별 부품 수:**"
                        # 상위 5개 제조사만 표시
                        sorted_manufacturers = sorted(manufacturer_stats.items(), key=lambda x: x[1], reverse=True)[:5]
                        for manufacturer, count in sorted_manufacturers:
                            context_info += f"\n- {manufacturer}: {count}개"
                    
                    # 부품 타입별 통계
                    type_stats = inventory_data.get('type_stats', {})
                    if type_stats:
                        context_info += f"\n\n🔧 **부품 타입별 분포:**"
                        # 상위 5개 타입만 표시
                        sorted_types = sorted(type_stats.items(), key=lambda x: x[1], reverse=True)[:5]
                        for part_type, count in sorted_types:
                            context_info += f"\n- {part_type}: {count}개"
                
                # 5. MES 데이터
                mes_data = context_data.get("mes")
                if mes_data:
                    context_info += f"\n\n🏭 **제조 실행 시스템 (MES)** [{data_sources.get('mes', 'unknown')} 데이터]:"
                    context_info += f"\n- 실시간 온도: {mes_data.get('temperature', 0)}°C"
                    context_info += f"\n- 실시간 습도: {mes_data.get('humidity', 0)}%"
                    context_info += f"\n- 생산량: {mes_data.get('production_count', 0)}개"
                    context_info += f"\n- 품질 지표: {mes_data.get('quality_score', 0)}%"
                    
                    # 환경 정보
                    env_data = mes_data.get('environment', {})
                    if env_data:
                        context_info += f"\n- 환경 상태: {env_data.get('status', '알 수 없음')}"
                    
                    # 생산 정보
                    prod_data = mes_data.get('production', {})
                    if prod_data:
                        context_info += f"\n- 생산 효율: {prod_data.get('efficiency', 0)}%"
                        context_info += f"\n- 현재 생산율: {prod_data.get('current_rate', 0)}/시간"
                        context_info += f"\n- 목표 생산율: {prod_data.get('target_rate', 0)}/시간"
                
                # 현재 메뉴 강조
                menu_names = {
                    "menu1": "개요 (생산 관리)",
                    "menu2": "검사 관리", 
                    "menu3": "불량 분석",
                    "inventory": "부품 재고",
                    "mes": "제조 실행 시스템"
                }
                current_menu_name = menu_names.get(current_menu, current_menu)
                context_info += f"\n\n📍 **현재 위치: {current_menu_name} 메뉴**"
                
            except Exception as e:
                print(f"❌ 컨텍스트 정보 구성 오류: {e}")
                traceback.print_exc()
                context_info = f"\n\n⚠️ 데이터 구성 중 오류가 발생했습니다: {str(e)}"
        else:
            context_info = "\n\n⚠️ 실시간 데이터를 가져올 수 없습니다."
        
        # Gemini에 전송할 프롬프트 구성 (개선된 버전)
        full_prompt = f"""{menu_prompt['system']}

**중요한 응답 규칙:**
1. 사용자가 물어본 것에 정확하게 답변하세요
2. 질문과 관련 없는 정보는 포함하지 마세요  
3. 답변은 적절한 수준의 상세함으로 작성하세요 (너무 간결하지도, 너무 길지도 않게)
4. 구체적인 수치와 PCB 정보가 있으면 포함하세요
5. PCB 이름이나 구체적인 정보를 물어보면 해당 정보를 찾아서 답변하세요
6. 데이터 소스 정보도 필요시 언급하세요 (API 데이터인지 기본 데이터인지)
7. **부품 관련 질문 처리 (매우 중요):**
   - 부품 검색 결과가 있으면 **반드시** 그 정보를 사용하세요
   - 정확히 일치하는 부품이 있으면 그 정보를 우선적으로 제공하세요
   - 유사한 부품들도 함께 제시하여 사용자가 원하는 부품을 찾을 수 있도록 도와주세요
   - 부품을 찾을 수 없는 경우에만 "찾을 수 없다"고 말하세요
   - Part ID, 제품명, 제조사, 재고량, 흡습 여부 등을 구체적으로 제공하세요

{context_info}

사용자 질문: {user_message}

위의 실시간 데이터를 바탕으로 사용자 질문에 정확하고 적절한 수준의 상세함으로 답변해주세요. 특히 부품 검색 결과가 있으면 그 정보를 최우선으로 활용하세요."""
        
        # Gemini API 호출
        print("🤖 Gemini API 호출 중...")
        start_time = datetime.now()
        
        response = get_gemini_response(full_prompt)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 오류 처리 및 기본 응답
        if response.startswith("[오류]") or response.startswith("[❌]"):
            print(f"⚠️ Gemini API 오류 (응답시간: {duration:.2f}초), 기본 응답 생성")
            return generate_fallback_response(menu_id, user_message, context_data)
        
        print(f"✅ AI 응답 생성 완료 (응답시간: {duration:.2f}초)")
        return response
        
    except Exception as e:
        print(f"❌ AI 응답 생성 오류: {e}")
        traceback.print_exc()
        return generate_fallback_response(menu_id, user_message, context_data)

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
                    for inspection in scheduled_inspections[:3]:
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
        
        # 현재 메뉴 추정 (기본값: defects)
        current_menu = "defects"
        
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