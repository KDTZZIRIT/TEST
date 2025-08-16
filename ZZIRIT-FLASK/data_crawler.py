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
        """PCB 불량 관리 데이터 크롤링 (개선된 버전 - 불량 유형별 분포 차트 지원)"""
        try:
            print("📈 Menu3 데이터 크롤링 시작...")
            response = await self.fetch_api_data("/api/user/pcb-defect")
            
            if response and isinstance(response, list) and len(response) > 0:
                print(f"📊 Menu3 실제 데이터 처리: {len(response)}개 항목")
                
                # 실제 데이터 구조 확인 (디버깅용)
                print(f"🔍 첫 번째 항목 구조 확인:")
                first_item = response[0]
                print(f"  - 키 목록: {list(first_item.keys())}")
                print(f"  - status: {first_item.get('status')}")
                print(f"  - defect_result 타입: {type(first_item.get('defect_result'))}")
                if first_item.get('defect_result'):
                    print(f"  - defect_result 내용: {first_item.get('defect_result')}")
                else:
                    print(f"  - defect_result 없음")
                
                # 불량 데이터가 있는 항목들 확인
                defect_items = [item for item in response if item.get('defect_result')]
                print(f"  - defect_result가 있는 항목: {len(defect_items)}개")
                if defect_items:
                    print(f"  - 첫 번째 불량 항목의 defect_result: {defect_items[0].get('defect_result')}")
                
                # PCB별로 그룹화
                pcb_groups = {}
                total_defects = 0
                total_inspections = len(response)
                
                # 불량 유형별 통계 (메뉴3 모달 차트용)
                defect_type_colors = {
                    "Missing_hole": "#64748b",
                    "Short": "#3b82f6", 
                    "Open_circuit": "#10b981",
                    "Spur": "#f59e0b",
                    "Mouse_bite": "#8b5cf6",
                    "Spurious_copper": "#6b7280",
                    "기타": "#6b7280"
                }
                
                # 불량 유형 정규화 함수 (개선된 버전)
                def normalize_defect_type(label):
                    if not label:
                        return "기타"
                    
                    normalized = label.lower().strip()
                    
                    # 정확한 매칭 우선
                    exact_matches = {
                        "missing_hole": "Missing_hole",
                        "short": "Short", 
                        "open_circuit": "Open_circuit",
                        "spur": "Spur",
                        "mouse_bite": "Mouse_bite",
                        "spurious_copper": "Spurious_copper"
                    }
                    
                    if normalized in exact_matches:
                        return exact_matches[normalized]
                    
                    # 부분 매칭
                    if "missing_hole" in normalized or "missing hole" in normalized or "hole_missing" in normalized or "홀 누락" in normalized:
                        return "Missing_hole"
                    elif "short" in normalized or "short_circuit" in normalized or "단락" in normalized or "쇼트" in normalized:
                        return "Short"
                    elif "open_circuit" in normalized or "open circuit" in normalized or "circuit_open" in normalized or "개방 회로" in normalized or "오픈" in normalized:
                        return "Open_circuit"
                    elif "spur" in normalized or "spur_defect" in normalized or "스퍼" in normalized or "스퍼어" in normalized:
                        return "Spur"
                    elif "mouse_bite" in normalized or "mouse bite" in normalized or "bite_mouse" in normalized or "마우스 바이트" in normalized or "마우스바이트" in normalized:
                        return "Mouse_bite"
                    elif "spurious_copper" in normalized or "spurious copper" in normalized or "copper_spurious" in normalized or "불량 구리" in normalized or "스퓨리어스" in normalized:
                        return "Spurious_copper"
                    else:
                        # 원본 라벨을 그대로 반환하되, 첫 글자만 대문자로
                        return label.capitalize() if label else "기타"
                
                # 전체 불량 유형별 통계 수집
                all_defect_types = {}
                total_defect_instances = 0
                
                for item in response:
                    pcb_id = item.get('pcb_id', 'unknown')
                    if pcb_id not in pcb_groups:
                        pcb_groups[pcb_id] = {
                            'inspections': [],
                            'defect_count': 0,
                            'total_inspections': 0,
                            'defect_types': {},
                            'all_defects': []
                        }
                    
                    pcb_groups[pcb_id]['inspections'].append(item)
                    pcb_groups[pcb_id]['total_inspections'] += 1
                    
                    # 불량 검사인 경우
                    status = item.get('status', '')
                    if status == '불합격' or item.get('defect_result') or item.get('label'):
                        pcb_groups[pcb_id]['defect_count'] += 1
                        total_defects += 1
                
                        # defect_result에서 불량 정보 수집 (개선된 버전)
                        defect_result = item.get('defect_result')
                        
                        # API 응답 구조에 따라 불량 정보 처리
                        if defect_result:
                            # 기존 defect_result 처리 로직
                            print(f"🔍 PCB {pcb_id} 불량 데이터 처리: {type(defect_result)}")
                            
                            # 다양한 데이터 구조 처리
                            defects_to_process = []
                            
                            if isinstance(defect_result, list):
                                print(f"  📋 리스트 형태 불량 데이터: {len(defect_result)}개")
                                defects_to_process = defect_result
                            elif isinstance(defect_result, dict):
                                print(f"  📋 딕셔너리 형태 불량 데이터: 1개")
                                defects_to_process = [defect_result]
                            elif isinstance(defect_result, str):
                                # 문자열인 경우 JSON 파싱 시도
                                try:
                                    import json
                                    parsed = json.loads(defect_result)
                                    if isinstance(parsed, list):
                                        defects_to_process = parsed
                                    elif isinstance(parsed, dict):
                                        defects_to_process = [parsed]
                                    print(f"  📋 JSON 파싱된 불량 데이터: {len(defects_to_process)}개")
                                except:
                                    # 단순 문자열을 라벨로 처리
                                    defects_to_process = [{'label': defect_result}]
                                    print(f"  📋 문자열을 라벨로 처리: '{defect_result}'")
                            
                            # 불량 데이터 처리
                            for i, defect in enumerate(defects_to_process):
                                if isinstance(defect, dict):
                                    original_label = defect.get('label', defect.get('type', defect.get('name', '기타')))
                                    defect_type = normalize_defect_type(original_label)
                                    total_defect_instances += 1
                                    
                                    print(f"    {i+1}. 원본: '{original_label}' -> 정규화: '{defect_type}'")
                                    
                                    # 전체 통계
                                    all_defect_types[defect_type] = all_defect_types.get(defect_type, 0) + 1
                                    
                                                                        # PCB별 통계
                                    pcb_groups[pcb_id]['defect_types'][defect_type] = pcb_groups[pcb_id]['defect_types'].get(defect_type, 0) + 1
                                    
                                    # 상세 불량 정보 저장
                                    pcb_groups[pcb_id]['all_defects'].append({
                                        'id': defect.get('id', defect.get('defect_id', 0)),
                                        'type': defect_type,
                                        'confidence': round(defect.get('score', defect.get('confidence', 0)) * 100),
                                        'x1': defect.get('x1', defect.get('x', 0)),
                                        'y1': defect.get('y1', defect.get('y', 0)),
                                        'x2': defect.get('x2', defect.get('x', 0)),
                                        'y2': defect.get('y2', defect.get('y', 0)),
                                        'width': defect.get('width', defect.get('w', 0)),
                                        'height': defect.get('height', defect.get('h', 0))
                                    })
                                elif isinstance(defect, str):
                                    # 문자열인 경우 직접 라벨로 처리
                                    defect_type = normalize_defect_type(defect)
                                    total_defect_instances += 1
                                    
                                    print(f"    {i+1}. 문자열 라벨: '{defect}' -> 정규화: '{defect_type}'")
                                    
                                    # 전체 통계
                                    all_defect_types[defect_type] = all_defect_types.get(defect_type, 0) + 1
                                    
                                    # PCB별 통계
                                    pcb_groups[pcb_id]['defect_types'][defect_type] = pcb_groups[pcb_id]['defect_types'].get(defect_type, 0) + 1
                        
                        # API 응답에서 직접 불량 정보 추출 (defect_result가 없는 경우)
                        elif item.get('label') or item.get('class_index') is not None:
                            print(f"🔍 PCB {pcb_id} 직접 불량 데이터 처리")
                            
                            # 직접 불량 정보 추출
                            original_label = item.get('label', '기타')
                            defect_type = normalize_defect_type(original_label)
                            total_defect_instances += 1
                            
                            print(f"  📋 직접 불량 데이터: 원본 '{original_label}' -> 정규화 '{defect_type}'")
                            
                            # 전체 통계
                            all_defect_types[defect_type] = all_defect_types.get(defect_type, 0) + 1
                            
                            # PCB별 통계
                            pcb_groups[pcb_id]['defect_types'][defect_type] = pcb_groups[pcb_id]['defect_types'].get(defect_type, 0) + 1
                            
                            # 상세 불량 정보 저장
                            pcb_groups[pcb_id]['all_defects'].append({
                                'id': item.get('id', 0),
                                'type': defect_type,
                                'confidence': round(item.get('score', 0) * 100),
                                'x1': item.get('x1', 0),
                                'y1': item.get('y1', 0),
                                'x2': item.get('x2', 0),
                                'y2': item.get('y2', 0),
                                'width': item.get('width', 0),
                                'height': item.get('height', 0)
                            })
                
                # PCB별 불량률 및 불량 유형 분포 계산
                pcb_defect_rates = []
                for pcb_id, data in pcb_groups.items():
                    defect_rate = (data['defect_count'] / data['total_inspections'] * 100) if data['total_inspections'] > 0 else 0
                    pcb_name = self.get_pcb_name(pcb_id)
                    
                    # PCB별 불량 유형 분포 차트 데이터 생성
                    pcb_defect_types = []
                    total_pcb_defects = len(data['all_defects'])
                    
                    for defect_type, count in data['defect_types'].items():
                        percentage = (count / total_pcb_defects * 100) if total_pcb_defects > 0 else 0
                        pcb_defect_types.append({
                            'type': defect_type,
                            'count': count,
                            'percentage': round(percentage, 2),
                            'color': defect_type_colors.get(defect_type, defect_type_colors["기타"])
                        })
                    
                    # 불량 유형별로 정렬
                    pcb_defect_types.sort(key=lambda x: x['count'], reverse=True)
                    
                    pcb_defect_rates.append({
                        'pcb_id': pcb_id,
                        'pcb_name': pcb_name,
                        'defect_count': data['defect_count'],
                        'total_inspections': data['total_inspections'],
                        'defect_rate': round(defect_rate, 1),
                        'defect_types': pcb_defect_types,
                        'all_defects': data['all_defects'],
                        'total_defect_instances': total_pcb_defects
                    })
                
                # 불량률 순으로 정렬 (상위 3개)
                pcb_defect_rates.sort(key=lambda x: x['defect_rate'], reverse=True)
                top_defective_pcbs = pcb_defect_rates[:3]
                
                # 전체 불량 유형별 분포 차트 데이터 생성
                overall_defect_types = []
                for defect_type, count in all_defect_types.items():
                    percentage = (count / total_defect_instances * 100) if total_defect_instances > 0 else 0
                    overall_defect_types.append({
                        'type': defect_type,
                        'count': count,
                        'percentage': round(percentage, 2),
                        'color': defect_type_colors.get(defect_type, defect_type_colors["기타"])
                    })
                
                # 불량 유형별로 정렬
                overall_defect_types.sort(key=lambda x: x['count'], reverse=True)
                
                # 디버깅 정보 출력
                print(f"📊 불량 유형별 분포 차트 데이터 생성:")
                print(f"  - 총 불량 인스턴스: {total_defect_instances}개")
                print(f"  - 불량 유형 수: {len(overall_defect_types)}개")
                for defect in overall_defect_types[:5]:  # 상위 5개 출력
                    print(f"  - {defect['type']}: {defect['count']}개 ({defect['percentage']}%)")
                
                # 전체 불량률 계산
                overall_defect_rate = (total_defects / total_inspections * 100) if total_inspections > 0 else 0
                
                # 일별 불량률 추이 데이터 생성 (최근 7일)
                daily_defect_rates = []
                try:
                    from datetime import datetime, timedelta
                    
                    # 최근 7일의 날짜 생성
                    today = datetime.now()
                    for i in range(6, -1, -1):  # 6일 전부터 오늘까지
                        target_date = today - timedelta(days=i)
                        date_str = target_date.strftime("%Y-%m-%d")
                        
                        # 해당 날짜의 불량 데이터 필터링 (inspection_id나 다른 날짜 필드 기준)
                        # 실제 API에서는 날짜 필드가 있을 것으로 예상
                        daily_inspections = []
                        daily_defects = 0
                        
                        for item in response:
                            # inspection_id를 날짜로 가정 (실제로는 created_at, inspection_date 등의 필드 사용)
                            # 여기서는 간단한 시뮬레이션으로 랜덤 데이터 생성
                            import random
                            if random.random() < 0.3:  # 30% 확률로 해당 날짜에 데이터가 있다고 가정
                                daily_inspections.append(item)
                                if item.get('status') == '불합격':
                                    daily_defects += 1
                        
                        # 일별 불량률 계산
                        daily_rate = (daily_defects / len(daily_inspections) * 100) if daily_inspections else 0
                        
                        daily_defect_rates.append({
                            'date': date_str,
                            'day': target_date.strftime("%a")[:3],  # Mon, Tue, Wed...
                            'day_kr': ['월', '화', '수', '목', '금', '토', '일'][target_date.weekday()],
                            'inspections': len(daily_inspections),
                            'defects': daily_defects,
                            'rate': round(daily_rate, 1)
                        })
                        
                except Exception as e:
                    print(f"⚠️ 일별 불량률 추이 데이터 생성 오류: {e}")
                    # 기본 데이터 사용
                    daily_defect_rates = [
                        {'date': '2024-08-01', 'day': 'Mon', 'day_kr': '월', 'inspections': 45, 'defects': 3, 'rate': 6.7},
                        {'date': '2024-08-02', 'day': 'Tue', 'day_kr': '화', 'inspections': 52, 'defects': 4, 'rate': 7.7},
                        {'date': '2024-08-03', 'day': 'Wed', 'day_kr': '수', 'inspections': 38, 'defects': 2, 'rate': 5.3},
                        {'date': '2024-08-04', 'day': 'Thu', 'day_kr': '목', 'inspections': 61, 'defects': 7, 'rate': 11.5},
                        {'date': '2024-08-05', 'day': 'Fri', 'day_kr': '금', 'inspections': 48, 'defects': 3, 'rate': 6.3},
                        {'date': '2024-08-06', 'day': 'Sat', 'day_kr': '토', 'inspections': 35, 'defects': 4, 'rate': 11.4},
                        {'date': '2024-08-07', 'day': 'Sun', 'day_kr': '일', 'inspections': 42, 'defects': 2, 'rate': 4.8}
                    ]
                
                # 기존 하위 호환성을 위한 defect_types 딕셔너리
                legacy_defect_types = {
                    "Missing_hole": all_defect_types.get("Missing_hole", 0),
                    "Short": all_defect_types.get("Short", 0),
                    "Open_circuit": all_defect_types.get("Open_circuit", 0),
                    "Spur": all_defect_types.get("Spur", 0),
                    "Mouse_bite": all_defect_types.get("Mouse_bite", 0),
                    "Spurious_copper": all_defect_types.get("Spurious_copper", 0)
                }
                
                result = {
                    "total_inspections": total_inspections,
                    "total_defects": total_defects,
                    "total_defect_instances": total_defect_instances,
                    "average_defect_rate": round(overall_defect_rate, 1),
                    "target_defect_rate": 5.0,
                    
                    # 새로운 불량 유형 분포 차트 데이터
                    "defect_types_chart": overall_defect_types,
                    "pcb_defect_rates": pcb_defect_rates,
                    "top_defective_pcbs": top_defective_pcbs,
                    
                    # 일별 불량률 추이 데이터 추가
                    "daily_defect_rates": daily_defect_rates,
                    
                    # 하위 호환성을 위한 기존 필드
                    "defect_types": legacy_defect_types,
                    
                    "data_source": "api"
                }
                
                print(f"✅ Menu3 크롤링 완료: {total_inspections}건 검사, {total_defects}건 불량 PCB, {total_defect_instances}개 불량 인스턴스 ({overall_defect_rate:.1f}%)")
                print(f"📊 불량 유형 분포: {len(overall_defect_types)}개 유형, 상위 3개: {[d['type'] for d in overall_defect_types[:3]]}")
                return result
                
        except Exception as e:
            print(f"❌ Menu3 데이터 크롤링 오류: {e}")
            import traceback
            traceback.print_exc()
        
        # 기본 데이터 (API 실패시)
        print("🔄 Menu3 기본 데이터 사용")
        
        # 기본 불량 유형 분포 차트 데이터 (더 현실적인 데이터)
        default_defect_types_chart = [
            {"type": "Missing_hole", "count": 12, "percentage": 35.3, "color": "#64748b"},
            {"type": "Short", "count": 8, "percentage": 23.5, "color": "#3b82f6"},
            {"type": "Open_circuit", "count": 6, "percentage": 17.6, "color": "#10b981"},
            {"type": "Spur", "count": 4, "percentage": 11.8, "color": "#f59e0b"},
            {"type": "Mouse_bite", "count": 3, "percentage": 8.8, "color": "#8b5cf6"},
            {"type": "Spurious_copper", "count": 1, "percentage": 2.9, "color": "#6b7280"}
        ]
        
        # 기본 PCB별 불량 유형 분포 데이터
        default_pcb_defect_rates = [
            {
                "pcb_id": "11_0", 
                "pcb_name": "XQ-AT52", 
                "defect_count": 20, 
                "total_inspections": 22, 
                "defect_rate": 90.9,
                "defect_types": [
                    {"type": "Missing_hole", "count": 8, "percentage": 40.0, "color": "#64748b"},
                    {"type": "Short", "count": 6, "percentage": 30.0, "color": "#3b82f6"},
                    {"type": "Open_circuit", "count": 4, "percentage": 20.0, "color": "#10b981"},
                    {"type": "Spur", "count": 2, "percentage": 10.0, "color": "#f59e0b"}
                ],
                "total_defect_instances": 20
            },
            {
                "pcb_id": "9_1", 
                "pcb_name": "V2312DA", 
                "defect_count": 7, 
                "total_inspections": 9, 
                "defect_rate": 77.8,
                "defect_types": [
                    {"type": "Short", "count": 3, "percentage": 42.9, "color": "#3b82f6"},
                    {"type": "Missing_hole", "count": 2, "percentage": 28.6, "color": "#64748b"},
                    {"type": "Mouse_bite", "count": 2, "percentage": 28.6, "color": "#8b5cf6"}
                ],
                "total_defect_instances": 7
            },
            {
                "pcb_id": "1_3", 
                "pcb_name": "SM-S901A", 
                "defect_count": 5, 
                "total_inspections": 6, 
                "defect_rate": 83.3,
                "defect_types": [
                    {"type": "Open_circuit", "count": 2, "percentage": 40.0, "color": "#10b981"},
                    {"type": "Spur", "count": 2, "percentage": 40.0, "color": "#f59e0b"},
                    {"type": "Spurious_copper", "count": 1, "percentage": 20.0, "color": "#6b7280"}
                ],
                "total_defect_instances": 5
            }
        ]
        
        return {
            "total_inspections": 83,
            "total_defects": 25,
            "total_defect_instances": 34,  # 실제 불량 인스턴스 총합
            "average_defect_rate": 12.8,
            "target_defect_rate": 5.0,
            
            # 새로운 불량 유형 분포 차트 데이터
            "defect_types_chart": default_defect_types_chart,
            "pcb_defect_rates": default_pcb_defect_rates,
            
            # 일별 불량률 추이 데이터 추가
            "daily_defect_rates": [
                {'date': '2024-08-01', 'day': 'Mon', 'day_kr': '월', 'inspections': 45, 'defects': 3, 'rate': 6.7},
                {'date': '2024-08-02', 'day': 'Tue', 'day_kr': '화', 'inspections': 52, 'defects': 4, 'rate': 7.7},
                {'date': '2024-08-03', 'day': 'Wed', 'day_kr': '수', 'inspections': 38, 'defects': 2, 'rate': 5.3},
                {'date': '2024-08-04', 'day': 'Thu', 'day_kr': '목', 'inspections': 61, 'defects': 7, 'rate': 11.5},
                {'date': '2024-08-05', 'day': 'Fri', 'day_kr': '금', 'inspections': 48, 'defects': 3, 'rate': 6.3},
                {'date': '2024-08-06', 'day': 'Sat', 'day_kr': '토', 'inspections': 35, 'defects': 4, 'rate': 11.4},
                {'date': '2024-08-07', 'day': 'Sun', 'day_kr': '일', 'inspections': 42, 'defects': 2, 'rate': 4.8}
            ],
            
            # 하위 호환성을 위한 기존 필드
            "defect_types": {
                "Missing_hole": 12,
                "Short": 8,
                "Open_circuit": 6,
                "Spur": 4,
                "Mouse_bite": 3,
                "Spurious_copper": 1
            },
            "top_defective_pcbs": [
                {"pcb_id": "11_0", "pcb_name": "XQ-AT52", "defect_count": 20, "total_inspections": 22, "defect_rate": 90.9},
                {"pcb_id": "9_1", "pcb_name": "V2312DA", "defect_count": 7, "total_inspections": 9, "defect_rate": 77.8},
                {"pcb_id": "1_3", "pcb_name": "SM-S901A", "defect_count": 5, "total_inspections": 6, "defect_rate": 83.3}
            ],
            "data_source": "fallback"
        }
    
    async def crawl_menu1_data(self):
        """Menu1 PCB 대시보드 데이터 크롤링"""
        try:
            print("📊 Menu1 데이터 크롤링 시작...")
            
            # 실제 API가 없으므로 시뮬레이션 데이터 생성
            # 실제 구현시에는 PCB 생산 관리 API를 사용
            from datetime import datetime, timedelta
            import random
            
            # 현재 시간 기준으로 최근 7일의 데이터 생성
            current_time = datetime.now()
            
            # PCB 생산 현황 데이터
            pcb_production_data = [
                {
                    'name': 'SM-S901A',
                    'size': '60×40',
                    'material': 'FR-4',
                    'smtDensity': 'Low',
                    'boardArea': '2400',
                    'stock': 1,
                    'status': 'active',
                    'description': '삼성 갤럭시 S23 시리즈용 메인보드',
                    'production_line': 1,
                    'target_date': (current_time + timedelta(days=5)).strftime('%Y-%m-%d')
                },
                {
                    'name': 'SM-G992N',
                    'size': '80×60',
                    'material': 'FR-4',
                    'smtDensity': 'Medium',
                    'boardArea': '4800',
                    'stock': 1,
                    'status': 'active',
                    'description': '삼성 갤럭시 S21 시리즈용 메인보드',
                    'production_line': 2,
                    'target_date': (current_time + timedelta(days=3)).strftime('%Y-%m-%d')
                },
                {
                    'name': 'M-G820K',
                    'size': '100×70',
                    'material': 'CEM-3',
                    'smtDensity': 'Medium',
                    'boardArea': '7000',
                    'stock': 1,
                    'status': 'active',
                    'description': 'LG G8 ThinQ용 메인보드',
                    'production_line': 3,
                    'target_date': (current_time + timedelta(days=7)).strftime('%Y-%m-%d')
                },
                {
                    'name': 'XT2315-2',
                    'size': '120×80',
                    'material': 'Aluminum',
                    'smtDensity': 'Medium',
                    'boardArea': '9600',
                    'stock': 1,
                    'status': 'active',
                    'description': 'Xiaomi 13T Pro용 메인보드',
                    'production_line': 1,
                    'target_date': (current_time + timedelta(days=4)).strftime('%Y-%m-%d')
                },
                {
                    'name': 'CPH2341',
                    'size': '100×100',
                    'material': 'FR-4',
                    'smtDensity': 'Medium~High',
                    'boardArea': '10000',
                    'stock': 1,
                    'status': 'active',
                    'description': 'OPPO Find X6 Pro용 메인보드',
                    'production_line': 2,
                    'target_date': (current_time + timedelta(days=6)).strftime('%Y-%m-%d')
                },
                {
                    'name': 'CPH2451',
                    'size': '130×90',
                    'material': 'Aluminum',
                    'smtDensity': 'High',
                    'boardArea': '11700',
                    'stock': 1,
                    'status': 'active',
                    'description': 'OPPO Find X7 Ultra용 메인보드',
                    'production_line': 3,
                    'target_date': (current_time + timedelta(days=2)).strftime('%Y-%m-%d')
                },
                {
                    'name': 'V2312DA',
                    'size': '150×100',
                    'material': 'Ceramic',
                    'smtDensity': 'Ultra-High',
                    'boardArea': '15000',
                    'stock': 1,
                    'status': 'active',
                    'description': 'Vivo X90 Pro+용 메인보드',
                    'production_line': 4,
                    'target_date': (current_time + timedelta(days=8)).strftime('%Y-%m-%d')
                },
                {
                    'name': 'Pixel-8Pro',
                    'size': '140×90',
                    'material': 'FR-4',
                    'smtDensity': 'Ultra-High',
                    'boardArea': '12600',
                    'stock': 1,
                    'status': 'active',
                    'description': 'Google Pixel 8 Pro용 메인보드',
                    'production_line': 1,
                    'target_date': (current_time + timedelta(days=1)).strftime('%Y-%m-%d')
                },
                {
                    'name': 'XQ-AT52',
                    'size': '80×50',
                    'material': 'CEM-1',
                    'smtDensity': 'Low',
                    'boardArea': '4000',
                    'stock': 1,
                    'status': 'active',
                    'description': 'Sony Xperia 1 V용 메인보드',
                    'production_line': 2,
                    'target_date': (current_time + timedelta(days=9)).strftime('%Y-%m-%d')
                },
                {
                    'name': 'A3101',
                    'size': '60×60',
                    'material': 'FR-4',
                    'smtDensity': 'Medium',
                    'boardArea': '3600',
                    'stock': 1,
                    'status': 'active',
                    'description': 'Apple iPhone 15용 메인보드',
                    'production_line': 4,
                    'target_date': (current_time + timedelta(days=10)).strftime('%Y-%m-%d')
                }
            ]
            
            # 예약된 검사 일정 데이터
            scheduled_inspections = [
                {
                    'id': '1',
                    'pcbName': 'SM-S901A',
                    'type': '입고검사',
                    'count': 5,
                    'method': 'AOI',
                    'urls': ['url1', 'url2'],
                    'date': (current_time + timedelta(days=1)).strftime('%Y-%m-%d'),
                    'status': 'scheduled'
                },
                {
                    'id': '2',
                    'pcbName': 'SM-G992N',
                    'type': '출하검사',
                    'count': 3,
                    'method': 'AOI',
                    'urls': ['url3'],
                    'date': (current_time + timedelta(days=2)).strftime('%Y-%m-%d'),
                    'status': 'scheduled'
                },
                {
                    'id': '3',
                    'pcbName': 'M-G820K',
                    'type': '입고검사',
                    'count': 8,
                    'method': 'AOI',
                    'urls': ['url4', 'url5', 'url6'],
                    'date': (current_time + timedelta(days=3)).strftime('%Y-%m-%d'),
                    'status': 'scheduled'
                }
            ]
            
            # 검사 이력 데이터
            inspection_history = [
                {
                    'id': 'hist1',
                    'pcbName': 'SM-S901A',
                    'passedCount': 18,
                    'defectiveCount': 2,
                    'totalInspected': 20,
                    'inspectionTime': 45,
                    'completedAt': (current_time - timedelta(hours=2)).isoformat(),
                    'status': 'completed',
                    'results': [
                        {
                            'defects': [
                                {'label': 'Short', 'count': 1},
                                {'label': 'Open_circuit', 'count': 1}
                            ]
                        }
                    ]
                },
                {
                    'id': 'hist2',
                    'pcbName': 'SM-G992N',
                    'passedCount': 15,
                    'defectiveCount': 5,
                    'totalInspected': 20,
                    'inspectionTime': 52,
                    'completedAt': (current_time - timedelta(hours=4)).isoformat(),
                    'status': 'completed',
                    'results': [
                        {
                            'defects': [
                                {'label': 'Mouse_bite', 'count': 2},
                                {'label': 'Spur', 'count': 2},
                                {'label': 'Short', 'count': 1}
                            ]
                        }
                    ]
                }
            ]
            
            # 생산 라인 부하 상태
            production_lines = [
                {
                    'line': 1,
                    'load': 75,
                    'status': 'active',
                    'currentPCB': 'SM-S901A',
                    'progress': 65
                },
                {
                    'line': 2,
                    'load': 45,
                    'status': 'active',
                    'currentPCB': 'SM-G992N',
                    'progress': 30
                },
                {
                    'line': 3,
                    'load': 90,
                    'status': 'active',
                    'currentPCB': 'M-G820K',
                    'progress': 85
                },
                {
                    'line': 4,
                    'load': 25,
                    'status': 'idle',
                    'currentPCB': None,
                    'progress': 0
                }
            ]
            
            # 알림 데이터
            notifications = [
                {
                    'id': 'notif1',
                    'type': 'warning',
                    'message': '라인 3 부하율 90% 초과',
                    'timestamp': (current_time - timedelta(hours=1)).isoformat(),
                    'severity': 'medium'
                },
                {
                    'id': 'notif2',
                    'type': 'info',
                    'message': 'SM-S901A 검사 완료',
                    'timestamp': (current_time - timedelta(hours=2)).isoformat(),
                    'severity': 'low'
                }
            ]
            
            # 통계 계산
            total_pcbs = len(pcb_production_data)
            total_scheduled = len(scheduled_inspections)
            total_inspections = len(inspection_history)
            total_notifications = len(notifications)
            
            # 재질별 통계
            material_stats = {}
            for pcb in pcb_production_data:
                material = pcb['material']
                material_stats[material] = material_stats.get(material, 0) + 1
            
            # SMT 밀도별 통계
            smt_density_stats = {}
            for pcb in pcb_production_data:
                density = pcb['smtDensity']
                smt_density_stats[density] = smt_density_stats.get(density, 0) + 1
            
            # 검사 통계
            total_passed = sum(inspection['passedCount'] for inspection in inspection_history)
            total_defective = sum(inspection['defectiveCount'] for inspection in inspection_history)
            total_inspected = sum(inspection['totalInspected'] for inspection in inspection_history)
            overall_defect_rate = round((total_defective / total_inspected) * 100, 1) if total_inspected > 0 else 0
            
            result = {
                'pcb_production_data': pcb_production_data,
                'scheduled_inspections': scheduled_inspections,
                'inspection_history': inspection_history,
                'production_lines': production_lines,
                'notifications': notifications,
                
                # 통계 데이터
                'total_pcbs': total_pcbs,
                'total_scheduled': total_scheduled,
                'total_inspections': total_inspections,
                'total_notifications': total_notifications,
                
                # 검사 통계
                'total_passed': total_passed,
                'total_defective': total_defective,
                'total_inspected': total_inspected,
                'overall_defect_rate': overall_defect_rate,
                
                # 분류별 통계
                'material_stats': material_stats,
                'smt_density_stats': smt_density_stats,
                
                'data_source': 'simulation'
            }
            
            print(f"✅ Menu1 데이터 크롤링 완료: PCB {total_pcbs}개, 예약 검사 {total_scheduled}건, 검사 이력 {total_inspections}건")
            print(f"📊 전체 불량률: {overall_defect_rate}%, 총 검사: {total_inspected}건")
            
            return result
            
        except Exception as e:
            print(f"❌ Menu1 데이터 크롤링 오류: {e}")
            import traceback
            traceback.print_exc()
            
            # 기본 데이터 반환
            return {
                'pcb_production_data': [],
                'scheduled_inspections': [],
                'inspection_history': [],
                'production_lines': [],
                'notifications': [],
                'total_pcbs': 0,
                'total_scheduled': 0,
                'total_inspections': 0,
                'total_notifications': 0,
                'total_passed': 0,
                'total_defective': 0,
                'total_inspected': 0,
                'overall_defect_rate': 0,
                'material_stats': {},
                'smt_density_stats': {},
                'data_source': 'fallback'
            }

    async def crawl_mes_data(self):
        """MES 공장 환경 모니터링 데이터 크롤링"""
        try:
            print("🏭 MES 데이터 크롤링 시작...")
            
            # 실제 API가 없으므로 시뮬레이션 데이터 생성
            # 실제 구현시에는 공장 환경 센서 API나 소켓 데이터를 사용
            from datetime import datetime, timedelta
            import random
            
            # 현재 시간 기준으로 최근 7시간의 환경 데이터 생성
            current_time = datetime.now()
            environment_history = []
            
            for i in range(7):
                target_time = current_time - timedelta(hours=i)
                # 실제 센서 데이터와 유사한 값 생성
                base_temp = 23.5
                base_humidity = 65.2
                base_pm25 = 12.3
                base_pm10 = 18.7
                base_co2 = 420
                
                # 시간대별 변동 추가
                hour_factor = target_time.hour
                if 6 <= hour_factor <= 18:  # 업무시간
                    temp_variation = random.uniform(-1, 2)
                    humidity_variation = random.uniform(-3, 5)
                    pm_variation = random.uniform(-1, 3)
                    co2_variation = random.uniform(-15, 25)
                else:  # 야간시간
                    temp_variation = random.uniform(-2, 1)
                    humidity_variation = random.uniform(-5, 3)
                    pm_variation = random.uniform(-2, 1)
                    co2_variation = random.uniform(-25, 15)
                
                environment_history.append({
                    'timestamp': target_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'time': target_time.strftime('%H:%M'),
                    'temperature_c': round(base_temp + temp_variation, 1),
                    'humidity_percent': round(base_humidity + humidity_variation, 1),
                    'pm25_ug_m3': round(base_pm25 + pm_variation, 1),
                    'pm10_ug_m3': round(base_pm10 + pm_variation, 1),
                    'co2_ppm': round(base_co2 + co2_variation),
                    'sensors': "정상"
                })
            
            # 습도 민감 자재 데이터 (실제 데이터 구조와 일치)
            moisture_sensitive_materials = [
                {
                    'name': 'LFD211G44PK9F557',
                    'type': 'IC / Power Management',
                    'optimalRange': '20-60%',
                    'currentHumidity': round(48.3 + random.uniform(-0.5, 0.5), 1),
                    'status': 'normal',
                    'warehouse': 'A-1',
                    'moistureAbsorption': True,
                    'inventory': 3482
                },
                {
                    'name': 'LST03-8P-H06-E20000',
                    'type': 'IC / Logic',
                    'optimalRange': '20-60%',
                    'currentHumidity': round(48.3 + random.uniform(-0.5, 0.5), 1),
                    'status': 'normal',
                    'warehouse': 'A-1',
                    'moistureAbsorption': True,
                    'inventory': 5371
                },
                {
                    'name': 'SAFFW1G54AA0E3K',
                    'type': 'IC / Memory',
                    'optimalRange': '20-60%',
                    'currentHumidity': round(48.6 + random.uniform(-0.5, 0.5), 1),
                    'status': 'normal',
                    'warehouse': 'A-1',
                    'moistureAbsorption': True,
                    'inventory': 4096
                },
                {
                    'name': 'AOCR33135A',
                    'type': 'IC / Audio',
                    'optimalRange': '20-60%',
                    'currentHumidity': round(38.5 + random.uniform(-0.5, 0.5), 1),
                    'status': 'normal',
                    'warehouse': 'A-2',
                    'moistureAbsorption': True,
                    'inventory': 6610
                },
                {
                    'name': 'ET3138SE',
                    'type': 'IC / Communication',
                    'optimalRange': '20-60%',
                    'currentHumidity': round(38.4 + random.uniform(-0.5, 0.5), 1),
                    'status': 'normal',
                    'warehouse': 'A-2',
                    'moistureAbsorption': False,
                    'inventory': 5535
                },
                {
                    'name': 'ET53128YB',
                    'type': 'IC / Communication',
                    'optimalRange': '20-60%',
                    'currentHumidity': round(38.3 + random.uniform(-0.5, 0.5), 1),
                    'status': 'normal',
                    'warehouse': 'A-2',
                    'moistureAbsorption': True,
                    'inventory': 7010
                },
                {
                    'name': 'MAX17333X22+T',
                    'type': 'IC / Power Management',
                    'optimalRange': '20-60%',
                    'currentHumidity': round(38.2 + random.uniform(-0.5, 0.5), 1),
                    'status': 'normal',
                    'warehouse': 'A-2',
                    'moistureAbsorption': True,
                    'inventory': 6982
                },
                {
                    'name': 'MXD8546CDS',
                    'type': 'IC / Logic',
                    'optimalRange': '20-60%',
                    'currentHumidity': round(38.6 + random.uniform(-0.5, 0.5), 1),
                    'status': 'normal',
                    'warehouse': 'A-2',
                    'moistureAbsorption': True,
                    'inventory': 8075
                },
                {
                    'name': 'MXDLN14TS',
                    'type': 'IC / Logic',
                    'optimalRange': '20-60%',
                    'currentHumidity': round(38.5 + random.uniform(-0.5, 0.5), 1),
                    'status': 'normal',
                    'warehouse': 'A-2',
                    'moistureAbsorption': True,
                    'inventory': 6211
                },
                {
                    'name': 'S2DOS15A01-6032',
                    'type': 'IC / Power Management',
                    'optimalRange': '20-60%',
                    'currentHumidity': round(38.3 + random.uniform(-0.5, 0.5), 1),
                    'status': 'normal',
                    'warehouse': 'A-2',
                    'moistureAbsorption': True,
                    'inventory': 7951
                },
                {
                    'name': 'SM3012A',
                    'type': 'IC / Power Management',
                    'optimalRange': '20-60%',
                    'currentHumidity': round(38.5 + random.uniform(-0.5, 0.5), 1),
                    'status': 'normal',
                    'warehouse': 'A-2',
                    'moistureAbsorption': True,
                    'inventory': 8016
                },
                {
                    'name': 'QM23030',
                    'type': 'IC / RF',
                    'optimalRange': '20-60%',
                    'currentHumidity': round(53.4 + random.uniform(-0.5, 0.5), 1),
                    'status': 'normal',
                    'warehouse': 'A-3',
                    'moistureAbsorption': True,
                    'inventory': 7223
                },
                {
                    'name': 'QM42500A',
                    'type': 'IC / RF',
                    'optimalRange': '20-60%',
                    'currentHumidity': round(53.6 + random.uniform(-0.5, 0.5), 1),
                    'status': 'normal',
                    'warehouse': 'A-3',
                    'moistureAbsorption': True,
                    'inventory': 9470
                },
                {
                    'name': 'SAYRZ634MBA0C3K',
                    'type': 'IC / Memory',
                    'optimalRange': '20-60%',
                    'currentHumidity': round(53.6 + random.uniform(-0.5, 0.5), 1),
                    'status': 'normal',
                    'warehouse': 'A-3',
                    'moistureAbsorption': True,
                    'inventory': 8564
                },
                {
                    'name': 'SAYRZ725MBA0L3K',
                    'type': 'IC / Memory',
                    'optimalRange': '20-60%',
                    'currentHumidity': round(53.4 + random.uniform(-0.5, 0.5), 1),
                    'status': 'normal',
                    'warehouse': 'A-3',
                    'moistureAbsorption': False,
                    'inventory': 9174
                },
                {
                    'name': 'SFHG76AF302',
                    'type': 'IC / RF',
                    'optimalRange': '20-60%',
                    'currentHumidity': round(53.3 + random.uniform(-0.5, 0.5), 1),
                    'status': 'normal',
                    'warehouse': 'A-3',
                    'moistureAbsorption': True,
                    'inventory': 8528
                },
                {
                    'name': 'SFHG89BF302',
                    'type': 'IC / RF',
                    'optimalRange': '20-60%',
                    'currentHumidity': round(53.4 + random.uniform(-0.5, 0.5), 1),
                    'status': 'normal',
                    'warehouse': 'A-3',
                    'moistureAbsorption': True,
                    'inventory': 8503
                },
                {
                    'name': 'SFML5Y0J001',
                    'type': 'IC / RF',
                    'optimalRange': '20-60%',
                    'currentHumidity': round(53.5 + random.uniform(-0.5, 0.5), 1),
                    'status': 'normal',
                    'warehouse': 'A-3',
                    'moistureAbsorption': False,
                    'inventory': 6784
                },
                {
                    'name': 'SFML7F0J001',
                    'type': 'IC / RF',
                    'optimalRange': '20-60%',
                    'currentHumidity': round(53.5 + random.uniform(-0.5, 0.5), 1),
                    'status': 'normal',
                    'warehouse': 'A-3',
                    'moistureAbsorption': False,
                    'inventory': 8628
                },
                {
                    'name': 'SFWG76ME602',
                    'type': 'IC / RF',
                    'optimalRange': '20-60%',
                    'currentHumidity': round(53.2 + random.uniform(-0.5, 0.5), 1),
                    'status': 'normal',
                    'warehouse': 'A-3',
                    'moistureAbsorption': True,
                    'inventory': 9092
                },
                {
                    'name': 'SFH722FF302',
                    'type': 'IC / RF',
                    'optimalRange': '20-60%',
                    'currentHumidity': round(48.3 + random.uniform(-0.5, 0.5), 1),
                    'status': 'normal',
                    'warehouse': 'A-1',
                    'moistureAbsorption': True,
                    'inventory': -4034
                },
                {
                    'name': 'QPM7815A',
                    'type': 'IC / Power Management',
                    'optimalRange': '20-60%',
                    'currentHumidity': round(38.3 + random.uniform(-0.5, 0.5), 1),
                    'status': 'normal',
                    'warehouse': 'A-2',
                    'moistureAbsorption': True,
                    'inventory': 7407
                },
                {
                    'name': 'SKY58093-11',
                    'type': 'IC / RF',
                    'optimalRange': '20-60%',
                    'currentHumidity': round(38.4 + random.uniform(-0.5, 0.5), 1),
                    'status': 'normal',
                    'warehouse': 'A-2',
                    'moistureAbsorption': False,
                    'inventory': 7345
                },
                {
                    'name': 'SKY58098-11',
                    'type': 'IC / RF',
                    'optimalRange': '20-60%',
                    'currentHumidity': round(38.3 + random.uniform(-0.5, 0.5), 1),
                    'status': 'normal',
                    'warehouse': 'A-2',
                    'moistureAbsorption': False,
                    'inventory': 6696
                },
                {
                    'name': 'SKY58261-11',
                    'type': 'IC / RF',
                    'optimalRange': '20-60%',
                    'currentHumidity': round(38.5 + random.uniform(-0.5, 0.5), 1),
                    'status': 'normal',
                    'warehouse': 'A-2',
                    'moistureAbsorption': True,
                    'inventory': 7222
                }
            ]
            
            # 현재 환경 상태 (최신 데이터)
            current_environment = environment_history[0] if environment_history else {
                'temperature_c': 23.5,
                'humidity_percent': 65.2,
                'pm25_ug_m3': 12.3,
                'pm10_ug_m3': 18.7,
                'co2_ppm': 420
            }
            
            # 환경 상태 분석
            def analyze_environment_status(data):
                status = {
                    'temperature': 'normal',
                    'humidity': 'normal',
                    'pm25': 'normal',
                    'pm10': 'normal',
                    'co2': 'normal'
                }
                
                # 온도 상태 (18-25°C가 최적)
                if data['temperature_c'] < 18 or data['temperature_c'] > 25:
                    status['temperature'] = 'warning'
                
                # 습도 상태 (70% 이상이면 경고)
                if data['humidity_percent'] >= 70:
                    status['humidity'] = 'warning'
                
                # PM2.5 상태 (50㎍/m³ 이상이면 경고)
                if data['pm25_ug_m3'] >= 50:
                    status['pm25'] = 'warning'
                
                # PM10 상태 (100㎍/m³ 이상이면 경고)
                if data['pm10_ug_m3'] >= 100:
                    status['pm10'] = 'warning'
                
                # CO2 상태 (1000ppm 이상이면 경고)
                if data['co2_ppm'] >= 1000:
                    status['co2'] = 'warning'
                
                return status
            
            environment_status = analyze_environment_status(current_environment)
            
            # 경고가 있는 자재 수
            warning_materials = len([m for m in moisture_sensitive_materials if m['status'] == 'warning'])
            
            # 환경 데이터 통계
            temperatures = [d['temperature_c'] for d in environment_history]
            humidities = [d['humidity_percent'] for d in environment_history]
            pm25_values = [d['pm25_ug_m3'] for d in environment_history]
            pm10_values = [d['pm10_ug_m3'] for d in environment_history]
            co2_values = [d['co2_ppm'] for d in environment_history]
            
            result = {
                'current_environment': current_environment,
                'environment_status': environment_status,
                'environment_history': environment_history,
                'moisture_sensitive_materials': moisture_sensitive_materials,
                'warning_materials': warning_materials,
                'total_materials': len(moisture_sensitive_materials),
                
                # 환경 데이터 통계
                'temperature_stats': {
                    'current': current_environment['temperature_c'],
                    'average': round(sum(temperatures) / len(temperatures), 1),
                    'min': round(min(temperatures), 1),
                    'max': round(max(temperatures), 1),
                    'trend': 'stable' if abs(max(temperatures) - min(temperatures)) < 3 else 'variable'
                },
                'humidity_stats': {
                    'current': current_environment['humidity_percent'],
                    'average': round(sum(humidities) / len(humidities), 1),
                    'min': round(min(humidities), 1),
                    'max': round(max(humidities), 1),
                    'trend': 'stable' if abs(max(humidities) - min(humidities)) < 10 else 'variable'
                },
                'pm25_stats': {
                    'current': current_environment['pm25_ug_m3'],
                    'average': round(sum(pm25_values) / len(pm25_values), 1),
                    'min': round(min(pm25_values), 1),
                    'max': round(max(pm25_values), 1),
                    'trend': 'stable' if abs(max(pm25_values) - min(pm25_values)) < 2 else 'variable'
                },
                'pm10_stats': {
                    'current': current_environment['pm10_ug_m3'],
                    'average': round(sum(pm10_values) / len(pm10_values), 1),
                    'min': round(min(pm10_values), 1),
                    'max': round(max(pm10_values), 1),
                    'trend': 'stable' if abs(max(pm10_values) - min(pm10_values)) < 3 else 'variable'
                },
                'co2_stats': {
                    'current': current_environment['co2_ppm'],
                    'average': round(sum(co2_values) / len(co2_values)),
                    'min': min(co2_values),
                    'max': max(co2_values),
                    'trend': 'stable' if abs(max(co2_values) - min(co2_values)) < 20 else 'variable'
                },
                
                'data_source': 'simulation'
            }
            
            print(f"✅ MES 데이터 크롤링 완료: 환경 데이터 {len(environment_history)}개, 자재 {len(moisture_sensitive_materials)}개")
            print(f"📊 현재 환경: 온도 {current_environment['temperature_c']}°C, 습도 {current_environment['humidity_percent']}%")
            print(f"⚠️ 경고 자재: {warning_materials}개")
            
            return result
            
        except Exception as e:
            print(f"❌ MES 데이터 크롤링 오류: {e}")
            import traceback
            traceback.print_exc()
            
            # 기본 데이터 반환 (mse.tsx와 일치하는 구조)
            return {
                'current_environment': {
                    'temperature_c': 23.5,
                    'humidity_percent': 65.2,
                    'pm25_ug_m3': 12.3,
                    'pm10_ug_m3': 18.7,
                    'co2_ppm': 420
                },
                'environment_status': {
                    'temperature': 'normal',
                    'humidity': 'normal',
                    'pm25': 'normal',
                    'pm10': 'normal',
                    'co2': 'normal'
                },
                'environment_history': [
                    {
                        'timestamp': '2024-01-24 14:00:00',
                        'time': '14:00',
                        'temperature_c': 23.5,
                        'humidity_percent': 65.2,
                        'pm25_ug_m3': 12.3,
                        'pm10_ug_m3': 18.7,
                        'co2_ppm': 420,
                        'sensors': "정상"
                    },
                    {
                        'timestamp': '2024-01-24 13:00:00',
                        'time': '13:00',
                        'temperature_c': 23.8,
                        'humidity_percent': 64.8,
                        'pm25_ug_m3': 12.1,
                        'pm10_ug_m3': 18.5,
                        'co2_ppm': 418,
                        'sensors': "정상"
                    },
                    {
                        'timestamp': '2024-01-24 12:00:00',
                        'time': '12:00',
                        'temperature_c': 24.1,
                        'humidity_percent': 65.5,
                        'pm25_ug_m3': 12.5,
                        'pm10_ug_m3': 18.9,
                        'co2_ppm': 422,
                        'sensors': "정상"
                    },
                    {
                        'timestamp': '2024-01-24 11:00:00',
                        'time': '11:00',
                        'temperature_c': 23.9,
                        'humidity_percent': 65.0,
                        'pm25_ug_m3': 12.2,
                        'pm10_ug_m3': 18.6,
                        'co2_ppm': 419,
                        'sensors': "정상"
                    },
                    {
                        'timestamp': '2024-01-24 10:00:00',
                        'time': '10:00',
                        'temperature_c': 23.6,
                        'humidity_percent': 64.9,
                        'pm25_ug_m3': 12.0,
                        'pm10_ug_m3': 18.4,
                        'co2_ppm': 417,
                        'sensors': "정상"
                    },
                    {
                        'timestamp': '2024-01-24 09:00:00',
                        'time': '09:00',
                        'temperature_c': 23.4,
                        'humidity_percent': 65.1,
                        'pm25_ug_m3': 12.4,
                        'pm10_ug_m3': 18.8,
                        'co2_ppm': 421,
                        'sensors': "정상"
                    },
                    {
                        'timestamp': '2024-01-24 08:00:00',
                        'time': '08:00',
                        'temperature_c': 23.2,
                        'humidity_percent': 65.3,
                        'pm25_ug_m3': 12.6,
                        'pm10_ug_m3': 19.0,
                        'co2_ppm': 423,
                        'sensors': "정상"
                    }
                ],
                'moisture_sensitive_materials': [
                    {
                        'name': 'LFD211G44PK9F557',
                        'type': 'IC / Power Management',
                        'optimalRange': '20-60%',
                        'currentHumidity': 48.3,
                        'status': 'normal',
                        'warehouse': 'A-1',
                        'moistureAbsorption': True,
                        'inventory': 3482
                    },
                    {
                        'name': 'LST03-8P-H06-E20000',
                        'type': 'IC / Logic',
                        'optimalRange': '20-60%',
                        'currentHumidity': 48.3,
                        'status': 'normal',
                        'warehouse': 'A-1',
                        'moistureAbsorption': True,
                        'inventory': 5371
                    },
                    {
                        'name': 'SAFFW1G54AA0E3K',
                        'type': 'IC / Memory',
                        'optimalRange': '20-60%',
                        'currentHumidity': 48.6,
                        'status': 'normal',
                        'warehouse': 'A-1',
                        'moistureAbsorption': True,
                        'inventory': 4096
                    },
                    {
                        'name': 'AOCR33135A',
                        'type': 'IC / Audio',
                        'optimalRange': '20-60%',
                        'currentHumidity': 38.5,
                        'status': 'normal',
                        'warehouse': 'A-2',
                        'moistureAbsorption': True,
                        'inventory': 6610
                    },
                    {
                        'name': 'ET3138SE',
                        'type': 'IC / Communication',
                        'optimalRange': '20-60%',
                        'currentHumidity': 38.4,
                        'status': 'normal',
                        'warehouse': 'A-2',
                        'moistureAbsorption': False,
                        'inventory': 5535
                    },
                    {
                        'name': 'ET53128YB',
                        'type': 'IC / Communication',
                        'optimalRange': '20-60%',
                        'currentHumidity': 38.3,
                        'status': 'normal',
                        'warehouse': 'A-2',
                        'moistureAbsorption': True,
                        'inventory': 7010
                    },
                    {
                        'name': 'MAX17333X22+T',
                        'type': 'IC / Power Management',
                        'optimalRange': '20-60%',
                        'currentHumidity': 38.2,
                        'status': 'normal',
                        'warehouse': 'A-2',
                        'moistureAbsorption': True,
                        'inventory': 6982
                    },
                    {
                        'name': 'MXD8546CDS',
                        'type': 'IC / Logic',
                        'optimalRange': '20-60%',
                        'currentHumidity': 38.6,
                        'status': 'normal',
                        'warehouse': 'A-2',
                        'moistureAbsorption': True,
                        'inventory': 8075
                    },
                    {
                        'name': 'MXDLN14TS',
                        'type': 'IC / Logic',
                        'optimalRange': '20-60%',
                        'currentHumidity': 38.5,
                        'status': 'normal',
                        'warehouse': 'A-2',
                        'moistureAbsorption': True,
                        'inventory': 6211
                    },
                    {
                        'name': 'S2DOS15A01-6032',
                        'type': 'IC / Power Management',
                        'optimalRange': '20-60%',
                        'currentHumidity': 38.3,
                        'status': 'normal',
                        'warehouse': 'A-2',
                        'moistureAbsorption': True,
                        'inventory': 7951
                    },
                    {
                        'name': 'SM3012A',
                        'type': 'IC / Power Management',
                        'optimalRange': '20-60%',
                        'currentHumidity': 38.5,
                        'status': 'normal',
                        'warehouse': 'A-2',
                        'moistureAbsorption': True,
                        'inventory': 8016
                    },
                    {
                        'name': 'QM23030',
                        'type': 'IC / RF',
                        'optimalRange': '20-60%',
                        'currentHumidity': 53.4,
                        'status': 'normal',
                        'warehouse': 'A-3',
                        'moistureAbsorption': True,
                        'inventory': 7223
                    },
                    {
                        'name': 'QM42500A',
                        'type': 'IC / RF',
                        'optimalRange': '20-60%',
                        'currentHumidity': 53.6,
                        'status': 'normal',
                        'warehouse': 'A-3',
                        'moistureAbsorption': True,
                        'inventory': 9470
                    },
                    {
                        'name': 'SAYRZ634MBA0C3K',
                        'type': 'IC / Memory',
                        'optimalRange': '20-60%',
                        'currentHumidity': 53.6,
                        'status': 'normal',
                        'warehouse': 'A-3',
                        'moistureAbsorption': True,
                        'inventory': 8564
                    },
                    {
                        'name': 'SAYRZ725MBA0L3K',
                        'type': 'IC / Memory',
                        'optimalRange': '20-60%',
                        'currentHumidity': 53.4,
                        'status': 'normal',
                        'warehouse': 'A-3',
                        'moistureAbsorption': False,
                        'inventory': 9174
                    },
                    {
                        'name': 'SFHG76AF302',
                        'type': 'IC / RF',
                        'optimalRange': '20-60%',
                        'currentHumidity': 53.3,
                        'status': 'normal',
                        'warehouse': 'A-3',
                        'moistureAbsorption': True,
                        'inventory': 8528
                    },
                    {
                        'name': 'SFHG89BF302',
                        'type': 'IC / RF',
                        'optimalRange': '20-60%',
                        'currentHumidity': 53.4,
                        'status': 'normal',
                        'warehouse': 'A-3',
                        'moistureAbsorption': True,
                        'inventory': 8503
                    },
                    {
                        'name': 'SFML5Y0J001',
                        'type': 'IC / RF',
                        'optimalRange': '20-60%',
                        'currentHumidity': 53.5,
                        'status': 'normal',
                        'warehouse': 'A-3',
                        'moistureAbsorption': False,
                        'inventory': 6784
                    },
                    {
                        'name': 'SFML7F0J001',
                        'type': 'IC / RF',
                        'optimalRange': '20-60%',
                        'currentHumidity': 53.5,
                        'status': 'normal',
                        'warehouse': 'A-3',
                        'moistureAbsorption': False,
                        'inventory': 8628
                    },
                    {
                        'name': 'SFWG76ME602',
                        'type': 'IC / RF',
                        'optimalRange': '20-60%',
                        'currentHumidity': 53.2,
                        'status': 'normal',
                        'warehouse': 'A-3',
                        'moistureAbsorption': True,
                        'inventory': 9092
                    },
                    {
                        'name': 'SFH722FF302',
                        'type': 'IC / RF',
                        'optimalRange': '20-60%',
                        'currentHumidity': 48.3,
                        'status': 'normal',
                        'warehouse': 'A-1',
                        'moistureAbsorption': True,
                        'inventory': -4034
                    },
                    {
                        'name': 'QPM7815A',
                        'type': 'IC / Power Management',
                        'optimalRange': '20-60%',
                        'currentHumidity': 38.3,
                        'status': 'normal',
                        'warehouse': 'A-2',
                        'moistureAbsorption': True,
                        'inventory': 7407
                    },
                    {
                        'name': 'SKY58093-11',
                        'type': 'IC / RF',
                        'optimalRange': '20-60%',
                        'currentHumidity': 38.4,
                        'status': 'normal',
                        'warehouse': 'A-2',
                        'moistureAbsorption': False,
                        'inventory': 7345
                    },
                    {
                        'name': 'SKY58098-11',
                        'type': 'IC / RF',
                        'optimalRange': '20-60%',
                        'currentHumidity': 38.3,
                        'status': 'normal',
                        'warehouse': 'A-2',
                        'moistureAbsorption': False,
                        'inventory': 6696
                    },
                    {
                        'name': 'SKY58261-11',
                        'type': 'IC / RF',
                        'optimalRange': '20-60%',
                        'currentHumidity': 38.5,
                        'status': 'normal',
                        'warehouse': 'A-2',
                        'moistureAbsorption': True,
                        'inventory': 7222
                    }
                ],
                'warning_materials': 0,
                'total_materials': 30,
                'data_source': 'fallback'
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

# Flask API 엔드포인트 추가
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/crawler/menu1', methods=['GET'])
async def get_menu1_data():
    """Menu1 데이터 크롤링 API 엔드포인트"""
    try:
        result = await crawler.crawl_menu1_data()
        return jsonify(result)
    except Exception as e:
        print(f"❌ Menu1 API 오류: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/crawler/menu3', methods=['GET'])
async def get_menu3_data():
    """Menu3 데이터 크롤링 API 엔드포인트"""
    try:
        result = await crawler.crawl_menu3_data()
        return jsonify(result)
    except Exception as e:
        print(f"❌ Menu3 API 오류: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/crawler/menu3/defect-types', methods=['GET'])
async def get_defect_types_chart():
    """불량 유형별 분포 차트 데이터 API 엔드포인트"""
    try:
        result = await crawler.crawl_menu3_data()
        if result and 'defect_types_chart' in result:
            return jsonify({
                "defect_types_chart": result['defect_types_chart'],
                "total_defect_instances": result.get('total_defect_instances', 0),
                "data_source": result.get('data_source', 'unknown')
            })
        else:
            return jsonify({"error": "데이터를 찾을 수 없습니다"}), 404
    except Exception as e:
        print(f"❌ 불량 유형 차트 API 오류: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/crawler/mes', methods=['GET'])
async def get_mes_data():
    """MES 공장 환경 모니터링 데이터 API"""
    try:
        result = await crawler.crawl_mes_data()
        if result:
            return jsonify({
                'success': True,
                'data': result,
                'data_source': result.get('data_source', 'unknown')
            })
        else:
            return jsonify({
                'success': False,
                'error': 'MES 데이터를 찾을 수 없습니다.',
                'data_source': 'unknown'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data_source': 'error'
        }), 500

@app.route('/api/crawler/mse', methods=['GET'])
async def get_mse_data():
    """MSE 공장 환경 모니터링 데이터 API (MES와 동일)"""
    try:
        result = await crawler.crawl_mes_data()
        if result:
            return jsonify({
                'success': True,
                'data': result,
                'data_source': result.get('data_source', 'unknown')
            })
        else:
            return jsonify({
                'success': False,
                'error': 'MSE 데이터를 찾을 수 없습니다.',
                'data_source': 'unknown'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data_source': 'error'
        }), 500

if __name__ == "__main__":
    # 직접 실행시 테스트 수행
    asyncio.run(test_crawler())
    
    # Flask 서버 시작
    print("\n🚀 Flask 서버 시작 중...")
    print("📡 API 엔드포인트:")
    print("  - http://localhost:5001/api/crawler/menu1")
    print("  - http://localhost:5001/api/crawler/menu3")
    print("  - http://localhost:5001/api/crawler/menu3/defect-types")
    print("  - http://localhost:5001/api/crawler/mes")
    print("  - http://localhost:5001/api/crawler/mse")
    app.run(host='0.0.0.0', port=5001, debug=True)