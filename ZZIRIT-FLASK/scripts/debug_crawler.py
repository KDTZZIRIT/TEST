# full_data_debug.py - 전체 데이터 크롤링 디버깅 스크립트

import asyncio
import requests
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.external.crawler import crawler

async def debug_inventory_data():
    """인벤토리 데이터 크롤링 디버깅"""
    print("=" * 80)
    print("🔍 인벤토리 데이터 크롤링 디버깅 시작")
    print("=" * 80)
    
    # 1. 기본 API 테스트
    print("\n1️⃣ 기본 API 엔드포인트 테스트")
    endpoint_result = crawler.test_endpoint_sync("/api/user/pcb-parts")
    print("📊 테스트 결과:")
    for key, value in endpoint_result.items():
        if key not in ['sample_item', 'pagination_test']:
            print(f"  - {key}: {value}")
    
    # 샘플 데이터 표시
    if 'sample_item' in endpoint_result:
        print(f"\n📋 샘플 데이터:")
        sample = endpoint_result['sample_item']
        for key, value in sample.items():
            print(f"  - {key}: {value}")
    
    # 페이지네이션 테스트 결과
    if 'pagination_test' in endpoint_result:
        print(f"\n🔄 페이지네이션 테스트 결과:")
        pagination = endpoint_result['pagination_test']
        for key, value in pagination.items():
            print(f"  - {key}: {value}")
    
    # 2. 비동기 크롤링 테스트
    print(f"\n2️⃣ 비동기 크롤링 테스트")
    inventory_data = await crawler.crawl_menu4_data()
    
    if inventory_data:
        print(f"✅ 크롤링 성공!")
        print(f"📊 전체 통계:")
        print(f"  - 총 부품: {inventory_data.get('total_items', 0)}개")
        print(f"  - 재고 부족: {inventory_data.get('low_stock_items', 0)}개")
        print(f"  - 흡습 민감: {inventory_data.get('moisture_sensitive_items', 0)}개")
        print(f"  - 데이터 소스: {inventory_data.get('data_source', 'unknown')}")
        
        # 상세 부품 정보 확인
        parts_details = inventory_data.get('parts_details', [])
        if parts_details:
            print(f"\n📦 상세 부품 정보: {len(parts_details)}개")
            print("상위 5개 부품:")
            for i, part in enumerate(parts_details[:5], 1):
                print(f"  {i}. {part.get('part_id', 'Unknown')} - {part.get('product_name', 'Unknown')}")
                print(f"     제조사: {part.get('manufacturer', 'Unknown')}, 재고: {part.get('quantity', 0)}개")
        
        # 제조사별 통계
        manufacturer_stats = inventory_data.get('manufacturer_stats', {})
        if manufacturer_stats:
            print(f"\n🏭 제조사별 통계:")
            for manufacturer, count in sorted(manufacturer_stats.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  - {manufacturer}: {count}개")
        
        # 흡습 민감 부품 상세
        moisture_details = inventory_data.get('moisture_sensitive_details', [])
        if moisture_details:
            print(f"\n🌡️ 흡습 민감 부품: {len(moisture_details)}개")
            for i, part in enumerate(moisture_details[:3], 1):
                print(f"  {i}. {part.get('part_id', 'Unknown')} - {part.get('moisture_materials', 'Unknown')}")
    else:
        print(f"❌ 크롤링 실패")
    
    # 3. 특정 부품 검색 테스트
    print(f"\n3️⃣ 특정 부품 검색 테스트")
    test_part_ids = ["CL02A104K2NNNC", "CL02B102KP2NNNC", "CL02B102KP2NNNC"]
    
    if inventory_data and inventory_data.get('part_id_index'):
        part_index = inventory_data['part_id_index']
        for part_id in test_part_ids:
            if part_id in part_index:
                part_info = part_index[part_id]
                print(f"✅ {part_id} 발견:")
                print(f"  - 제품명: {part_info.get('product_name', 'Unknown')}")
                print(f"  - 제조사: {part_info.get('manufacturer', 'Unknown')}")
                print(f"  - 재고: {part_info.get('quantity', 0)}개")
                print(f"  - 흡습: {'O' if part_info.get('moisture_absorption') else 'X'}")
            else:
                print(f"❌ {part_id} 찾을 수 없음")
    
    print("\n" + "=" * 80)
    print("🔍 디버깅 완료")
    print("=" * 80)

def debug_direct_api_call():
    """직접 API 호출로 데이터 확인"""
    print("\n" + "=" * 80)
    print("🌐 직접 API 호출 테스트")
    print("=" * 80)
    
    try:
        url = "http://43.201.249.204:5000/api/user/pcb-parts"
        print(f"📡 URL: {url}")
        
        response = requests.get(url, timeout=30)
        print(f"📊 응답 상태: {response.status_code}")
        print(f"📄 Content-Type: {response.headers.get('content-type')}")
        print(f"📦 응답 크기: {len(response.content)} bytes")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ JSON 파싱 성공")
            print(f"📊 데이터 타입: {type(data)}")
            
            if isinstance(data, list):
                print(f"📋 배열 길이: {len(data)}개")
                if len(data) > 0:
                    first_item = data[0]
                    print(f"📦 첫 번째 항목 키: {list(first_item.keys())}")
                    
                    # 모든 part_id 목록 출력
                    part_ids = []
                    for item in data:
                        part_id = item.get('partId') or item.get('part_id') or item.get('id')
                        if part_id:
                            part_ids.append(str(part_id))
                    
                    print(f"📝 모든 Part ID 목록 ({len(part_ids)}개):")
                    for i, part_id in enumerate(part_ids, 1):
                        print(f"  {i:2d}. {part_id}")
                        
                    # 특정 부품 찾기 테스트
                    target_parts = ["CL02A104K2NNNC", "CL02B102KP2NNNC"]
                    print(f"\n🔍 특정 부품 검색:")
                    for target in target_parts:
                        found = False
                        for item in data:
                            item_part_id = str(item.get('partId', '') or item.get('part_id', '') or item.get('product', ''))
                            if target in item_part_id:
                                print(f"✅ {target} 발견: {item}")
                                found = True
                                break
                        if not found:
                            print(f"❌ {target} 찾을 수 없음")
            
            elif isinstance(data, dict):
                print(f"📊 dict 키: {list(data.keys())}")
                # dict 내부에 배열이 있는지 확인
                for key in ['data', 'items', 'results', 'parts']:
                    if key in data and isinstance(data[key], list):
                        print(f"📋 {key} 배열 길이: {len(data[key])}개")
        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            print(f"❌ 오류 내용: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ 직접 API 호출 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 직접 API 호출 테스트
    debug_direct_api_call()
    
    # 비동기 크롤링 테스트
    asyncio.run(debug_inventory_data())