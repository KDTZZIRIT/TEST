#!/usr/bin/env python3
"""
ZZIRIT-FLASK 서버 빠른 테스트 스크립트
"""

import requests
import json
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:5100"

def test_endpoint(endpoint: str, method: str = "GET", data: Dict[Any, Any] = None) -> Dict[str, Any]:
    """엔드포인트 테스트"""
    try:
        url = f"{BASE_URL}{endpoint}"
        
        if method.upper() == "GET":
            response = requests.get(url, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            return {"success": False, "error": f"지원하지 않는 메소드: {method}"}
        
        result = {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "endpoint": endpoint,
            "method": method
        }
        
        if response.status_code == 200:
            try:
                result["data"] = response.json()
            except:
                result["data"] = response.text[:200]
        else:
            result["error"] = response.text[:200]
            
        return result
        
    except Exception as e:
        return {
            "success": False,
            "endpoint": endpoint,
            "method": method,
            "error": str(e)
        }

def main():
    print("🧪 ZZIRIT-FLASK 서버 테스트 시작...")
    print("=" * 60)
    
    # 테스트할 엔드포인트 목록
    tests = [
        # 기본 엔드포인트
        {"endpoint": "/", "method": "GET", "name": "메인 페이지"},
        {"endpoint": "/health", "method": "GET", "name": "헬스체크"},
        
        # 완성된 API (chat1, api_server)
        {"endpoint": "/api/chat", "method": "POST", "name": "메인 채팅", 
         "data": {"messages": [{"role": "user", "content": "안녕하세요"}]}},
        {"endpoint": "/api/predict", "method": "POST", "name": "AI 예측",
         "data": {"limit": 10}},
        
        # 개발중인 API (chat4)
        {"endpoint": "/api/inventory-chat", "method": "POST", "name": "재고 채팅",
         "data": {"message": "재고 현황을 알려주세요"}},
    ]
    
    results = []
    success_count = 0
    
    for test in tests:
        print(f"\n🔍 테스트: {test['name']}")
        print(f"   엔드포인트: {test['endpoint']}")
        
        result = test_endpoint(
            test["endpoint"], 
            test["method"], 
            test.get("data")
        )
        
        results.append({**result, "name": test["name"]})
        
        if result["success"]:
            print(f"   ✅ 성공 (HTTP {result['status_code']})")
            success_count += 1
            
            # 간단한 응답 정보 표시
            if "data" in result and isinstance(result["data"], dict):
                if "status" in result["data"]:
                    print(f"   📋 상태: {result['data']['status']}")
                if "message" in result["data"]:
                    msg = result["data"]["message"]
                    if isinstance(msg, dict) and "content" in msg:
                        print(f"   💬 응답: {msg['content'][:100]}...")
                    elif isinstance(msg, str):
                        print(f"   💬 응답: {msg[:100]}...")
        else:
            print(f"   ❌ 실패: {result.get('error', '알 수 없는 오류')}")
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    
    total_tests = len(tests)
    success_rate = (success_count / total_tests) * 100
    
    print(f"총 테스트: {total_tests}개")
    print(f"성공: {success_count}개")
    print(f"실패: {total_tests - success_count}개")
    print(f"성공률: {success_rate:.1f}%")
    
    # 실패한 테스트 상세 정보
    failed_tests = [r for r in results if not r["success"]]
    if failed_tests:
        print(f"\n❌ 실패한 테스트:")
        for test in failed_tests:
            print(f"  - {test['name']}: {test.get('error', '알 수 없는 오류')}")
    
    # 성공한 테스트
    successful_tests = [r for r in results if r["success"]]
    if successful_tests:
        print(f"\n✅ 성공한 테스트:")
        for test in successful_tests:
            print(f"  - {test['name']}")
    
    print("\n" + "=" * 60)
    
    if success_rate >= 80:
        print("🎉 서버가 정상적으로 작동하고 있습니다!")
        sys.exit(0)
    elif success_rate >= 50:
        print("⚠️ 일부 기능에 문제가 있습니다. 로그를 확인해주세요.")
        sys.exit(1)
    else:
        print("💥 서버에 심각한 문제가 있습니다.")
        sys.exit(2)

if __name__ == "__main__":
    main()