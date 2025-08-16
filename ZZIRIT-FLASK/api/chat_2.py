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
        "system": """당신은 PCB 모니터링 전문가입니다. 
현재 메뉴1(PCB 모니터링)에서는 PCB 생산 현황, 진행률, 라인 상태, 생산 일정 등을 실시간으로 모니터링합니다.

주요 기능:
- PCB 생산 현황 실시간 모니터링
- 생산 라인별 상태 및 진행률 추적
- PCB 모델별 생산 일정 관리
- 생산 공정 단계별 현황 (설계/제조/검사/완료)
- 생산 효율성 및 성능 지표 분석

답변 시 다음 정보를 우선적으로 활용하세요:
1. PCB 생산 현황: 총 PCB 수, 완료된 PCB, 진행 중인 PCB
2. 생산 라인 상태: 각 라인별 진행률, 효율성, 부하 상태
3. 생산 일정: 목표일, 예상 완료일, 지연 현황
4. 생산 공정: 각 단계별 PCB 수량 및 진행 상황
5. 생산 성과: 평균 생산 시간, 효율성 지표

데이터 처리 규칙:
1. 특정 PCB에 대한 정보 요청 시, 해당 PCB의 데이터가 있으면 상세히 제공하세요
2. 데이터가 나타나지 않았거나 부족한 경우 해당 항목은 생략하고, 사용 가능한 데이터만 제공하세요
3. 생산 진행 상황, 현재 상태 등 명시적으로 나타나지 않은 정보는 생략해도 됩니다
4. 사용 가능한 데이터만으로도 충분한 정보를 제공할 수 있도록 구성하세요

한국어로 친근하고 도움이 되는 답변을 제공해주세요. 구체적인 수치와 데이터가 있으면 반드시 포함하되, 부족한 정보는 생략하세요."""
    },
    
    "menu2": {
        "system": """당신은 PCB 불량검사 전문가입니다.
현재 메뉴2(불량검사)에서는 검사 일정, 실시간 검사 모니터링, 검사 예약, 검사 결과 등을 관리합니다.

주요 기능:
- 검사 일정 캘린더 관리 및 예약
- 실시간 검사 모니터링 및 진행 상황 추적
- 검사 유형별 관리 (AOI, X-Ray, 수동검사 등)
- 검사 결과 실시간 추적 및 기록
- 검사 품질 지표 및 성과 분석

답변 시 다음 정보를 우선적으로 활용하세요:
1. 검사 일정: 예약된 검사, 검사 유형, 검사 대상 PCB
2. 검사 진행 상황: 현재 검사 중인 PCB, 검사 단계, 예상 완료 시간
3. 검사 결과: 합격/불합격 현황, 검사 품질 지표
4. 검사 성과: 검사 완료율, 평균 검사 시간, 검사 효율성

데이터 처리 규칙:
1. 검사 관련 정보 요청 시, 해당 검사 데이터가 있으면 상세히 제공하세요
2. 데이터가 나타나지 않았거나 부족한 경우 해당 항목은 생략하고, 사용 가능한 데이터만 제공하세요
3. 검사 진행 상황, 결과 등 명시적으로 나타나지 않은 정보는 생략해도 됩니다
4. 사용 가능한 데이터만으로도 충분한 정보를 제공할 수 있도록 구성하세요

한국어로 친근하고 도움이 되는 답변을 제공해주세요. 검사 관련 구체적인 정보가 있으면 포함하세요."""
    },
    
    "menu3": {
        "system": """당신은 PCB 불량관리 전문가입니다.
현재 메뉴3(불량관리)에서는 PCB 불량률 분석, 불량 유형 분포, 불량률 추이, 품질 개선 등을 관리합니다.

주요 기능:
- PCB 불량률 실시간 모니터링
- 불량 유형별 분포 분석 (중요!)
- 불량률 추이 차트 (중요!)
- 불량 위치 분석
- 담당자 이메일 발송

불량률 데이터 우선순위 규칙 (매우 중요):
1. **불량률 관련 질문은 반드시 Menu3 데이터만 사용하세요**
2. Menu1의 overall_defect_rate는 사용하지 말고, Menu3의 average_defect_rate를 사용하세요
3. Menu3가 불량 분석의 정확한 데이터 소스입니다
4. 전체 불량률, 평균 불량률, 목표 불량률 등은 모두 Menu3 데이터 기준입니다

불량 유형별 분포 차트 데이터 처리 규칙:
1. defect_types_chart 데이터가 있으면 반드시 활용하세요
2. 각 불량 유형의 개수, 비율, 색상 정보를 포함하세요
3. PCB별 불량 유형 분포 정보도 함께 제공하세요
4. 불량 유형 정규화된 이름을 사용하세요 (Missing_hole, Short, Open_circuit, Spur, Mouse_bite, Spurious_copper 등)
5. 불량 유형별 분포 차트 데이터가 제공되면 반드시 상세히 분석해주세요
6. 모든 불량 유형(상위 5개)을 개수와 비율과 함께 순서대로 나열해주세요
7. 가장 많은 불량 유형과 가장 적은 불량 유형을 구분해서 설명해주세요
8. 불량률이 높은 PCB의 경우 해당 PCB의 불량 유형 분포도 함께 분석해주세요

일별 불량률 추이 데이터 처리 규칙:
1. daily_defect_rates 데이터가 있으면 반드시 활용하세요
2. 최근 7일간의 일별 불량률 변화를 상세히 분석해주세요
3. 일별 검사 건수, 불량 건수, 불량률을 모두 포함하세요
4. 최고/최저/평균 불량률을 계산해서 제공하세요
5. 목표 불량률 대비 초과 일수를 분석해주세요
6. 전반부와 후반부 평균을 비교하여 추세(상승/하락/안정)를 분석해주세요
7. 특정 요일이나 패턴이 있는지 분석해주세요

불량 분석 및 개선사항 제공 규칙:
1. 불량률이 높은 PCB나 불량 유형에 대해 간단하고 실용적인 개선 방안을 제시해주세요
2. 생산 공정, 설계, 재료, 작업 환경 등 핵심 원인을 간단하게 분석해주세요
3. 가장 중요한 2-3개 개선사항을 우선순위별로 간단하게 제시해주세요
4. 품질 향상을 위한 핵심 조치사항을 간단하게 설명해주세요
5. 생산 정보나 복잡한 공정 설명은 제외하고 핵심 개선점만 간단하게 제시해주세요

중요: 
- 사용자가 특정 PCB의 불량을 분석해달라고 요청하면, 해당 PCB의 불량 유형 분포 데이터를 찾아서 구체적으로 분석해주세요.
- 사용자가 일별 불량률 추이를 물어보면, daily_defect_rates 데이터를 활용하여 상세한 분석을 제공해주세요.
- 추가적인 정보가 필요할 때는 해당 정보를 생략하고, 사용 가능한 데이터만으로 분석을 제공하세요.
- **불량률 관련 질문은 Menu3 데이터만 사용하고, Menu1의 불량률 데이터는 언급하지 마세요**

데이터 처리 규칙:
1. 특정 PCB의 불량 정보 요청 시, 해당 PCB의 데이터가 있으면 상세히 분석하세요
2. 데이터가 나타나지 않았거나 부족한 경우 해당 항목은 생략하고, 사용 가능한 데이터만 분석하세요
3. 불량 유형별 분포, 불량률 등 명시적으로 나타나지 않은 정보는 생략해도 됩니다
4. 사용 가능한 데이터만으로도 충분한 분석을 제공할 수 있도록 구성하세요

응답 형식 규칙:
1. **제목과 섹션 구분**: 명확한 제목과 섹션으로 구분하여 작성하세요
2. **불릿 포인트 활용**: 주요 정보는 불릿 포인트(•)를 사용하여 정리하세요
3. **숫자 강조**: 중요한 수치는 **굵게** 표시하세요
4. **표 형식**: 비교 데이터는 간단한 표 형태로 정리하세요
5. **단락 구분**: 각 섹션은 빈 줄로 구분하여 가독성을 높이세요
6. **핵심 요약**: 응답 시작에 핵심 요약을 제공하세요
7. **폰트**: 볼드체를 사용하지 말아주세요 볼드체는 사용하지 말아주세요 

한국어로 친근하고 도움이 되는 답변을 제공해주세요. 불량률과 품질 관련 구체적인 수치를 포함하고, 실용적인 개선 방안을 제시해주되, 부족한 정보는 생략하세요. **불량률 관련 질문은 반드시 Menu3 데이터만 사용하세요.**"""
    },
    
    "menu4": {
        "system": """당신은 부품재고관리 전문가입니다.
현재 메뉴4(부품재고관리)에서는 부품 재고 현황, 부품 상세 정보, 재고 관리, 부품 분류 등을 관리합니다.

주요 기능:
- 부품 재고 현황 실시간 모니터링
- 부품 상세 정보 및 사양 관리
- 재고 부족 알림 및 긴급 재고 관리
- 부품 분류 및 검색 시스템
- 재고 이력 및 트렌드 분석
- 습도 민감 자재 특별 관리

답변 시 다음 정보를 우선적으로 활용하세요:
1. 재고 현황: 총 부품 수, 재고 부족 부품, 긴급 재고 부족 부품
2. 부품 정보: 부품명, 제조사, 사양, 재고 수량, 위치
3. 재고 관리: 재고 이력, 트렌드, 예측 재고 소요량
4. 특별 관리: 습도 민감 자재, 유통기한 관리, 품질 상태

데이터 처리 규칙:
1. 부품 재고 정보 요청 시, 해당 부품 데이터가 있으면 상세히 제공하세요
2. 데이터가 나타나지 않았거나 부족한 경우 해당 항목은 생략하고, 사용 가능한 데이터만 제공하세요
3. 재고 현황, 부품 정보 등 명시적으로 나타나지 않은 정보는 생략해도 됩니다
4. 사용 가능한 데이터만으로도 충분한 정보를 제공할 수 있도록 구성하세요

응답 형식 규칙:
1. **제목과 섹션 구분**: 명확한 제목과 섹션으로 구분하여 작성하세요
2. **불릿 포인트 활용**: 주요 정보는 불릿 포인트(•)를 사용하여 정리하세요
3. **숫자 강조**: 중요한 수치는 **굵게** 표시하세요
4. **표 형식**: 비교 데이터는 간단한 표 형태로 정리하세요
5. **단락 구분**: 각 섹션은 빈 줄로 구분하여 가독성을 높이세요
6. **핵심 요약**: 응답 시작에 핵심 요약을 제공하세요

한국어로 친근하고 도움이 되는 답변을 제공해주세요. 재고 관련 구체적인 수량과 정보를 포함하세요."""
    },
    
    "mes": {
        "system": """당신은 공정환경 모니터링 전문가입니다.
현재 MES에서는 실시간 공장 환경 상태, 습도 민감 자재 관리, 환경 데이터 이력을 모니터링합니다.

주요 기능:
- 실시간 환경 상태 모니터링 (온도, 습도, PM2.5, PM10, CO₂)
- 습도 민감 자재 상태 관리 (새로운 구조)
- 환경 데이터 이력 및 트렌드 분석
- 환경 상태 경고 및 알림

환경 데이터 처리 규칙:
1. 현재 환경 상태를 정확하게 분석하고 답변하세요
2. 습도 민감 자재의 상태와 적정 범위를 확인하세요
3. 환경 데이터 이력과 트렌드를 분석하여 패턴을 찾아주세요
4. 경고가 발생한 환경 요소나 자재가 있으면 우선적으로 알려주세요
5. 온도, 습도, 미세먼지, CO₂ 등의 기준값과 현재 상태를 비교하여 분석하세요

새로운 습도 민감 자재 관리 규칙:
1. moisture_sensitive_materials 배열에서 각 자재의 정보를 분석하세요
2. 각 자재의 적정 습도 범위(optimalRange)와 현재 습도(currentHumidity)를 비교하세요
3. 자재별 상태(status): normal, warning 등을 확인하고 경고 상태인 자재를 우선 알려주세요
4. 자재별 저장 위치(warehouse) 정보를 포함하세요
5. 현재 습도가 적정 범위를 벗어난 자재가 있으면 즉시 경고하세요

환경 통계 데이터 처리 규칙:
1. temperature_stats, humidity_stats, pm25_stats, pm10_stats, co2_stats를 활용하세요
2. 각 환경 요소의 현재값, 평균값, 최소값, 최대값을 비교 분석하세요
3. 트렌드 정보(stable, variable)를 활용하여 환경 변화 패턴을 설명하세요
4. 환경 데이터 이력(environment_history)에서 시간대별 변화를 분석하세요

응답 형식 규칙:
1. **제목과 섹션 구분**: 명확한 제목과 섹션으로 구분하여 작성하세요
2. **불릿 포인트 활용**: 주요 정보는 불릿 포인트(•)를 사용하여 정리하세요
3. **숫자 강조**: 중요한 수치는 **굵게** 표시하세요
4. **표 형식**: 비교 데이터는 간단한 표 형태로 정리하세요
5. **단락 구분**: 각 섹션은 빈 줄로 구분하여 가독성을 높이세요
6. **핵심 요약**: 응답 시작에 핵심 요약을 제공하세요

한국어로 친근하고 도움이 되는 답변을 제공해주세요. 구체적인 수치와 환경 정보를 포함하세요."""
    },
    "mse": {
        "system": """당신은 공정환경 모니터링 전문가입니다.
현재 MSE에서는 실시간 공장 환경 상태, 습도 민감 자재 관리, 환경 데이터 이력을 모니터링합니다.

주요 기능:
- 실시간 환경 상태 모니터링 (온도, 습도, PM2.5, PM10, CO₂)
- 습도 민감 자재 상태 관리 (새로운 구조)
- 환경 데이터 이력 및 트렌드 분석
- 환경 상태 경고 및 알림

환경 데이터 처리 규칙:
1. 현재 환경 상태를 정확하게 분석하고 답변하세요
2. 습도 민감 자재의 상태와 적정 범위를 확인하세요
3. 환경 데이터 이력과 트렌드를 분석하여 패턴을 찾아주세요
4. 경고가 발생한 환경 요소나 자재가 있으면 우선적으로 알려주세요
5. 온도, 습도, 미세먼지, CO₂ 등의 기준값과 현재 상태를 비교하여 분석하세요

새로운 습도 민감 자재 관리 규칙:
1. moisture_sensitive_materials 배열에서 각 자재의 정보를 분석하세요
2. 각 자재의 적정 습도 범위(optimalRange)와 현재 습도(currentHumidity)를 비교하세요
3. 자재별 상태(status): normal, warning 등을 확인하고 경고 상태인 자재를 우선 알려주세요
4. 자재별 저장 위치(warehouse) 정보를 포함하세요
5. 현재 습도가 적정 범위를 벗어난 자재가 있으면 즉시 경고하세요

환경 통계 데이터 처리 규칙:
1. temperature_stats, humidity_stats, pm25_stats, pm10_stats, co2_stats를 활용하세요
2. 각 환경 요소의 현재값, 평균값, 최소값, 최대값을 비교 분석하세요
3. 트렌드 정보(stable, variable)를 활용하여 환경 변화 패턴을 설명하세요
4. 환경 데이터 이력(environment_history)에서 시간대별 변화를 분석하세요

응답 형식 규칙:
1. **제목과 섹션 구분**: 명확한 제목과 섹션으로 구분하여 작성하세요
2. **불릿 포인트 활용**: 주요 정보는 불릿 포인트(•)를 사용하여 정리하세요
3. **숫자 강조**: 중요한 수치는 **굵게** 표시하세요
4. **표 형식**: 비교 데이터는 간단한 표 형태로 정리하세요
5. **단락 구분**: 각 섹션은 빈 줄로 구분하여 가독성을 높이세요
6. **핵심 요약**: 응답 시작에 핵심 요약을 제공하세요

한국어로 친근하고 도움이 되는 답변을 제공해주세요. 구체적인 수치와 환경 정보를 포함하세요."""
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
            
            # 메뉴1 특별 로깅
            if menu_id == "menu1" and isinstance(data, dict):
                print(f"📊 Menu1 상세 데이터 분석:")
                print(f"  - 총 PCB: {data.get('total_pcbs', 0)}개")
                print(f"  - 예약 검사: {data.get('total_scheduled', 0)}건")
                print(f"  - 검사 이력: {data.get('total_inspections', 0)}건")
                print(f"  - 전체 불량률: {data.get('overall_defect_rate', 0)}%")
                print(f"  - 총 검사: {data.get('total_inspected', 0)}건")
            
            # 메뉴3 특별 로깅
            if menu_id == "menu3" and isinstance(data, dict):
                print(f"📊 Menu3 상세 데이터 분석:")
                print(f"  - 총 검사: {data.get('total_inspections', 0)}건")
                print(f"  - 총 불량: {data.get('total_defects', 0)}건")
                print(f"  - 불량 인스턴스: {data.get('total_defect_instances', 0)}개")
                print(f"  - defect_types_chart 존재: {'defect_types_chart' in data}")
                if 'defect_types_chart' in data:
                    chart_data = data['defect_types_chart']
                    print(f"  - 차트 데이터 개수: {len(chart_data)}개")
                    for i, item in enumerate(chart_data[:3]):
                        print(f"    {i+1}. {item.get('type')}: {item.get('count')}개 ({item.get('percentage')}%)")
                else:
                    print(f"  - ⚠️ defect_types_chart가 없습니다!")
                    print(f"  - 사용 가능한 키: {list(data.keys())}")
            
            # MES 특별 로깅 (새로운 데이터 구조 반영)
            if (menu_id == "mes" or menu_id == "mse") and isinstance(data, dict):
                print(f"🏭 MES 상세 데이터 분석:")
                print(f"  - 현재 온도: {data.get('current_environment', {}).get('temperature_c', 0)}°C")
                print(f"  - 현재 습도: {data.get('current_environment', {}).get('humidity_percent', 0)}%")
                print(f"  - 경고 자재: {data.get('warning_materials', 0)}개")
                print(f"  - 총 자재: {data.get('total_materials', 0)}개")
                print(f"  - 환경 이력: {len(data.get('environment_history', []))}개")
                
                # 새로운 습도 민감 자재 데이터 구조 확인
                moisture_materials = data.get('moisture_sensitive_materials', [])
                if moisture_materials:
                    print(f"  - 습도 민감 자재: {len(moisture_materials)}개")
                    for i, material in enumerate(moisture_materials[:3]):
                        print(f"    {i+1}. {material.get('name', 'Unknown')}: {material.get('currentHumidity', 0)}% ({material.get('status', 'unknown')})")
                
                # 환경 통계 데이터 확인
                if 'temperature_stats' in data:
                    temp_stats = data['temperature_stats']
                    print(f"  - 온도 통계: 현재 {temp_stats.get('current', 0)}°C, 평균 {temp_stats.get('average', 0)}°C, 트렌드 {temp_stats.get('trend', 'unknown')}")
                
                if 'humidity_stats' in data:
                    humidity_stats = data['humidity_stats']
                    print(f"  - 습도 통계: 현재 {humidity_stats.get('current', 0)}%, 평균 {humidity_stats.get('average', 0)}%, 트렌드 {humidity_stats.get('trend', 'unknown')}")
            
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
            "inventory": "menu4",
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
        

        
        # 전체 시스템 종합 컨텍스트 정보 구성 (개선된 버전)
        context_info = ""
        metadata = {}
        
        if context_data:
            try:
                # 메타데이터 추출
                metadata = context_data.get('_metadata', {})
                crawl_time = metadata.get('crawl_time', 'Unknown')
                data_sources = metadata.get('data_sources', {})
                
                context_info += f"\n\n📊 PCB-Manager 시스템 종합 데이터 (수집시간: {crawl_time})"
                

                
                # 1. 메뉴1 (개요) 데이터
                menu1_data = context_data.get("menu1")
                if menu1_data:
                    context_info += f"\n\n📊 Menu1 PCB 대시보드 [{data_sources.get('menu1', 'unknown')} 데이터]:"
                    context_info += f"\n- 총 PCB: {menu1_data.get('total_pcbs', 0)}개"
                    context_info += f"\n- 예약된 검사: {menu1_data.get('total_scheduled', 0)}건"
                    context_info += f"\n- 검사 이력: {menu1_data.get('total_inspections', 0)}건"
                    context_info += f"\n- 전체 불량률: {menu1_data.get('overall_defect_rate', 0)}%"
                    context_info += f"\n- 총 검사: {menu1_data.get('total_inspected', 0)}건"
                    
                    # PCB 생산 데이터 (상세 정보 포함)
                    pcb_data = menu1_data.get('pcb_production_data', [])
                    if pcb_data:
                        context_info += f"\n\n🔧 PCB 생산 현황 (전체 {len(pcb_data)}개):"
                        for i, pcb in enumerate(pcb_data):
                            context_info += f"\n- {pcb.get('name')}: {pcb.get('size')}mm, {pcb.get('material')}, SMT {pcb.get('smtDensity')}, 면적 {pcb.get('boardArea')}mm²"
                            if pcb.get('description'):
                                context_info += f" ({pcb.get('description')})"
                            if pcb.get('production_line'):
                                context_info += f", 라인 {pcb.get('production_line')}"
                            if pcb.get('target_date'):
                                context_info += f", 목표일 {pcb.get('target_date')}"
                    

                    
                    # 예약된 검사
                    scheduled = menu1_data.get('scheduled_inspections', [])
                    if scheduled:
                        context_info += f"\n\n📅 예약된 검사 (최근 3건):"
                        for i, inspection in enumerate(scheduled[:3]):
                            context_info += f"\n- {inspection.get('pcbName')}: {inspection.get('type')} {inspection.get('count')}개 ({inspection.get('method')})"
                    
                    # 검사 이력
                    history = menu1_data.get('inspection_history', [])
                    if history:
                        context_info += f"\n\n📋 최근 검사 이력 (최근 2건):"
                        for i, inspection in enumerate(history[:2]):
                            defect_rate = round((inspection.get('defectiveCount', 0) / inspection.get('totalInspected', 1)) * 100, 1)
                            context_info += f"\n- {inspection.get('pcbName')}: {inspection.get('passedCount')}개 합격, {inspection.get('defectiveCount')}개 불합격 (불량률: {defect_rate}%)"
                    
                    # 재질별 통계
                    material_stats = menu1_data.get('material_stats', {})
                    if material_stats:
                        context_info += f"\n\n🏗️ 재질별 PCB 분포:"
                        for material, count in material_stats.items():
                            context_info += f"\n- {material}: {count}개"
                    
                    # SMT 밀도별 통계
                    smt_stats = menu1_data.get('smt_density_stats', {})
                    if smt_stats:
                        context_info += f"\n\n⚡ SMT 밀도별 분포:"
                        for density, count in smt_stats.items():
                            context_info += f"\n- {density}: {count}개"
                    
                    # 알림
                    notifications = menu1_data.get('notifications', [])
                    if notifications:
                        context_info += f"\n\n⚠️ 최근 알림:"
                        for i, notif in enumerate(notifications[:2]):
                            severity_icon = "🟡" if notif.get('severity') == 'medium' else "🔵"
                            context_info += f"\n- {severity_icon} {notif.get('message')}"
                    
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
                    context_info += f"\n\n🔍 검사 관리 (메뉴2) [{data_sources.get('menu2', 'unknown')} 데이터]:"
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
                    context_info += f"\n\n📈 불량 분석 (메뉴3) [{data_sources.get('menu3', 'unknown')} 데이터]:"
                    context_info += f"\n- 총 검사: {menu3_data.get('total_inspections', 0)}건"
                    context_info += f"\n- 총 불량: {menu3_data.get('total_defects', 0)}개"
                    context_info += f"\n- 총 불량 인스턴스: {menu3_data.get('total_defect_instances', 0)}개"
                    context_info += f"\n- 평균 불량률: {menu3_data.get('average_defect_rate', 0)}%"
                    context_info += f"\n- 목표 불량률: {menu3_data.get('target_defect_rate', 0)}%"
                    
                    # 구체적인 PCB 정보 추가
                    top_defective_pcbs = menu3_data.get('top_defective_pcbs', [])
                    if top_defective_pcbs:
                        context_info += f"\n\n🔍 상위 불량 PCB 정보:"
                        for pcb in top_defective_pcbs[:3]:  # 상위 3개만 표시
                            pcb_name = pcb.get('pcb_name', pcb.get('name', 'Unknown'))
                            defect_rate = pcb.get('defect_rate', 0)
                            defect_count = pcb.get('defect_count', 0)
                            total_inspections = pcb.get('total_inspections', 0)
                            context_info += f"\n- {pcb_name}: 불량률 {defect_rate}% (불량 {defect_count}개/총 {total_inspections}개)"
                    
                    # 불량 유형별 분포 차트 데이터 (중요!)
                    defect_types_chart = menu3_data.get('defect_types_chart', [])
                    if defect_types_chart and isinstance(defect_types_chart, list) and len(defect_types_chart) > 0:
                        context_info += f"\n\n📊 불량 유형별 분포 차트 데이터 (상세):"
                        context_info += f"\n- 총 불량 유형: {len(defect_types_chart)}개"
                        context_info += f"\n- 총 불량 인스턴스: {menu3_data.get('total_defect_instances', 0)}개"
                        
                        # 상위 5개 불량 유형 상세 정보
                        for i, defect in enumerate(defect_types_chart[:5]):
                            defect_type = defect.get('type', 'Unknown')
                            count = defect.get('count', 0)
                            percentage = defect.get('percentage', 0)
                            color = defect.get('color', '#6b7280')
                            rank_icon = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "📊"
                            context_info += f"\n- {rank_icon} {defect_type}: {count}개 ({percentage}%) - 색상: {color}"
                        
                        # 전체 불량 유형 요약
                        if len(defect_types_chart) > 5:
                            remaining_count = sum(d.get('count', 0) for d in defect_types_chart[5:])
                            remaining_percentage = sum(d.get('percentage', 0) for d in defect_types_chart[5:])
                            context_info += f"\n- 📋 기타 {len(defect_types_chart) - 5}개 유형: {remaining_count}개 ({remaining_percentage:.1f}%)"
                    
                    # PCB별 불량 유형 분포 정보 (개선된 버전)
                    pcb_defect_rates = menu3_data.get('pcb_defect_rates', [])
                    if pcb_defect_rates:
                        context_info += f"\n\n🔍 PCB별 불량 유형 분포 (상위 3개):"
                        for i, pcb in enumerate(pcb_defect_rates[:3]):
                            pcb_name = pcb.get('pcb_name', 'Unknown')
                            defect_rate = pcb.get('defect_rate', 0)
                            defect_types = pcb.get('defect_types', [])
                            total_instances = pcb.get('total_defect_instances', 0)
                            
                            rank_icon = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
                            context_info += f"\n- {rank_icon} {pcb_name} (불량률: {defect_rate}%, 총 {total_instances}개 불량):"
                            
                            # 해당 PCB의 상위 5개 불량 유형
                            for j, defect in enumerate(defect_types[:5]):
                                defect_type = defect.get('type', 'Unknown')
                                count = defect.get('count', 0)
                                percentage = defect.get('percentage', 0)
                                defect_icon = "🔴" if j == 0 else "🟡" if j == 1 else "🟢" if j == 2 else "🔵" if j == 3 else "🟣"
                                context_info += f"\n  {defect_icon} {defect_type}: {count}개 ({percentage}%)"
                            
                            # 해당 PCB의 전체 불량 현황
                            total_inspections = pcb.get('total_inspections', 0)
                            defect_count = pcb.get('defect_count', 0)
                            context_info += f"\n  📊 검사: {total_inspections}건, 불량: {defect_count}건"
                    
                    # 일별 불량률 추이 데이터 (중요!)
                    daily_defect_rates = menu3_data.get('daily_defect_rates', [])
                    if daily_defect_rates and isinstance(daily_defect_rates, list) and len(daily_defect_rates) > 0:
                        context_info += f"\n\n📈 일별 불량률 추이 (최근 7일):"
                        context_info += f"\n- 총 데이터 포인트: {len(daily_defect_rates)}일"
                        
                        # 일별 상세 데이터
                        for daily_data in daily_defect_rates:
                            date = daily_data.get('date', 'Unknown')
                            day_kr = daily_data.get('day_kr', 'Unknown')
                            inspections = daily_data.get('inspections', 0)
                            defects = daily_data.get('defects', 0)
                            rate = daily_data.get('rate', 0)
                            context_info += f"\n- {date} ({day_kr}): 검사 {inspections}건, 불량 {defects}건, 불량률 {rate}%"
                        
                        # 통계 요약
                        rates = [d.get('rate', 0) for d in daily_defect_rates]
                        if rates:
                            max_rate = max(rates)
                            min_rate = min(rates)
                            avg_rate = sum(rates) / len(rates)
                            target_rate = menu3_data.get('target_defect_rate', 5.0)
                            above_target_days = len([r for r in rates if r > target_rate])
                            
                            context_info += f"\n\n📊 일별 불량률 통계:"
                            context_info += f"\n- 최고 불량률: {max_rate}%"
                            context_info += f"\n- 최저 불량률: {min_rate}%"
                            context_info += f"\n- 평균 불량률: {avg_rate:.1f}%"
                            context_info += f"\n- 목표 초과 일수: {above_target_days}일 (목표: {target_rate}%)"
                            
                            # 추세 분석
                            if len(rates) >= 2:
                                first_half_avg = sum(rates[:len(rates)//2]) / (len(rates)//2)
                                second_half_avg = sum(rates[len(rates)//2:]) / (len(rates) - len(rates)//2)
                                
                                if second_half_avg > first_half_avg:
                                    trend = "상승"
                                    trend_icon = "📈"
                                elif second_half_avg < first_half_avg:
                                    trend = "하락"
                                    trend_icon = "📉"
                                else:
                                    trend = "안정"
                                    trend_icon = "➡️"
                                
                                context_info += f"\n- 추세: {trend_icon} {trend} (전반부 평균: {first_half_avg:.1f}%, 후반부 평균: {second_half_avg:.1f}%)"
                    
                    # 하위 호환성을 위한 기존 불량 유형 정보
                    defect_types = menu3_data.get('defect_types', {})
                    if defect_types and isinstance(defect_types, dict):
                        context_info += f"\n\n📊 기존 불량 유형별 분포:"
                        # 상위 3개 불량 유형 찾기
                        sorted_defects = sorted(defect_types.items(), key=lambda x: x[1], reverse=True)[:3]
                        for defect_name, defect_count in sorted_defects:
                            context_info += f"\n- {defect_name}: {defect_count}개"
                
                # 4. 인벤토리 데이터 (기본 부품 재고 정보만)
                inventory_data = context_data.get("inventory")
                if inventory_data:
                    context_info += f"\n\n📦 부품 재고 (인벤토리) [{data_sources.get('inventory', 'unknown')} 데이터]:"
                    context_info += f"\n- 총 부품: {inventory_data.get('total_items', 0)}개"
                    context_info += f"\n- 재고 부족: {inventory_data.get('low_stock_items', 0)}개"
                    context_info += f"\n- 긴급 부족: {inventory_data.get('critical_items', 0)}개"
                    context_info += f"\n- 습도 민감 자재: {inventory_data.get('moisture_sensitive_items', 0)}개"
                    
                    total_value = inventory_data.get('total_value', 0)
                    if total_value > 0:
                        context_info += f"\n- 총 재고 가치: {total_value:,}원"
                
                # 5. MES 데이터 (공장 환경 모니터링) - 새로운 구조 반영
                mes_data = context_data.get("mes")
                if mes_data:
                    context_info += f"\n\n🏭 MES 공장 환경 모니터링 [{data_sources.get('mes', 'unknown')} 데이터]:"
                    
                    # 현재 환경 상태
                    current_env = mes_data.get('current_environment', {})
                    if current_env:
                        context_info += f"\n\n🌡️ 현재 환경 상태:"
                        context_info += f"\n- 온도: {current_env.get('temperature_c', 0)}°C"
                        context_info += f"\n- 습도: {current_env.get('humidity_percent', 0)}%"
                        context_info += f"\n- PM2.5: {current_env.get('pm25_ug_m3', 0)}㎍/m³"
                        context_info += f"\n- PM10: {current_env.get('pm10_ug_m3', 0)}㎍/m³"
                        context_info += f"\n- CO₂: {current_env.get('co2_ppm', 0)}ppm"
                    
                    # 환경 상태 분석
                    env_status = mes_data.get('environment_status', {})
                    if env_status:
                        context_info += f"\n\n⚠️ 환경 상태 분석:"
                        for sensor, status in env_status.items():
                            status_icon = "🟢" if status == "normal" else "🟡" if status == "warning" else "🔴"
                            context_info += f"\n- {sensor}: {status_icon} {status}"
                    
                    # 새로운 습도 민감 자재 구조
                    materials = mes_data.get('moisture_sensitive_materials', [])
                    if materials:
                        context_info += f"\n\n💧 습도 민감 자재 모니터링 (새로운 구조):"
                        context_info += f"\n- 총 자재: {len(materials)}개"
                        context_info += f"\n- 경고 자재: {mes_data.get('warning_materials', 0)}개"
                        
                        for material in materials:
                            name = material.get('name', 'Unknown')
                            current_humidity = material.get('currentHumidity', 0)
                            optimal_range = material.get('optimalRange', '0-100%')
                            status = material.get('status', 'normal')
                            warehouse = material.get('warehouse', 'Unknown')
                            
                            # 상태 아이콘
                            status_icon = "🟢" if status == "normal" else "🟡" if status == "warning" else "🔴"
                            
                            context_info += f"\n- {status_icon} {name} ({warehouse}):"
                            context_info += f"\n  현재 습도: {current_humidity}% (적정: {optimal_range})"
                            context_info += f"\n  상태: {status}"
                    
                    # 환경 통계 데이터 (새로운 구조)
                    temperature_stats = mes_data.get('temperature_stats', {})
                    humidity_stats = mes_data.get('humidity_stats', {})
                    pm25_stats = mes_data.get('pm25_stats', {})
                    pm10_stats = mes_data.get('pm10_stats', {})
                    co2_stats = mes_data.get('co2_stats', {})
                    
                    if any([temperature_stats, humidity_stats, pm25_stats, pm10_stats, co2_stats]):
                        context_info += f"\n\n📊 환경 통계 데이터:"
                        
                        if temperature_stats:
                            context_info += f"\n- 🌡️ 온도: 현재 {temperature_stats.get('current', 0)}°C, 평균 {temperature_stats.get('average', 0)}°C"
                            context_info += f"\n  범위: {temperature_stats.get('min', 0)}°C ~ {temperature_stats.get('max', 0)}°C"
                            context_info += f"\n  트렌드: {temperature_stats.get('trend', 'unknown')}"
                        
                        if humidity_stats:
                            context_info += f"\n- 💧 습도: 현재 {humidity_stats.get('current', 0)}%, 평균 {humidity_stats.get('average', 0)}%"
                            context_info += f"\n  범위: {humidity_stats.get('min', 0)}% ~ {humidity_stats.get('max', 0)}%"
                            context_info += f"\n  트렌드: {humidity_stats.get('trend', 'unknown')}"
                        
                        if pm25_stats:
                            context_info += f"\n- 🫧 PM2.5: 현재 {pm25_stats.get('current', 0)}㎍/m³, 평균 {pm25_stats.get('average', 0)}㎍/m³"
                            context_info += f"\n  범위: {pm25_stats.get('min', 0)}㎍/m³ ~ {pm25_stats.get('max', 0)}㎍/m³"
                            context_info += f"\n  트렌드: {pm25_stats.get('trend', 'unknown')}"
                        
                        if pm10_stats:
                            context_info += f"\n- 🌫️ PM10: 현재 {pm10_stats.get('current', 0)}㎍/m³, 평균 {pm10_stats.get('average', 0)}㎍/m³"
                            context_info += f"\n  범위: {pm10_stats.get('min', 0)}㎍/m³ ~ {pm10_stats.get('max', 0)}㎍/m³"
                            context_info += f"\n  트렌드: {pm10_stats.get('trend', 'unknown')}"
                        
                        if co2_stats:
                            context_info += f"\n- 🌬️ CO₂: 현재 {co2_stats.get('current', 0)}ppm, 평균 {co2_stats.get('average', 0)}ppm"
                            context_info += f"\n  범위: {co2_stats.get('min', 0)}ppm ~ {co2_stats.get('max', 0)}ppm"
                            context_info += f"\n  트렌드: {co2_stats.get('trend', 'unknown')}"
                    
                    # 환경 데이터 이력
                    env_history = mes_data.get('environment_history', [])
                    if env_history:
                        context_info += f"\n\n📊 환경 데이터 이력 (최근 {len(env_history)}시간):"
                        for i, record in enumerate(env_history[:3]):  # 최근 3개만
                            context_info += f"\n- {record.get('time')}: 온도 {record.get('temperature_c')}°C, 습도 {record.get('humidity_percent')}%, PM2.5 {record.get('pm25_ug_m3')}㎍/m³"
                    
                    # 환경 통계
                    temp_stats = mes_data.get('temperature_stats', {})
                    humidity_stats = mes_data.get('humidity_stats', {})
                    if temp_stats and humidity_stats:
                        context_info += f"\n\n📈 환경 데이터 통계:"
                        context_info += f"\n- 온도: 현재 {temp_stats.get('current')}°C, 평균 {temp_stats.get('average')}°C, 범위 {temp_stats.get('min')}°C~{temp_stats.get('max')}°C"
                        context_info += f"\n- 습도: 현재 {humidity_stats.get('current')}%, 평균 {humidity_stats.get('average')}%, 범위 {humidity_stats.get('min')}%~{humidity_stats.get('max')}%"
                        context_info += f"\n- 온도 추세: {temp_stats.get('trend')}"
                        context_info += f"\n- 습도 추세: {humidity_stats.get('trend')}"
                
                # 현재 메뉴 강조
                menu_names = {
                    "menu1": "PCB 모니터링",
                    "menu2": "불량검사", 
                    "menu3": "불량관리",
                    "menu4": "부품재고관리",
                    "mes": "공정환경 모니터링"
                }
                current_menu_name = menu_names.get(current_menu, current_menu)
                context_info += f"\n\n📍 현재 위치: {current_menu_name} 메뉴"
                
            except Exception as e:
                print(f"❌ 컨텍스트 정보 구성 오류: {e}")
                traceback.print_exc()
                context_info = f"\n\n⚠️ 데이터 구성 중 오류가 발생했습니다: {str(e)}"
        else:
            context_info = "\n\n⚠️ 실시간 데이터를 가져올 수 없습니다."
        
        # Gemini에 전송할 프롬프트 구성 (개선된 버전)
        full_prompt = f"""{menu_prompt['system']}

중요한 응답 규칙:
1. 사용자가 물어본 것에 정확하게 답변하세요
2. 질문과 관련 없는 정보는 포함하지 마세요  
3. 답변은 적절한 수준의 상세함으로 작성하세요 (너무 간결하지도, 너무 길지도 않게)
4. 구체적인 수치와 PCB 정보가 있으면 포함하세요
5. PCB 이름이나 구체적인 정보를 물어보면 해당 정보를 찾아서 답변하세요
6. 데이터 소스 정보도 필요시 언급하세요 (API 데이터인지 기본 데이터인지)

7. 불량률 관련 질문 규칙 (매우 중요):
   - 불량률, 불량 분석, 품질 관련 질문은 반드시 Menu3(분석) 데이터만 사용하세요
   - Menu1의 overall_defect_rate는 사용하지 말고, Menu3의 average_defect_rate를 사용하세요
   - 불량 유형별 분포, 일별 불량률 추이 등은 Menu3의 데이터만 활용하세요
   - Menu1과 Menu3의 불량률이 다를 수 있으니, Menu3가 더 정확한 분석 데이터입니다

8. 데이터 관련 응답 규칙 (매우 중요):
   - "데이터가 발견되지 않았습니다", "해당 데이터가 필요합니다" 등의 메시지는 절대 출력하지 마세요
   - 실제 크롤링된 데이터만 사용하여 답변하세요
   - 데이터가 없는 경우에는 해당 내용을 언급하지 말고, 있는 데이터만으로 답변하세요
   - 사용자가 특정 PCB에 대해 질문하면, 해당 PCB의 불량 정보는 Menu3 데이터만 사용하세요

{context_info}

사용자 질문: {user_message}

위의 실시간 데이터를 바탕으로 사용자 질문에 정확하고 적절한 수준의 상세함으로 답변해주세요. 불량률 관련 질문은 Menu3 데이터만 사용하고, 데이터가 없는 경우에는 해당 내용을 언급하지 말고, 있는 데이터만으로 답변하세요."""
        
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
                
                response = base_response + f"""📊 PCB 생산 관리 현황 (데이터 소스: {data_source})

🏭 총 PCB 관리 현황:
- 전체 PCB: {total_pcbs}개
- 완료된 PCB: {completed}개
- 평균 진행률: {avg_progress}%
- 생산 효율성: {efficiency}%"""

                # 예약된 검사 일정
                if scheduled_inspections:
                    response += f"\n\n📅 예약된 검사 일정: {len(scheduled_inspections)}건"
                    for inspection in scheduled_inspections[:3]:
                        pcb_name = inspection.get('pcbName', 'Unknown')
                        insp_type = inspection.get('type', 'Unknown')
                        count = inspection.get('count', 0)
                        response += f"\n- {pcb_name}: {insp_type} {count}개"
                

                
                # 긴급 알림
                if emergency_alerts:
                    response += f"\n\n🚨 긴급 알림: {len(emergency_alerts)}건"
                    for alert in emergency_alerts[:2]:
                        message = alert.get('message', 'Unknown')
                        severity = alert.get('severity', 'medium')
                        response += f"\n- [{severity.upper()}] {message}"
                
                # 알림 현황
                if alert_trend:
                    total_today = alert_trend.get('total_today', 0)
                    response += f"\n\n📊 오늘 발생한 알림: {total_today}건"
                
                response += "\n\n더 자세한 정보가 필요하시면 구체적으로 질문해주세요."
            else:
                response = base_response + "생산 관리 데이터를 확인하고 있습니다. 잠시 후 다시 시도해주세요."
            
        elif menu_id == "menu2":
            if current_data:
                total_inspections = current_data.get('total_inspections', 0)
                completion_rate = current_data.get('completion_rate', 0)
                today_inspections = current_data.get('today_inspections', 0)
                
                response = base_response + f"""🔍 검사 관리 현황 (데이터 소스: {data_source})

🧪 검사 현황:
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
                total_defect_instances = current_data.get('total_defect_instances', 0)
                target_rate = current_data.get('target_defect_rate', 0)
                
                response = base_response + f"""📈 불량 분석 현황 (데이터 소스: {data_source})

📊 불량 통계:
- 평균 불량률: {avg_rate}%
- 목표 불량률: {target_rate}%
- 총 불량 PCB: {total_defects}개
- 총 검사: {total_inspections}건
- 총 불량 인스턴스: {total_defect_instances}개"""
                
                # 불량 유형별 분포 차트 데이터 추가
                defect_types_chart = current_data.get('defect_types_chart', [])
                if defect_types_chart:
                    response += f"\n\n📊 불량 유형별 분포:"
                    for defect in defect_types_chart[:5]:  # 상위 5개만
                        defect_type = defect.get('type', 'Unknown')
                        count = defect.get('count', 0)
                        percentage = defect.get('percentage', 0)
                        response += f"\n- {defect_type}: {count}개 ({percentage}%)"
                
                # 상위 불량 PCB 정보 추가
                top_pcbs = current_data.get('top_defective_pcbs', [])
                if top_pcbs:
                    response += f"\n\n🏆 상위 불량 PCB:"
                    for i, pcb in enumerate(top_pcbs[:3], 1):
                        pcb_name = pcb.get('pcb_name', pcb.get('pcb_id', 'Unknown'))
                        defect_rate = pcb.get('defect_rate', 0)
                        defect_count = pcb.get('defect_count', 0)
                        total_pcb_inspections = pcb.get('total_inspections', 0)
                        response += f"\n{i}위: {pcb_name} - 불량률 {defect_rate}% (불량 {defect_count}개/총 {total_pcb_inspections}개)"
                
                response += "\n\n더 자세한 불량 분석이 필요하시면 구체적으로 질문해주세요."
            else:
                response = base_response + "불량 분석 데이터를 확인하고 있습니다. 잠시 후 다시 시도해주세요."
                
        elif menu_id == "menu4":
            if current_data:
                total_items = current_data.get('total_items', 0)
                low_stock = current_data.get('low_stock_items', 0)
                critical_items = current_data.get('critical_items', 0)
                total_value = current_data.get('total_value', 0)
                
                response = base_response + f"""📦 부품재고관리 현황 (데이터 소스: {data_source})

🗂️ 재고 통계:
- 총 부품 종류: {total_items}개
- 재고 부족: {low_stock}개
- 긴급 부족: {critical_items}개"""
                
                if total_value > 0:
                    response += f"\n- 총 재고 가치: {total_value:,}원"
                
                response += "\n\n더 자세한 재고 정보가 필요하시면 구체적으로 질문해주세요."
            else:
                response = base_response + "부품재고관리 데이터를 확인하고 있습니다. 잠시 후 다시 시도해주세요."
                
        elif menu_id == "mes":
            if current_data:
                temp = current_data.get('temperature', 0)
                humidity = current_data.get('humidity', 0)
                production_count = current_data.get('production_count', 0)
                quality_score = current_data.get('quality_score', 0)
                
                response = base_response + f"""🏭 공정환경 모니터링 현황 (데이터 소스: {data_source})

🌡️ 환경 모니터링:
- 현재 온도: {temp}°C
- 현재 습도: {humidity}%

📊 생산 현황:
- 현재 생산량: {production_count}개
- 품질 지표: {quality_score}%

더 자세한 공정환경 모니터링 정보가 필요하시면 구체적으로 질문해주세요."""
            else:
                response = base_response + "공정환경 모니터링 데이터를 확인하고 있습니다. 잠시 후 다시 시도해주세요."
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
            "inventory": "menu4",
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

@chat_bp.route('/moisture-monitoring', methods=['GET'])
def get_moisture_monitoring():
    """습도 민감 자재 모니터링 전용 API 엔드포인트"""
    try:
        print("💧 습도 민감 자재 모니터링 데이터 요청...")
        
        # MES 데이터에서 습도 민감 자재 정보만 추출
        mes_data = get_menu_data_sync("mes")
        
        if not mes_data:
            return jsonify({
                "success": False,
                "error": "MES 데이터를 가져올 수 없습니다.",
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # 습도 민감 자재 데이터 추출
        moisture_materials = mes_data.get('moisture_sensitive_materials', [])
        current_environment = mes_data.get('current_environment', {})
        environment_status = mes_data.get('environment_status', {})
        
        # 자재별 상태 분석
        material_status = []
        warning_count = 0
        
        for material in moisture_materials:
            name = material.get('name', 'Unknown')
            current_humidity = material.get('currentHumidity', 0)
            optimal_range = material.get('optimalRange', '0-100%')
            status = material.get('status', 'normal')
            warehouse = material.get('warehouse', 'Unknown')
            description = material.get('description', '')
            
            # 적정 범위 파싱
            try:
                range_parts = optimal_range.replace('%', '').split('-')
                min_humidity = float(range_parts[0]) if len(range_parts) > 0 else 0
                max_humidity = float(range_parts[1]) if len(range_parts) > 1 else 100
                
                # 상태 판단
                if current_humidity < min_humidity:
                    humidity_status = 'low'
                    warning_count += 1
                elif current_humidity > max_humidity:
                    humidity_status = 'high'
                    warning_count += 1
                else:
                    humidity_status = 'normal'
                    
            except:
                humidity_status = 'unknown'
            
            material_status.append({
                'name': name,
                'current_humidity': current_humidity,
                'optimal_range': optimal_range,
                'status': status,
                'humidity_status': humidity_status,
                'warehouse': warehouse,
                'needs_attention': humidity_status != 'normal'
            })
        
        # 환경 상태 요약
        environment_summary = {
            'current_temperature': current_environment.get('temperature_c', 0),
            'current_humidity': current_environment.get('humidity_percent', 0),
            'temperature_status': environment_status.get('temperature', 'normal'),
            'humidity_status': environment_status.get('humidity', 'normal'),
            'overall_status': 'warning' if warning_count > 0 else 'normal'
        }
        
        return jsonify({
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "material_count": len(moisture_materials),
                "warning_count": warning_count,
                "environment_summary": environment_summary,
                "materials": material_status,
                "data_source": mes_data.get('data_source', 'unknown')
            }
        })
        
    except Exception as e:
        print(f"❌ 습도 모니터링 API 오류: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@chat_bp.route('/environment-status', methods=['GET'])
def get_environment_status():
    """공장 환경 상태 전용 API 엔드포인트"""
    try:
        print("🏭 공장 환경 상태 데이터 요청...")
        
        # MES 데이터에서 환경 정보만 추출
        mes_data = get_menu_data_sync("mes")
        
        if not mes_data:
            return jsonify({
                "success": False,
                "error": "MES 데이터를 가져올 수 없습니다.",
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # 환경 통계 데이터 추출
        current_environment = mes_data.get('current_environment', {})
        environment_history = mes_data.get('environment_history', [])
        
        # 통계 데이터
        temperature_stats = mes_data.get('temperature_stats', {})
        humidity_stats = mes_data.get('humidity_stats', {})
        pm25_stats = mes_data.get('pm25_stats', {})
        pm10_stats = mes_data.get('pm10_stats', {})
        co2_stats = mes_data.get('co2_stats', {})
        
        # 환경 상태 분석
        environment_analysis = {
            'temperature': {
                'current': current_environment.get('temperature_c', 0),
                'average': temperature_stats.get('average', 0),
                'min': temperature_stats.get('min', 0),
                'max': temperature_stats.get('max', 0),
                'trend': temperature_stats.get('trend', 'unknown'),
                'status': 'normal' if 18 <= current_environment.get('temperature_c', 0) <= 25 else 'warning'
            },
            'humidity': {
                'current': current_environment.get('humidity_percent', 0),
                'average': humidity_stats.get('average', 0),
                'min': humidity_stats.get('min', 0),
                'max': humidity_stats.get('max', 0),
                'trend': humidity_stats.get('trend', 'unknown'),
                'status': 'normal' if current_environment.get('humidity_percent', 0) < 70 else 'warning'
            },
            'pm25': {
                'current': current_environment.get('pm25_ug_m3', 0),
                'average': pm25_stats.get('average', 0),
                'min': pm25_stats.get('min', 0),
                'max': pm25_stats.get('max', 0),
                'trend': pm25_stats.get('trend', 'unknown'),
                'status': 'normal' if current_environment.get('pm25_ug_m3', 0) < 50 else 'warning'
            },
            'pm10': {
                'current': current_environment.get('pm10_ug_m3', 0),
                'average': pm10_stats.get('average', 0),
                'min': pm10_stats.get('min', 0),
                'max': pm10_stats.get('max', 0),
                'trend': pm10_stats.get('trend', 'unknown'),
                'status': 'normal' if current_environment.get('pm10_ug_m3', 0) < 100 else 'warning'
            },
            'co2': {
                'current': current_environment.get('co2_ppm', 0),
                'average': co2_stats.get('average', 0),
                'min': co2_stats.get('min', 0),
                'max': co2_stats.get('max', 0),
                'trend': co2_stats.get('trend', 'unknown'),
                'status': 'normal' if current_environment.get('co2_ppm', 0) < 1000 else 'warning'
            }
        }
        
        # 전체 환경 상태 판단
        warning_count = sum(1 for env in environment_analysis.values() if env['status'] == 'warning')
        overall_status = 'warning' if warning_count > 0 else 'normal'
        
        # 최근 환경 이력 (최근 3시간)
        recent_history = environment_history[:3] if environment_history else []
        
        return jsonify({
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "overall_status": overall_status,
                "warning_count": warning_count,
                "environment_analysis": environment_analysis,
                "recent_history": recent_history,
                "data_source": mes_data.get('data_source', 'unknown')
            }
        })
        
    except Exception as e:
        print(f"❌ 환경 상태 API 오류: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@chat_bp.route('/moisture-chat', methods=['POST'])
def moisture_chat():
    """습도 민감 자재 모니터링 전용 챗봇 API"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({
                "success": False,
                "error": "메시지가 필요합니다.",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        print(f"💧 습도 모니터링 챗봇 요청: {user_message}")
        
        # MES 데이터 가져오기
        mes_data = get_menu_data_sync("mes")
        
        if not mes_data:
            return jsonify({
                "success": False,
                "error": "MES 데이터를 가져올 수 없습니다.",
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # 습도 민감 자재 데이터 분석
        moisture_materials = mes_data.get('moisture_sensitive_materials', [])
        current_environment = mes_data.get('current_environment', {})
        
        # 사용자 메시지 분석 및 응답 생성
        response = generate_moisture_monitoring_response(user_message, moisture_materials, current_environment, mes_data)
        
        return jsonify({
            "success": True,
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "data_source": mes_data.get('data_source', 'unknown')
        })
        
    except Exception as e:
        print(f"❌ 습도 모니터링 챗봇 오류: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

def generate_moisture_monitoring_response(user_message, moisture_materials, current_environment, mes_data):
    """습도 민감 자재 모니터링 전용 응답 생성"""
    try:
        user_message_lower = user_message.lower()
        
        # 현재 환경 상태
        current_temp = current_environment.get('temperature_c', 0)
        current_humidity = current_environment.get('humidity_percent', 0)
        
        # 경고가 필요한 자재들
        warning_materials = []
        normal_materials = []
        
        for material in moisture_materials:
            name = material.get('name', 'Unknown')
            current_humidity_mat = material.get('currentHumidity', 0)
            optimal_range = material.get('optimalRange', '0-100%')
            status = material.get('status', 'normal')
            warehouse = material.get('warehouse', 'Unknown')
            
            # 적정 범위 파싱
            try:
                range_parts = optimal_range.replace('%', '').split('-')
                min_humidity = float(range_parts[0]) if len(range_parts) > 0 else 0
                max_humidity = float(range_parts[1]) if len(range_parts) > 1 else 100
                
                if current_humidity_mat < min_humidity or current_humidity_mat > max_humidity:
                    warning_materials.append({
                        'name': name,
                        'current': current_humidity_mat,
                        'optimal': optimal_range,
                        'warehouse': warehouse,
                        'issue': 'low' if current_humidity_mat < min_humidity else 'high'
                    })
                else:
                    normal_materials.append({
                        'name': name,
                        'current': current_humidity_mat,
                        'optimal': optimal_range,
                        'warehouse': warehouse
                    })
            except:
                normal_materials.append({
                    'name': name,
                    'current': current_humidity_mat,
                    'optimal': optimal_range,
                    'warehouse': warehouse
                })
        
        # 응답 생성
        if "상태" in user_message_lower or "현황" in user_message_lower:
            response = f"🏭 **공장 환경 모니터링 현황**\n\n"
            response += f"🌡️ **현재 환경 상태**\n"
            response += f"• 온도: {current_temp}°C\n"
            response += f"• 습도: {current_humidity}%\n\n"
            
            response += f"💧 **습도 민감 자재 현황**\n"
            response += f"• 총 자재: {len(moisture_materials)}개\n"
            response += f"• 정상 상태: {len(normal_materials)}개\n"
            response += f"• 주의 필요: {len(warning_materials)}개\n\n"
            
            if warning_materials:
                response += f"⚠️ **주의가 필요한 자재**\n"
                for material in warning_materials:
                    issue_text = "습도 부족" if material['issue'] == 'low' else "습도 과다"
                    response += f"• {material['name']} ({material['warehouse']}): {material['current']}% (적정: {material['optimal']}) - {issue_text}\n"
            
            if normal_materials:
                response += f"\n✅ **정상 상태 자재**\n"
                for material in normal_materials[:3]:  # 상위 3개만
                    response += f"• {material['name']} ({material['warehouse']}): {material['current']}% (적정: {material['optimal']})\n"
        
        elif "경고" in user_message_lower or "주의" in user_message_lower or "문제" in user_message_lower:
            if warning_materials:
                response = f"⚠️ **습도 관리 주의 자재**\n\n"
                response += f"현재 {len(warning_materials)}개의 자재가 적정 습도 범위를 벗어났습니다:\n\n"
                
                for material in warning_materials:
                    issue_text = "습도 부족" if material['issue'] == 'low' else "습도 과다"
                    response += f"🔴 **{material['name']}** ({material['warehouse']})\n"
                    response += f"• 현재 습도: {material['current']}%\n"
                    response += f"• 적정 범위: {material['optimal']}\n"
                    response += f"• 문제: {issue_text}\n\n"
                
                response += f"💡 **권장 조치사항**\n"
                response += f"• 습도 조절 장비 점검\n"
                response += f"• 창고 환기 시스템 확인\n"
                response += f"• 자재별 보호 장치 점검\n"
            else:
                response = f"✅ **모든 자재가 정상 상태입니다**\n\n"
                response += f"현재 습도 민감 자재 {len(moisture_materials)}개 모두 적정 습도 범위 내에 있습니다.\n"
                response += f"• 현재 공장 습도: {current_humidity}%\n"
                response += f"• 환경 상태: 양호"
        
        elif "자재" in user_message_lower or "부품" in user_message_lower:
            response = f"📦 **습도 민감 자재 목록**\n\n"
            response += f"총 {len(moisture_materials)}개의 자재가 모니터링되고 있습니다:\n\n"
            
            for material in moisture_materials:
                name = material.get('name', 'Unknown')
                current_humidity_mat = material.get('currentHumidity', 0)
                optimal_range = material.get('optimalRange', '0-100%')
                status = material.get('status', 'normal')
                warehouse = material.get('warehouse', 'Unknown')
                
                status_icon = "🟢" if status == "normal" else "🟡" if status == "warning" else "🔴"
                response += f"{status_icon} **{name}** ({warehouse})\n"
                response += f"• 현재 습도: {current_humidity_mat}%\n"
                response += f"• 적정 범위: {optimal_range}\n"
                response += f"• 상태: {status}\n"
                response += "\n"
        
        elif "환경" in user_message_lower or "온도" in user_message_lower:
            # 환경 통계 데이터 활용
            temperature_stats = mes_data.get('temperature_stats', {})
            humidity_stats = mes_data.get('humidity_stats', {})
            
            response = f"🌍 **공장 환경 상태 분석**\n\n"
            response += f"🌡️ **온도 현황**\n"
            response += f"• 현재: {current_temp}°C\n"
            if temperature_stats:
                response += f"• 평균: {temperature_stats.get('average', 0)}°C\n"
                response += f"• 범위: {temperature_stats.get('min', 0)}°C ~ {temperature_stats.get('max', 0)}°C\n"
                response += f"• 트렌드: {temperature_stats.get('trend', 'unknown')}\n"
            
            response += f"\n💧 **습도 현황**\n"
            response += f"• 현재: {current_humidity}%\n"
            if humidity_stats:
                response += f"• 평균: {humidity_stats.get('average', 0)}%\n"
                response += f"• 범위: {humidity_stats.get('min', 0)}% ~ {humidity_stats.get('max', 0)}%\n"
                response += f"• 트렌드: {humidity_stats.get('trend', 'unknown')}\n"
            
            response += f"\n📊 **전체 환경 상태**\n"
            response += f"• 습도 민감 자재: {len(moisture_materials)}개\n"
            response += f"• 주의 자재: {len(warning_materials)}개\n"
            response += f"• 환경 상태: {'⚠️ 주의 필요' if warning_materials else '✅ 양호'}"
        
        else:
            # 기본 응답
            response = f"💧 **습도 민감 자재 모니터링 시스템**\n\n"
            response += f"안녕하세요! 습도 민감 자재 모니터링 AI 어시스턴트입니다.\n\n"
            response += f"📊 **현재 상황 요약**\n"
            response += f"• 총 모니터링 자재: {len(moisture_materials)}개\n"
            response += f"• 정상 상태: {len(normal_materials)}개\n"
            response += f"• 주의 필요: {len(warning_materials)}개\n"
            response += f"• 현재 공장 습도: {current_humidity}%\n\n"
            
            response += f"💡 **질문 예시**\n"
            response += f"• '습도 민감 자재 상태 알려줘'\n"
            response += f"• '경고가 필요한 자재는?'\n"
            response += f"• '특정 자재 정보 알려줘'\n"
            response += f"• '환경 상태 분석해줘'"
        
        return response
        
    except Exception as e:
        print(f"❌ 습도 모니터링 응답 생성 오류: {e}")
        return "죄송합니다. 습도 모니터링 정보를 처리하는 중 오류가 발생했습니다."

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
                "/api/debug",
                "/api/moisture-monitoring",
                "/api/environment-status",
                "/api/moisture-chat"
            ]
        }
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500