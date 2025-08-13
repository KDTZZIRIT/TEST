import aiohttp
import asyncio
from datetime import datetime
import json
import re
import requests
from typing import Optional, Dict, Any

class DataCrawler:
    """각 메뉴의 데이터를 크롤링하는 클래스 (개선된 버전)"""
    
    def __init__(self, base_url="http://43.201.249.204:5000"):
        self.base_url = base_url
        print(f"🌐 DataCrawler 초기화 - 서버: {self.base_url}")
    
    def get_pcb_name(self, pcb_id):
        """PCB ID를 실제 PCB 이름으로 변환"""
        try:
            # pcb_id를 문자열로 변환 후 숫자 추출
            pcb_id_str = str(pcb_id)
            number_match = re.match(r'^(\d+)', pcb_id_str)
            if number_match:
                number = int(number_match.group(1))
                
                pcb_names = {
                    1: "SM-S901A",
                    4: "SM-G992N", 
                    5: "LM-G820K",
                    6: "XT2315-2",
                    7: "CPH2341",
                    8: "CPH2451",
                    9: "V2312DA",
                    10: "Pixel-8Pro",
                    11: "XQ-AT52",
                    12: "A3101"
                }
                
                return pcb_names.get(number, f"PCB{pcb_id}")
            else:
                return f"PCB{pcb_id}"
        except Exception as e:
            print(f"❌ PCB 이름 변환 오류: {e}")
            return f"PCB{pcb_id}"
    
    def test_endpoint_sync(self, endpoint: str) -> Dict[str, Any]:
        """동기적으로 엔드포인트 테스트 (전체 데이터 수집 테스트 포함)"""
        try:
            url = f"{self.base_url}{endpoint}"
            print(f"🧪 엔드포인트 테스트: {url}")
            
            # 기본 요청
            response = requests.get(url, timeout=30)
            
            result = {
                "endpoint": endpoint,
                "url": url,
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response_size": len(response.content),
                "content_type": response.headers.get('content-type', 'unknown')
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    result["data_type"] = type(data).__name__
                    
                    if isinstance(data, list):
                        result["data_length"] = len(data)
                        print(f"✅ 테스트 성공: {endpoint} - {len(data)}개 항목")
                        
                        # 샘플 데이터 확인
                        if len(data) > 0:
                            result["sample_item"] = data[0]
                            result["all_keys"] = list(data[0].keys()) if isinstance(data[0], dict) else []
                        
                        # 페이지네이션 가능성 체크
                        if len(data) in [50, 100, 500, 1000]:
                            print(f"⚠️ 페이지네이션 가능성 있음 ({len(data)}개)")
                            result["pagination_suspected"] = True
                            
                            # 페이지네이션 테스트
                            pagination_results = self._test_pagination_sync(url)
                            result["pagination_test"] = pagination_results
                        else:
                            result["pagination_suspected"] = False
                            
                    elif isinstance(data, dict):
                        result["data_length"] = len(data) if isinstance(data, dict) else 0
                        result["dict_keys"] = list(data.keys())
                        
                        # dict 내부에 배열이 있는지 확인
                        for key in ['data', 'items', 'results']:
                            if key in data and isinstance(data[key], list):
                                result[f"nested_{key}_length"] = len(data[key])
                                print(f"✅ 내부 배열 발견: {key} - {len(data[key])}개")
                        
                        print(f"✅ 테스트 성공: {endpoint} - dict 객체")
                    else:
                        result["data_length"] = 0
                        print(f"⚠️ 테스트 성공하지만 예상과 다른 타입: {type(data)}")
                        
                except Exception as parse_error:
                    result["data_type"] = "non-json"
                    result["parse_error"] = str(parse_error)
                    print(f"⚠️ JSON 파싱 실패: {endpoint}")
            else:
                result["error"] = response.text[:200]
                print(f"❌ 테스트 실패: {endpoint} - HTTP {response.status_code}")
                
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 네트워크 오류: {endpoint} - {e}")
            return {
                "endpoint": endpoint,
                "success": False,
                "error": f"Network error: {str(e)}"
            }
        except Exception as e:
            print(f"❌ 예외 발생: {endpoint} - {e}")
            return {
                "endpoint": endpoint,
                "success": False,
                "error": f"Exception: {str(e)}"
            }
    
    def _test_pagination_sync(self, base_url: str) -> Dict[str, Any]:
        """동기 방식으로 페이지네이션 테스트"""
        pagination_result = {
            "tested_params": [],
            "successful_pages": 0,
            "total_additional_items": 0,
            "working_params": None
        }
        
        try:
            # 다양한 페이지네이션 파라미터 테스트
            param_sets = [
                {'page': 2},
                {'page': 2, 'limit': 100},
                {'offset': 100, 'limit': 100},
                {'skip': 100, 'take': 100},
                {'start': 100, 'count': 100}
            ]
            
            for param_set in param_sets:
                try:
                    # URL에 파라미터 추가
                    params_str = '&'.join([f"{k}={v}" for k, v in param_set.items()])
                    separator = '&' if '?' in base_url else '?'
                    test_url = f"{base_url}{separator}{params_str}"
                    
                    pagination_result["tested_params"].append(param_set)
                    
                    response = requests.get(test_url, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if isinstance(data, list) and len(data) > 0:
                            pagination_result["successful_pages"] += 1
                            pagination_result["total_additional_items"] += len(data)
                            pagination_result["working_params"] = param_set
                            print(f"✅ 페이지네이션 성공: {param_set} - {len(data)}개 추가 항목")
                            break  # 성공하면 중단
                        elif isinstance(data, dict) and 'data' in data and len(data['data']) > 0:
                            pagination_result["successful_pages"] += 1
                            pagination_result["total_additional_items"] += len(data['data'])
                            pagination_result["working_params"] = param_set
                            print(f"✅ 페이지네이션 성공 (dict): {param_set} - {len(data['data'])}개 추가 항목")
                            break
                        
                except Exception as e:
                    print(f"❌ 페이지네이션 테스트 실패: {param_set} - {e}")
                    continue
            
        except Exception as e:
            pagination_result["error"] = str(e)
            
        return pagination_result
    
    async def fetch_api_data(self, endpoint):
        """API 데이터 가져오기 (개선된 오류 처리 및 로깅, 페이지네이션 지원)"""
        try:
            url = f"{self.base_url}{endpoint}"
            print(f"🔍 API 호출 시도: {url}")
            
            timeout = aiohttp.ClientTimeout(total=30)  # 타임아웃 증가
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            
            async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                # 첫 번째 요청 - 기본 데이터
                async with session.get(url, headers={
                    'Accept': 'application/json',
                    'User-Agent': 'PCB-Manager-Crawler/1.0'
                }) as response:
                    
                    print(f"📡 응답 상태: {response.status} - {url}")
                    print(f"📄 Content-Type: {response.headers.get('content-type', 'unknown')}")
                    
                    if response.status == 200:
                        try:
                            data = await response.json()
                            
                            # 데이터 타입별 처리
                            if isinstance(data, list):
                                data_info = f"{len(data)}개 항목"
                                print(f"✅ API 데이터 수신 성공: {endpoint} - {data_info}")
                                
                                # 페이지네이션이나 제한이 있는지 확인
                                if len(data) > 0:
                                    print(f"📊 첫 번째 항목 샘플: {data[0]}")
                                    
                                    # 만약 정확히 100개, 50개 등 딱 떨어지는 수라면 더 있을 가능성 체크
                                    if len(data) in [50, 100, 500, 1000]:
                                        print(f"⚠️ 데이터 개수가 {len(data)}개로 페이지네이션이 있을 수 있습니다.")
                                        
                                        # 페이지네이션 파라미터로 더 많은 데이터 시도
                                        additional_data = await self._fetch_paginated_data(session, url)
                                        if additional_data:
                                            data.extend(additional_data)
                                            print(f"📈 페이지네이션으로 추가 데이터 수집: 총 {len(data)}개")
                                
                                return data
                            elif isinstance(data, dict):
                                data_info = f"{type(data).__name__} 객체"
                                print(f"✅ API 데이터 수신 성공: {endpoint} - {data_info}")
                                
                                # dict 타입인 경우 내부에 배열이 있는지 확인
                                if 'data' in data and isinstance(data['data'], list):
                                    print(f"📊 dict 내부 data 배열 발견: {len(data['data'])}개")
                                    return data['data']
                                elif 'items' in data and isinstance(data['items'], list):
                                    print(f"📊 dict 내부 items 배열 발견: {len(data['items'])}개")
                                    return data['items']
                                else:
                                    return data
                            else:
                                print(f"✅ API 데이터 수신: {endpoint} - {type(data)}")
                                return data
                                
                        except aiohttp.ContentTypeError as e:
                            print(f"❌ JSON 파싱 오류: {endpoint} - {e}")
                            text_content = await response.text()
                            print(f"📄 응답 내용 (처음 500자): {text_content[:500]}")
                            return None
                    else:
                        error_text = await response.text()
                        print(f"❌ API 응답 오류: {endpoint} - HTTP {response.status}")
                        print(f"❌ 오류 내용: {error_text[:200]}...")
                        return None
                        
        except asyncio.TimeoutError:
            print(f"⏰ API 타임아웃: {endpoint}")
            return None
        except aiohttp.ClientError as e:
            print(f"❌ 클라이언트 오류: {endpoint} - {e}")
            return None
        except Exception as e:
            print(f"❌ API 데이터 가져오기 예외: {endpoint} - {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _fetch_paginated_data(self, session, base_url):
        """페이지네이션으로 추가 데이터 가져오기"""
        additional_data = []
        page = 2
        max_pages = 10  # 최대 10페이지까지만 시도
        
        try:
            while page <= max_pages:
                # 다양한 페이지네이션 파라미터 시도
                for param_set in [
                    {'page': page},
                    {'page': page, 'limit': 100},
                    {'offset': (page - 1) * 100, 'limit': 100},
                    {'skip': (page - 1) * 100, 'take': 100}
                ]:
                    try:
                        # URL에 파라미터 추가
                        params_str = '&'.join([f"{k}={v}" for k, v in param_set.items()])
                        separator = '&' if '?' in base_url else '?'
                        paginated_url = f"{base_url}{separator}{params_str}"
                        
                        print(f"🔄 페이지네이션 시도: {paginated_url}")
                        
                        async with session.get(paginated_url, headers={
                            'Accept': 'application/json',
                            'User-Agent': 'PCB-Manager-Crawler/1.0'
                        }) as response:
                            
                            if response.status == 200:
                                page_data = await response.json()
                                
                                if isinstance(page_data, list) and len(page_data) > 0:
                                    print(f"✅ 페이지 {page} 데이터 수집: {len(page_data)}개")
                                    additional_data.extend(page_data)
                                    page += 1
                                    break  # 성공하면 다음 페이지로
                                elif isinstance(page_data, dict):
                                    if 'data' in page_data and isinstance(page_data['data'], list) and len(page_data['data']) > 0:
                                        print(f"✅ 페이지 {page} 데이터 수집: {len(page_data['data'])}개")
                                        additional_data.extend(page_data['data'])
                                        page += 1
                                        break
                                    else:
                                        # 더 이상 데이터가 없음
                                        print(f"📋 페이지 {page}: 더 이상 데이터가 없습니다.")
                                        return additional_data
                                else:
                                    # 빈 배열이거나 데이터가 없음
                                    print(f"📋 페이지 {page}: 데이터가 없습니다.")
                                    return additional_data
                            else:
                                print(f"❌ 페이지 {page} 요청 실패: HTTP {response.status}")
                                continue  # 다음 파라미터 시도
                    except Exception as e:
                        print(f"❌ 페이지 {page} 오류: {e}")
                        continue
                else:
                    # 모든 파라미터 시도했지만 실패
                    print(f"❌ 페이지 {page}: 모든 파라미터 시도 실패")
                    break
            
            return additional_data
            
        except Exception as e:
            print(f"❌ 페이지네이션 처리 오류: {e}")
            return additional_data
    
    async def crawl_menu1_data(self):
        """PCB 대시보드 데이터 크롤링 (메뉴1 새로운 구조 반영)"""
        try:
            print("📊 Menu1 데이터 크롤링 시작...")
            response = await self.fetch_api_data("/api/user/pcb-summary")
            
            if response and isinstance(response, list) and len(response) > 0:
                print(f"📈 Menu1 실제 데이터 처리: {len(response)}개 PCB")
                
                # 1. 예약된 검사 일정 데이터
                scheduled_inspections = []
                for item in response:
                    if item.get('scheduled') or item.get('inspection_scheduled'):
                        inspection = {
                            'id': item.get('id', f"insp_{len(scheduled_inspections)}"),
                            'pcbName': item.get('name', 'Unknown'),
                            'type': item.get('inspection_type', '입고검사'),
                            'count': item.get('quantity', 1),
                            'method': item.get('inspection_method', 'AOI'),
                            'date': item.get('inspection_date', item.get('scheduled_date', '')),
                            'urls': item.get('image_urls', [])
                        }
                        scheduled_inspections.append(inspection)
                
                # 2. 생산 라인 부하 상태
                production_lines = {
                    "1라인": {"load": 85, "pcbs": ["A-32-Rev4"], "status": "high"},
                    "2라인": {"load": 45, "pcbs": ["B-16-Rev2"], "status": "normal"},
                    "3라인": {"load": 72, "pcbs": ["C-64-Rev1", "D-08-Rev3"], "status": "medium"},
                    "4라인": {"load": 30, "pcbs": ["E-24-Rev1"], "status": "normal"}
                }
                
                # 실제 데이터에서 라인별 부하 계산
                line_pcbs = {}
                for item in response:
                    line = item.get('line', '1라인')
                    if line not in line_pcbs:
                        line_pcbs[line] = []
                    line_pcbs[line].append(item.get('name', 'Unknown'))
                
                # 라인별 부하율 계산 (진행률 기반)
                for line, pcbs in line_pcbs.items():
                    if pcbs:
                        avg_progress = sum(item.get('progress', 0) for item in response if item.get('line') == line) / len(pcbs)
                        load = min(100, max(10, avg_progress + 20))  # 진행률 + 20%로 부하율 계산
                        production_lines[line] = {
                            "load": round(load),
                            "pcbs": pcbs,
                            "status": "high" if load > 70 else "medium" if load > 40 else "normal"
                        }
                
                # 3. PCB 모델별 평균 생산 소요시간
                pcb_production_times = []
                for item in response:
                    pcb_name = item.get('name', 'Unknown')
                    start_date = item.get('start_date', '')
                    expected_end = item.get('expected_end', '')
                    
                    if start_date and expected_end:
                        try:
                            from datetime import datetime
                            start = datetime.strptime(start_date, '%Y-%m-%d')
                            end = datetime.strptime(expected_end, '%Y-%m-%d')
                            days = (end - start).days
                            
                            # 실제 진행률을 고려한 예상 소요시간
                            progress = item.get('progress', 0)
                            if progress > 0:
                                actual_days = days * (100 / progress)
                            else:
                                actual_days = days
                            
                            pcb_production_times.append({
                                'model': pcb_name,
                                'days': round(actual_days, 1),
                                'average': 9.5,  # 평균 기준
                                'status': '지연' if actual_days > 10 else '빠름' if actual_days < 8 else '정상'
                            })
                        except:
                            pcb_production_times.append({
                                'model': pcb_name,
                                'days': 9.5,
                                'average': 9.5,
                                'status': '정상'
                            })
                
                # 4. 최근 7일 알림 추이 (시뮬레이션)
                alert_trend = {
                    'daily_alerts': [12, 8, 15, 23, 18, 11, 9],  # 최근 7일
                    'total_today': 23,
                    'trend': 'increasing'
                }
                
                # 5. 긴급 알림 및 경고
                emergency_alerts = [
                    {
                        'id': 1,
                        'message': '3라인 수작업 보정 단계 오류 발생',
                        'severity': 'high',
                        'line': '3라인',
                        'timestamp': '2025-01-24 14:32',
                        'details': 'PCB C-64-Rev1 솔더링 불량'
                    },
                    {
                        'id': 2,
                        'message': '부품 부족 - IC 칩 재고 없음',
                        'severity': 'high',
                        'line': '전체',
                        'timestamp': '2025-01-24 13:15',
                        'details': '자동 발주 시스템 활성화 필요'
                    },
                    {
                        'id': 3,
                        'message': '1라인 AOI 검사 장비 점검 필요',
                        'severity': 'medium',
                        'line': '1라인',
                        'timestamp': '2025-01-24 12:45',
                        'details': '정기 점검 일정 도래'
                    }
                ]
                
                # 6. PCB 상세 목록
                pcb_detailed_list = []
                for item in response:
                    pcb_detail = {
                        'name': item.get('name', 'Unknown'),
                        'line': item.get('line', '1라인'),
                        'status': item.get('status', '대기'),
                        'startDate': item.get('start_date', ''),
                        'expectedEnd': item.get('expected_end', ''),
                        'progress': item.get('progress', 0),
                        'statusColor': self._get_status_color(item.get('status', '대기'))
                    }
                    pcb_detailed_list.append(pcb_detail)
                
                # 7. 생산 공정 플로우
                process_flow = [
                    {'stage': '설계', 'count': len([p for p in response if p.get('status') == 'design']), 'color': 'bg-purple-500', 'isActive': True},
                    {'stage': '제조', 'count': len([p for p in response if p.get('status') == 'manufacturing']), 'color': 'bg-blue-500', 'isActive': True},
                    {'stage': '검사', 'count': len([p for p in response if p.get('status') == 'testing']), 'color': 'bg-yellow-500', 'isActive': True},
                    {'stage': '완료', 'count': len([p for p in response if p.get('status') == 'completed']), 'color': 'bg-green-500', 'isActive': False}
                ]
                
                # 8. PCB 상태 분포
                status_distribution = []
                total_pcbs = len(response)
                status_counts = {}
                
                for item in response:
                    status = item.get('status', '대기')
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                for status, count in status_counts.items():
                    percentage = round((count / total_pcbs) * 100) if total_pcbs > 0 else 0
                    status_distribution.append({
                        'status': status,
                        'count': count,
                        'color': self._get_status_color(status),
                        'percentage': percentage
                    })
                
                result = {
                    # 기본 통계
                    "total_pcbs": total_pcbs,
                    "production_status": {
                        "design": status_counts.get('design', 0),
                        "manufacturing": status_counts.get('manufacturing', 0),
                        "testing": status_counts.get('testing', 0),
                        "completed": status_counts.get('completed', 0)
                    },
                    "average_progress": round(sum(item.get('progress', 0) for item in response) / total_pcbs, 1) if total_pcbs > 0 else 0,
                    
                    # 새로운 구조 데이터
                    "scheduled_inspections": scheduled_inspections,
                    "production_lines": production_lines,
                    "pcb_production_times": pcb_production_times,
                    "alert_trend": alert_trend,
                    "emergency_alerts": emergency_alerts,
                    "pcb_detailed_list": pcb_detailed_list,
                    "process_flow": process_flow,
                    "status_distribution": status_distribution,
                    
                    # 하위 호환성을 위한 기존 필드들
                    "progress_stats": {
                        "0-25%": len([p for p in response if p.get('progress', 0) <= 25]),
                        "26-50%": len([p for p in response if 25 < p.get('progress', 0) <= 50]),
                        "51-75%": len([p for p in response if 50 < p.get('progress', 0) <= 75]),
                        "76-100%": len([p for p in response if p.get('progress', 0) > 75])
                    },
                    "recent_pcbs": sorted(response, key=lambda x: x.get('progress', 0), reverse=True)[:5],
                    "production_efficiency": round((status_counts.get('completed', 0) / total_pcbs * 100), 1) if total_pcbs > 0 else 0,
                    
                    "data_source": "api"
                }
                
                print(f"✅ Menu1 크롤링 완료: 총 {total_pcbs}개 PCB, 예약검사 {len(scheduled_inspections)}건, 알림 {len(emergency_alerts)}건")
                return result
                
        except Exception as e:
            print(f"❌ Menu1 데이터 크롤링 오류: {e}")
            import traceback
            traceback.print_exc()
        
        # 기본 데이터 반환 (API 실패시)
        print("🔄 Menu1 기본 데이터 사용")
        return {
            "total_pcbs": 18,
            "production_status": {
                "design": 2,
                "manufacturing": 3,
                "testing": 1,
                "completed": 12
            },
            "average_progress": 65.5,
            "scheduled_inspections": [
                {
                    'id': 'insp_1',
                    'pcbName': 'SM-S901A',
                    'type': '입고검사',
                    'count': 5,
                    'method': 'AOI',
                    'date': '2025-01-25',
                    'urls': ['image1.jpg', 'image2.jpg']
                }
            ],
            "production_lines": {
                "1라인": {"load": 85, "pcbs": ["A-32-Rev4"], "status": "high"},
                "2라인": {"load": 45, "pcbs": ["B-16-Rev2"], "status": "normal"},
                "3라인": {"load": 72, "pcbs": ["C-64-Rev1"], "status": "medium"},
                "4라인": {"load": 30, "pcbs": ["E-24-Rev1"], "status": "normal"}
            },
            "pcb_production_times": [
                {"model": "A-32-Rev4", "days": 10.2, "average": 9.5, "status": "지연"},
                {"model": "B-16-Rev2", "days": 8.1, "average": 9.5, "status": "정상"},
                {"model": "C-64-Rev1", "days": 11.8, "average": 9.5, "status": "지연"}
            ],
            "alert_trend": {
                'daily_alerts': [12, 8, 15, 23, 18, 11, 9],
                'total_today': 23,
                'trend': 'increasing'
            },
            "emergency_alerts": [
                {
                    'id': 1,
                    'message': '3라인 수작업 보정 단계 오류 발생',
                    'severity': 'high',
                    'line': '3라인',
                    'timestamp': '2025-01-24 14:32',
                    'details': 'PCB C-64-Rev1 솔더링 불량'
                }
            ],
            "pcb_detailed_list": [
                {"name": "SM-S901A", "line": "1라인", "status": "제조", "startDate": "2025-01-15", "expectedEnd": "2025-01-25", "progress": 85, "statusColor": "bg-yellow-500"},
                {"name": "LM-G820K", "line": "2라인", "status": "완성", "startDate": "2025-01-10", "expectedEnd": "2025-01-20", "progress": 100, "statusColor": "bg-green-500"}
            ],
            "process_flow": [
                {"stage": "설계", "count": 2, "color": "bg-purple-500", "isActive": True},
                {"stage": "제조", "count": 3, "color": "bg-blue-500", "isActive": True},
                {"stage": "검사", "count": 1, "color": "bg-yellow-500", "isActive": True},
                {"stage": "완료", "count": 12, "color": "bg-green-500", "isActive": False}
            ],
            "status_distribution": [
                {"status": "설계중", "count": 2, "color": "bg-purple-500", "percentage": 11},
                {"status": "제조중", "count": 3, "color": "bg-blue-500", "percentage": 17},
                {"status": "검사중", "count": 1, "color": "bg-yellow-500", "percentage": 6},
                {"status": "완료", "count": 12, "color": "bg-green-500", "percentage": 66}
            ],
            "progress_stats": {
                "0-25%": 2,
                "26-50%": 2,
                "51-75%": 3,
                "76-100%": 11
            },
            "recent_pcbs": [
                {"name": "A-32-Rev4", "status": "testing", "progress": 85},
                {"name": "B-16-Rev2", "status": "completed", "progress": 100},
                {"name": "C-64-Rev1", "status": "manufacturing", "progress": 45}
            ],
            "production_efficiency": 66.7,
            "data_source": "fallback"
        }
    
    def _get_status_color(self, status):
        """상태에 따른 색상 반환"""
        color_map = {
            'design': 'bg-purple-500',
            'manufacturing': 'bg-blue-500',
            'testing': 'bg-yellow-500',
            'completed': 'bg-green-500',
            '제조': 'bg-blue-500',
            '완성': 'bg-green-500',
            '검사': 'bg-yellow-500',
            '설계': 'bg-purple-500',
            '대기': 'bg-gray-500'
        }
        return color_map.get(status, 'bg-gray-500')
    
    async def crawl_menu2_data(self):
        """PCB 검사 관리 데이터 크롤링 (검사 현황 중심)"""
        try:
            print("🔍 Menu2 데이터 크롤링 시작...")
            response = await self.fetch_api_data("/api/user/pcb-summary")
            
            if response and isinstance(response, list) and len(response) > 0:
                total_inspections = len(response)
                print(f"🔬 Menu2 실제 데이터 처리: {total_inspections}건 검사")
                
                # 검사 상태별 통계
                inspection_status = {
                    "scheduled": len([p for p in response if p.get('scheduled')]),
                    "completed": len([p for p in response if p.get('status') == 'completed']),
                    "testing": len([p for p in response if p.get('status') == 'testing']),
                    "pending": len([p for p in response if p.get('status') in ['design', 'manufacturing']])
                }
                
                # 진행률별 검사 현황
                inspection_progress = {
                    "ready_for_inspection": len([p for p in response if p.get('progress', 0) >= 80 and p.get('status') != 'completed']),
                    "in_progress": len([p for p in response if 25 < p.get('progress', 0) < 80]),
                    "not_ready": len([p for p in response if p.get('progress', 0) <= 25])
                }
                
                # 검사 완료율 계산
                completion_rate = (inspection_status["completed"] / total_inspections * 100) if total_inspections > 0 else 0
                
                # 검사 예정 PCB들
                scheduled_pcbs = [p for p in response if p.get('scheduled')][:5]
                
                result = {
                    "total_inspections": total_inspections,
                    "inspection_status": inspection_status,
                    "inspection_progress": inspection_progress,
                    "completion_rate": round(completion_rate, 1),
                    "scheduled_pcbs": scheduled_pcbs,
                    "today_inspections": len([p for p in response if p.get('scheduled') and p.get('progress', 0) >= 80]),
                    "avg_inspection_time": 2.5,
                    "data_source": "api"
                }
                print(f"✅ Menu2 크롤링 완료: 총 {total_inspections}건 검사, 완료율 {completion_rate:.1f}%")
                return result
                
        except Exception as e:
            print(f"❌ Menu2 데이터 크롤링 오류: {e}")
        
        print("🔄 Menu2 기본 데이터 사용")
        return {
            "total_inspections": 10,
            "inspection_status": {
                "scheduled": 5,
                "completed": 3,
                "testing": 2,
                "pending": 0
            },
            "inspection_progress": {
                "ready_for_inspection": 4,
                "in_progress": 3,
                "not_ready": 3
            },
            "completion_rate": 30.0,
            "scheduled_pcbs": [
                {"name": "A-32-Rev4", "status": "testing", "progress": 85, "scheduled": True},
                {"name": "E-256-Rev1", "status": "testing", "progress": 90, "scheduled": True}
            ],
            "today_inspections": 2,
            "avg_inspection_time": 2.5,
            "data_source": "fallback"
        }
    
    async def crawl_menu3_data(self):
        """PCB 불량 관리 데이터 크롤링 (개선된 버전)"""
        try:
            print("📈 Menu3 데이터 크롤링 시작...")
            response = await self.fetch_api_data("/api/user/pcb-defect")
            
            if response and isinstance(response, list) and len(response) > 0:
                print(f"📊 Menu3 실제 데이터 처리: {len(response)}개 항목")
                
                # PCB별로 그룹화
                pcb_groups = {}
                total_defects = 0
                total_inspections = len(response)
                
                for item in response:
                    pcb_id = item.get('pcb_id', 'unknown')
                    if pcb_id not in pcb_groups:
                        pcb_groups[pcb_id] = {
                            'inspections': [],
                            'defect_count': 0,
                            'total_inspections': 0
                        }
                    
                    pcb_groups[pcb_id]['inspections'].append(item)
                    pcb_groups[pcb_id]['total_inspections'] += 1
                    
                    # 불량 검사인 경우
                    status = item.get('status', '')
                    if status == '불합격' or item.get('defect_result'):
                        pcb_groups[pcb_id]['defect_count'] += 1
                        total_defects += 1
                
                # PCB별 불량률 계산
                pcb_defect_rates = []
                for pcb_id, data in pcb_groups.items():
                    defect_rate = (data['defect_count'] / data['total_inspections'] * 100) if data['total_inspections'] > 0 else 0
                    pcb_name = self.get_pcb_name(pcb_id)
                    pcb_defect_rates.append({
                        'pcb_id': pcb_id,
                        'pcb_name': pcb_name,
                        'defect_count': data['defect_count'],
                        'total_inspections': data['total_inspections'],
                        'defect_rate': round(defect_rate, 1)
                    })
                
                # 불량률 순으로 정렬 (상위 3개)
                pcb_defect_rates.sort(key=lambda x: x['defect_rate'], reverse=True)
                top_defective_pcbs = pcb_defect_rates[:3]
                
                # 불량 유형별 통계
                defect_types = {
                    "Missing_hole": 0,
                    "Short": 0,
                    "Open_circuit": 0,
                    "Spur": 0,
                    "Mouse_bite": 0,
                    "Spurious_copper": 0
                }
                
                for item in response:
                    defect_result = item.get('defect_result')
                    if defect_result:
                        if isinstance(defect_result, list):
                            for defect in defect_result:
                                defect_type = defect.get('label', '기타')
                                if defect_type in defect_types:
                                    defect_types[defect_type] += 1
                                else:
                                    defect_types['Spurious_copper'] += 1
                        elif isinstance(defect_result, dict):
                            defect_type = defect_result.get('label', '기타')
                            if defect_type in defect_types:
                                defect_types[defect_type] += 1
                            else:
                                defect_types['Spurious_copper'] += 1
                
                # 전체 불량률 계산
                overall_defect_rate = (total_defects / total_inspections * 100) if total_inspections > 0 else 0
                
                result = {
                    "total_inspections": total_inspections,
                    "total_defects": total_defects,
                    "average_defect_rate": round(overall_defect_rate, 1),
                    "target_defect_rate": 5.0,
                    "defect_types": defect_types,
                    "top_defective_pcbs": top_defective_pcbs,
                    "pcb_defect_rates": pcb_defect_rates,
                    "data_source": "api"
                }
                print(f"✅ Menu3 크롤링 완료: {total_inspections}건 검사, {total_defects}건 불량 ({overall_defect_rate:.1f}%)")
                return result
                
        except Exception as e:
            print(f"❌ Menu3 데이터 크롤링 오류: {e}")
            import traceback
            traceback.print_exc()
        
        # 기본 데이터 (API 실패시)
        print("🔄 Menu3 기본 데이터 사용")
        return {
            "total_inspections": 83,
            "total_defects": 25,
            "average_defect_rate": 12.8,
            "target_defect_rate": 5.0,
            "defect_types": {
                "Missing_hole": 8,
                "Short": 6,
                "Open_circuit": 5,
                "Spur": 3,
                "Mouse_bite": 2,
                "Spurious_copper": 1
            },
            "top_defective_pcbs": [
                {"pcb_id": "11_0", "pcb_name": "XQ-AT52", "defect_count": 20, "total_inspections": 22, "defect_rate": 90.9},
                {"pcb_id": "9_1", "pcb_name": "V2312DA", "defect_count": 7, "total_inspections": 9, "defect_rate": 77.8},
                {"pcb_id": "1_3", "pcb_name": "SM-S901A", "defect_count": 5, "total_inspections": 6, "defect_rate": 83.3}
            ],
            "pcb_defect_rates": [],
            "data_source": "fallback"
        }
    
    async def crawl_menu4_data(self):
        """부품 재고 관리 데이터 크롤링 (프론트엔드 필드명 통일)"""
        try:
            print("📦 Menu4 데이터 크롤링 시작...")
            response = await self.fetch_api_data("/api/user/pcb-parts")
            
            if response and isinstance(response, list) and len(response) > 0:
                print(f"📋 Menu4 실제 데이터 처리: {len(response)}개 부품")
                
                low_stock_items = []
                critical_items = []
                moisture_sensitive_items = []
                capacitor_items = []
                samsung_parts = []
                murata_parts = []
                total_value = 0
                
                # 부품별 상세 정보 수집
                parts_details = []
                
                # 인덱스 개선 (대소문자 구분 없이, 여러 필드 포함)
                part_id_index = {}
                product_name_index = {}
                
                for item in response:
                    # ✅ 프론트엔드와 동일한 필드명 사용
                    partId = (item.get('partId') or 
                             item.get('part_id') or 
                             item.get('id') or 
                             'Unknown')
                    
                    product = (item.get('product') or 
                              item.get('part_number') or 
                              item.get('productName') or 
                              item.get('name') or 
                              'Unknown')
                    
                    type_field = (item.get('type') or 
                                 item.get('category') or 
                                 item.get('partType') or 
                                 'Unknown')
                    
                    size = item.get('size', 'Unknown')
                    manufacturer = item.get('manufacturer', 'Unknown')
                    quantity = item.get('quantity', 0)
                    minimumStock = (item.get('minimumStock') or 
                                   item.get('min_stock') or 
                                   item.get('minStock') or 0)
                    
                    unitCost = (item.get('unitCost') or 
                               item.get('unit_cost') or 
                               item.get('price') or 0)
                    
                    receivedDate = (item.get('receivedDate') or 
                                   item.get('received_date') or 
                                   item.get('date') or '')
                    
                    moistureAbsorption = (item.get('moistureAbsorption') or 
                                         item.get('moisture_absorption') or 
                                         item.get('isMoistureSensitive') or False)
                    
                    moistureMaterials = (item.get('moistureMaterials') or 
                                        item.get('moisture_materials') or 
                                        item.get('moistureProtection') or '불필요')
                    
                    actionRequired = (item.get('actionRequired') or 
                                     item.get('action_required') or 
                                     item.get('action') or '-')
                    
                    orderRequired = (item.get('orderRequired') or 
                                    item.get('order_required') or 
                                    item.get('needsOrder') or '-')
                    
                    # ✅ 프론트엔드와 정확히 일치하는 구조로 저장
                    part_detail = {
                        # 프론트엔드 필드명과 정확히 일치
                        'id': item.get('id', partId),
                        'partId': partId,
                        'product': product,
                        'type': type_field,
                        'size': size,
                        'manufacturer': manufacturer,
                        'quantity': quantity,
                        'minimumStock': minimumStock,
                        'receivedDate': receivedDate,
                        'moistureAbsorption': moistureAbsorption,
                        'moistureMaterials': moistureMaterials,
                        'actionRequired': actionRequired,
                        'orderRequired': orderRequired,
                        'unitCost': unitCost,
                        
                        # 검색용 추가 필드 (하위 호환성)
                        'part_id': partId,
                        'product_name': product,
                        'min_stock': minimumStock,
                        'unit_cost': unitCost,
                        'received_date': receivedDate,
                        'moisture_absorption': moistureAbsorption,
                        'moisture_materials': moistureMaterials,
                        'action_required': actionRequired,
                        'order_required': orderRequired
                    }
                    parts_details.append(part_detail)
                    
                    # 인덱스 생성 (대소문자 구분 없이, 공백 제거)
                    clean_part_id = str(partId).upper().strip()
                    clean_product_name = str(product).lower().strip()
                    
                    part_id_index[clean_part_id] = part_detail
                    product_name_index[clean_product_name] = part_detail
                    
                    print(f"📋 부품 등록: {clean_part_id} ({product})")
                    
                    # 재고 부족 항목 확인
                    if quantity <= minimumStock:
                        low_stock_items.append(part_detail)
                        if quantity < minimumStock * 0.5:
                            critical_items.append(part_detail)
                    
                    # 흡습성 항목 확인
                    if moistureAbsorption:
                        moisture_sensitive_items.append(part_detail)
                    
                    # 부품 타입별 분류
                    if 'capacitor' in type_field.lower() or 'cap' in type_field.lower():
                        capacitor_items.append(part_detail)
                    
                    # 제조사별 분류
                    manufacturer_lower = manufacturer.lower()
                    if 'samsung' in manufacturer_lower:
                        samsung_parts.append(part_detail)
                    elif 'murata' in manufacturer_lower:
                        murata_parts.append(part_detail)
                    
                    # 총 가치 계산
                    total_value += quantity * unitCost
                
                print(f"📊 인덱스 생성 완료:")
                print(f"  - Part ID 인덱스: {len(part_id_index)}개")
                print(f"  - Product Name 인덱스: {len(product_name_index)}개")
                
                # 실제 데이터 샘플 출력 (디버깅용)
                if parts_details:
                    sample_part = parts_details[0]
                    print(f"📋 샘플 부품 데이터: {sample_part.get('partId')} - {sample_part.get('product')}")
                
                # 통계 정보 생성
                manufacturer_stats = {}
                type_stats = {}
                moisture_materials_stats = {}
                
                for item in parts_details:
                    # 제조사별 통계
                    manufacturer = item['manufacturer']
                    manufacturer_stats[manufacturer] = manufacturer_stats.get(manufacturer, 0) + 1
                    
                    # 부품 타입별 통계
                    part_type = item['type']
                    type_stats[part_type] = type_stats.get(part_type, 0) + 1
                    
                    # 흡습 자재 통계
                    if item['moistureAbsorption']:
                        material = item['moistureMaterials']
                        moisture_materials_stats[material] = moisture_materials_stats.get(material, 0) + 1
                
                result = {
                    "total_items": len(response),
                    "low_stock_items": len(low_stock_items),
                    "critical_items": len(critical_items),
                    "moisture_sensitive_items": len(moisture_sensitive_items),
                    "capacitor_items": len(capacitor_items),
                    "samsung_parts": len(samsung_parts),
                    "murata_parts": len(murata_parts),
                    "total_value": total_value,
                    
                    # 상세 정보
                    "parts_details": parts_details,
                    "low_stock_details": low_stock_items[:10],
                    "moisture_sensitive_details": moisture_sensitive_items[:10],
                    "critical_items_details": critical_items,
                    
                    # 통계 정보
                    "moisture_materials_stats": moisture_materials_stats,
                    "manufacturer_stats": manufacturer_stats,
                    "type_stats": type_stats,
                    
                    # 개선된 검색 인덱스
                    "part_id_index": part_id_index,
                    "product_name_index": product_name_index,
                    
                    "data_source": "api"
                }
                print(f"✅ Menu4 크롤링 완료: {len(response)}개 부품, {len(low_stock_items)}개 부족, {len(moisture_sensitive_items)}개 흡습 민감")
                return result
                
        except Exception as e:
            print(f"❌ Menu4 데이터 크롤링 오류: {e}")
            import traceback
            traceback.print_exc()
        
        print("🔄 Menu4 기본 데이터 사용")
        return {
            "total_items": 50,
            "low_stock_items": 8,
            "critical_items": 3,
            "moisture_sensitive_items": 12,
            "capacitor_items": 15,
            "samsung_parts": 20,
            "murata_parts": 18,
            "total_value": 2450000,
            "parts_details": [],
            "low_stock_details": [],
            "moisture_sensitive_details": [],
            "part_id_index": {},
            "product_name_index": {},
            "data_source": "fallback"
        }
    
    async def crawl_mes_data(self):
        """MES 시스템 데이터 크롤링"""
        try:
            print("⚡ MES 데이터 크롤링 시작...")
            # 실제 환경에서는 MES API 엔드포인트를 사용
            # response = await self.fetch_api_data("/api/mes/status")
            
            # 시뮬레이션 데이터 (실제 환경에 맞게 수정 필요)
            result = {
                "temperature": 23.5,
                "humidity": 65.2,
                "production_count": 742,
                "quality_score": 94.2,
                "environment": {
                    "temperature": 23.5,
                    "humidity": 65.2,
                    "status": "정상"
                },
                "production": {
                    "current_rate": 24,
                    "target_rate": 25,
                    "efficiency": 96.0
                },
                "quality": {
                    "first_pass_yield": 94.2,
                    "rework_rate": 5.8,
                    "defect_rate": 2.1
                },
                "equipment": {
                    "uptime": 95.5,
                    "maintenance_due": 2,
                    "alerts": 0
                },
                "data_source": "simulation"
            }
            print("✅ MES 크롤링 완료 (시뮬레이션 데이터)")
            return result
            
        except Exception as e:
            print(f"❌ MES 데이터 크롤링 오류: {e}")
            return {
                "temperature": 23.5,
                "humidity": 65.2,
                "production_count": 742,
                "quality_score": 94.2,
                "data_source": "fallback"
            }
    
    async def get_menu_data(self, menu_id):
        """메뉴별 데이터 가져오기"""
        menu_crawlers = {
            "overview": self.crawl_menu1_data,
            "defects": self.crawl_menu2_data,
            "analytics": self.crawl_menu3_data,
            "inventory": self.crawl_menu4_data,
            "mes": self.crawl_mes_data,
            "menu1": self.crawl_menu1_data,
            "menu2": self.crawl_menu2_data,
            "menu3": self.crawl_menu3_data,
            "menu4": self.crawl_menu4_data,
            "mse": self.crawl_mes_data
        }
        
        crawler = menu_crawlers.get(menu_id)
        if crawler:
            try:
                print(f"🚀 {menu_id} 데이터 크롤링 시작...")
                result = await crawler()
                print(f"✅ {menu_id} 데이터 크롤링 완료")
                return result
            except Exception as e:
                print(f"❌ {menu_id} 크롤링 실패: {e}")
                return None
        else:
            print(f"⚠️ 지원하지 않는 메뉴 ID: {menu_id}")
            return None

    async def get_all_menu_data(self):
        """모든 메뉴 데이터를 병렬로 가져오기 (개선된 버전)"""
        try:
            print("🌐 전체 메뉴 데이터 크롤링 시작...")
            
            # 병렬 실행을 위한 태스크 생성
            tasks = [
                ("menu1", self.crawl_menu1_data()),
                ("menu2", self.crawl_menu2_data()), 
                ("menu3", self.crawl_menu3_data()),
                ("inventory", self.crawl_menu4_data()),
                ("mes", self.crawl_mes_data())
            ]
            
            # 모든 태스크를 병렬로 실행
            results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
            
            all_data = {}
            for i, (menu_name, _) in enumerate(tasks):
                result = results[i]
                if isinstance(result, Exception):
                    print(f"❌ {menu_name} 크롤링 실패: {result}")
                    all_data[menu_name] = None
                else:
                    all_data[menu_name] = result
                    source = result.get('data_source', 'unknown') if isinstance(result, dict) else 'unknown'
                    print(f"✅ {menu_name} 완료 (데이터 소스: {source})")
                    
            # 성공/실패 통계
            successful = sum(1 for data in all_data.values() if data is not None)
            total = len(all_data)
            print(f"📊 전체 크롤링 결과: {successful}/{total} 성공")
            
            return all_data
            
        except Exception as e:
            print(f"❌ 전체 메뉴 데이터 크롤링 오류: {e}")
            import traceback
            traceback.print_exc()
            return None

    def test_all_endpoints(self) -> Dict[str, Any]:
        """모든 API 엔드포인트를 동기적으로 테스트"""
        endpoints = [
            "/api/user/pcb-summary",
            "/api/user/pcb-defect", 
            "/api/user/pcb-parts",
            "/api/health"
        ]
        
        print(f"🧪 API 엔드포인트 종합 테스트 시작 - 서버: {self.base_url}")
        results = {}
        
        for endpoint in endpoints:
            results[endpoint] = self.test_endpoint_sync(endpoint)
        
        # 결과 요약
        successful = sum(1 for result in results.values() if result.get('success', False))
        total = len(results)
        
        print(f"\n📊 API 테스트 결과 요약:")
        print(f"  - 총 엔드포인트: {total}개")
        print(f"  - 성공: {successful}개")
        print(f"  - 실패: {total - successful}개")
        print(f"  - 성공률: {(successful/total*100):.1f}%")
        
        return {
            "server_url": self.base_url,
            "total_endpoints": total,
            "successful_endpoints": successful,
            "success_rate": round((successful/total*100), 1),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }

# 전역 크롤러 인스턴스
crawler = DataCrawler()

# 테스트 함수
async def test_crawler():
    """크롤러 테스트 함수 (개선된 버전)"""
    print("=" * 80)
    print("📊 데이터 크롤러 종합 테스트 시작...")
    print("=" * 80)
    
    # 1. 서버 연결 테스트
    print("\n🔍 1단계: API 엔드포인트 테스트")
    endpoint_results = crawler.test_all_endpoints()
    
    # 2. 개별 메뉴 테스트
    print("\n🔍 2단계: 개별 메뉴 크롤링 테스트")
    for menu_id in ["overview", "defects", "analytics", "inventory", "mes"]:
        print(f"\n🧪 {menu_id} 테스트...")
        try:
            data = await crawler.get_menu_data(menu_id)
            if data:
                source = data.get('data_source', 'unknown') if isinstance(data, dict) else 'unknown'
                print(f"✅ {menu_id} 성공 (소스: {source})")
            else:
                print(f"❌ {menu_id} 실패 - 데이터 없음")
        except Exception as e:
            print(f"❌ {menu_id} 예외 발생: {e}")
    
    # 3. 전체 데이터 테스트
    print(f"\n🔍 3단계: 전체 데이터 크롤링 테스트")
    try:
        all_data = await crawler.get_all_menu_data()
        if all_data:
            print(f"✅ 전체 데이터 크롤링 성공")
            for menu, data in all_data.items():
                status = "✅ 성공" if data else "❌ 실패"
                source = data.get('data_source', 'unknown') if isinstance(data, dict) and data else 'none'
                print(f"  {status} {menu}: {type(data).__name__} (소스: {source})")
        else:
            print(f"❌ 전체 데이터 크롤링 실패")
    except Exception as e:
        print(f"❌ 전체 데이터 크롤링 예외: {e}")
    
    print("\n" + "=" * 80)
    print("📊 크롤러 테스트 완료")
    print("=" * 80)

if __name__ == "__main__":
    # 직접 실행시 테스트 수행
    asyncio.run(test_crawler())