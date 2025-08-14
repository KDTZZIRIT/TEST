"use client";

import React, { useEffect, useRef, useState } from 'react';
import { MapPin, X, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { loadKakaoSdk } from '@/lib/kakao'; 

interface LocationSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLocationSelect: (address: string, lat: number, lng: number) => void;
}
const KAKAO_KEY = "83216edebad683a9aa10abdaeea5e542";

export default function LocationSearchModal({ isOpen, onClose, onLocationSelect }: LocationSearchModalProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<any>(null);
  const [marker, setMarker] = useState<any>(null);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [sdkLoading, setSdkLoading] = useState(false);
  const [sdkError, setSdkError] = useState<string | null>(null);

  // 디버깅: 모달 상태 변화 감지
  useEffect(() => {
    console.log('LocationSearchModal: isOpen 상태 변화:', isOpen);
    if (isOpen) {
      console.log('LocationSearchModal: 모달이 열렸습니다. mapRef.current:', mapRef.current);
    }
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;

    console.log('LocationSearchModal: 모달이 열렸습니다. 지도 초기화 시작...');
    setSdkLoading(true);
    setSdkError(null);

    const initializeMapAsync = async () => {
      try {
        await loadKakaoSdk(KAKAO_KEY, ["services"]);
        setSdkLoading(false);
        initializeMap();
      } catch (error) {
        console.error('LocationSearchModal: SDK 로드 또는 지도 초기화 실패:', error);
        setSdkLoading(false);
        setSdkError(`초기화 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`);
      }
    };

    initializeMapAsync();
  }, [isOpen]);

  // 지도 초기화 함수
  const initializeMap = () => {
    if (!window.kakao || !mapRef.current) {
      console.error('LocationSearchModal: window.kakao 또는 mapRef.current가 없습니다.');
      console.log('window.kakao:', window.kakao);
      console.log('mapRef.current:', mapRef.current);
      return;
    }

    console.log('LocationSearchModal: 지도 초기화 시작');
    
    try {
      // 지도를 담을 영역의 DOM 레퍼런스
      const container = mapRef.current;
      console.log('LocationSearchModal: 지도 컨테이너:', container);
      
      // 지도를 생성할 때 필요한 기본 옵션
      const options = {
        center: new window.kakao.maps.LatLng(37.5665, 126.9780), // 서울시청 중심좌표
        level: 3 // 지도의 레벨(확대, 축소 정도)
      };

      // 지도 생성 및 객체 리턴
      const kakaoMap = new window.kakao.maps.Map(container, options);
      console.log('LocationSearchModal: 지도 생성 성공:', kakaoMap);
      setMap(kakaoMap);

      // 지도 클릭 이벤트
      window.kakao.maps.event.addListener(kakaoMap, 'click', function(mouseEvent: any) {
        const latlng = mouseEvent.latLng;
        
        // 기존 마커 제거
        if (marker) {
          marker.setMap(null);
        }

        // 새 마커 생성
        const newMarker = new window.kakao.maps.Marker({
          position: latlng
        });
        newMarker.setMap(kakaoMap);
        setMarker(newMarker);

        // 주소 검색 (services 라이브러리 사용)
        const geocoder = new window.kakao.maps.services.Geocoder();
        geocoder.coord2Address(latlng.getLng(), latlng.getLat(), (result: any, status: any) => {
          if (status === window.kakao.maps.services.Status.OK) {
            const address = result[0].address.address_name;
            onLocationSelect(address, latlng.getLat(), latlng.getLng());
            onClose();
          }
        });
      });
    } catch (error) {
      console.error('LocationSearchModal: 지도 생성 실패:', error);
      setSdkError(`지도 생성 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`);
    }
  };

  // 검색 기능 (services 라이브러리 사용)
  const searchLocation = () => {
    console.log('LocationSearchModal: 검색 시작:', searchKeyword);
    
    if (!searchKeyword.trim()) {
      console.log('LocationSearchModal: 검색어가 비어있습니다.');
      return;
    }
    
    if (!window.kakao || !window.kakao.maps) {
      console.error('LocationSearchModal: window.kakao.maps가 로드되지 않았습니다.');
      setSdkError('카카오맵이 아직 로드되지 않았습니다. 잠시 후 다시 시도해주세요.');
      return;
    }

    try {
      // 장소 검색 객체를 생성합니다
      const places = new window.kakao.maps.services.Places();
      console.log('LocationSearchModal: Places 객체 생성됨');
      
      // 키워드로 장소를 검색합니다
      places.keywordSearch(searchKeyword, (results: any, status: any) => {
        console.log('LocationSearchModal: 검색 결과 상태:', status);
        console.log('LocationSearchModal: 검색 결과:', results);
        
        if (status === window.kakao.maps.services.Status.OK) {
          setSearchResults(results);
          console.log('LocationSearchModal: 검색 결과 설정됨, 개수:', results.length);
        } else if (status === window.kakao.maps.services.Status.ZERO_RESULT) {
          setSearchResults([]);
          console.log('LocationSearchModal: 검색 결과가 없습니다.');
        } else {
          setSearchResults([]);
          console.log('LocationSearchModal: 검색 실패, 상태:', status);
        }
      });
    } catch (error) {
      console.error('LocationSearchModal: 검색 중 오류 발생:', error);
      setSdkError(`검색 중 오류가 발생했습니다: ${error instanceof Error ? error.message : '알 수 없는 오류'}`);
    }
  };

  // 검색 결과 선택
  const selectSearchResult = (place: any) => {
    if (!map || !window.kakao || !window.kakao.maps) {
      console.error('LocationSearchModal: 지도 또는 카카오맵이 로드되지 않았습니다.');
      setSdkError('지도가 로드되지 않았습니다. 잠시 후 다시 시도해주세요.');
      return;
    }

    try {
      // 검색된 장소의 좌표로 지도 중심을 이동시킵니다
      const latlng = new window.kakao.maps.LatLng(place.y, place.x);
      
      // 지도 중심 이동
      map.setCenter(latlng);
      
      // 기존 마커 제거
      if (marker) {
        marker.setMap(null);
      }

      // 새 마커 생성
      const newMarker = new window.kakao.maps.Marker({
        position: latlng
      });
      newMarker.setMap(map);
      setMarker(newMarker);

      // 선택된 위치 정보를 부모 컴포넌트로 전달
      onLocationSelect(place.address_name, place.y, place.x);
      setSearchResults([]);
      setSearchKeyword('');
      onClose();
    } catch (error) {
      console.error('LocationSearchModal: 위치 선택 중 오류 발생:', error);
      setSdkError(`위치 선택 중 오류가 발생했습니다: ${error instanceof Error ? error.message : '알 수 없는 오류'}`);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl h-[80vh] relative flex flex-col">
        {/* 헤더 */}
        <div className="flex items-center justify-between p-6 border-b flex-shrink-0">
          <div className="flex items-center gap-3">
            <MapPin className="w-6 h-6 text-blue-600" />
            <div>
              <h2 className="text-2xl font-bold text-gray-900">회사 위치 선택</h2>
              <div className="flex items-center gap-2 mt-1">
                {sdkLoading && (
                  <div className="flex items-center gap-1 text-sm text-blue-600">
                    <div className="animate-spin rounded-full h-3 w-3 border-b border-blue-600"></div>
                    <span>SDK 로딩 중...</span>
                  </div>
                )}
                {sdkError && (
                  <div className="flex items-center gap-1 text-sm text-red-600">
                    <span>⚠️ {sdkError}</span>
                  </div>
                )}
                {!sdkLoading && !sdkError && map && (
                  <div className="flex items-center gap-1 text-sm text-green-600">
                    <span>✓ 지도 준비됨</span>
                  </div>
                )}
              </div>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <X className="w-6 h-6" />
          </Button>
        </div>

        {/* 검색 영역 */}
        <div className="p-6 border-b flex-shrink-0">
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && searchLocation()}
                placeholder="주소를 검색하세요 (예: 강남구 테헤란로)"
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <Button
              onClick={searchLocation}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              검색
            </Button>
          </div>
          
                     {/* 검색 결과 */}
          {searchResults.length > 0 && (
            <div className="mt-4 max-h-40 overflow-y-auto border border-gray-200 rounded-lg bg-white">
              <div className="p-2 bg-blue-50 border-b border-blue-200 text-blue-700 text-sm font-medium">
                검색 결과 ({searchResults.length}개)
              </div>
              {searchResults.map((place, index) => (
                <div
                  key={index}
                  onClick={() => selectSearchResult(place)}
                  className="p-3 hover:bg-blue-50 cursor-pointer border-b border-gray-100 last:border-b-0 transition-colors"
                >
                  <div className="font-medium text-gray-900">{place.place_name}</div>
                  <div className="text-sm text-gray-600">{place.address_name}</div>
                </div>
              ))}
            </div>
          )}
          {searchKeyword && searchResults.length === 0 && (
            <div className="mt-4 p-3 text-center text-gray-500 bg-gray-50 rounded-lg border">
              <Search className="w-5 h-5 mx-auto mb-2 text-gray-400" />
              <p className="font-medium mb-1">검색 결과가 없습니다</p>
              <p className="text-sm">다른 키워드로 검색해보세요</p>
            </div>
          )}
        </div>

        {/* 지도 영역 */}
        <div className="flex-1 p-6">
          <div 
            ref={mapRef} 
            className="w-full rounded-lg border-2 border-gray-300 bg-gray-100"
            style={{ 
              width: '100%', 
              height: '400px',
              minHeight: '400px',
              position: 'relative',
              overflow: 'hidden'
            }}
          />
          
          {/* 로딩 상태 표시 */}
          {sdkLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded-lg">
              <div className="text-center text-gray-500">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-2"></div>
                <p>카카오맵 SDK를 로딩하는 중...</p>
              </div>
            </div>
          )}
          
          {/* 에러 상태 표시 */}
          {sdkError && !map && (
            <div className="absolute inset-0 flex items-center justify-center bg-red-50 rounded-lg border-2 border-red-200">
              <div className="text-center text-red-600 p-4">
                <MapPin className="w-12 h-12 mx-auto mb-2 text-red-400" />
                <p className="font-medium mb-2">지도 로딩 실패</p>
                <p className="text-sm mb-3">{sdkError}</p>
                                 <Button 
                   onClick={() => {
                     setSdkError(null);
                     setSdkLoading(true);
                     const initializeMapAsync = async () => {
                       try {
                         await loadKakaoSdk(KAKAO_KEY, ["services"]);
                         setSdkLoading(false);
                         initializeMap();
                       } catch (error) {
                         console.error('LocationSearchModal: 재시도 실패:', error);
                         setSdkLoading(false);
                         setSdkError(`재시도 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`);
                       }
                     };
                     initializeMapAsync();
                   }}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded-lg"
                >
                  다시 시도
                </Button>
              </div>
            </div>
          )}
          
          {/* 지도 로딩 중 표시 */}
          {!sdkLoading && !sdkError && !map && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded-lg">
              <div className="text-center text-gray-500">
                <MapPin className="w-12 h-12 mx-auto mb-2" />
                <p>지도를 불러오는 중...</p>
              </div>
            </div>
          )}
        </div>

        {/* 하단 안내 */}
        <div className="p-6 border-t bg-gray-50 flex-shrink-0">
          <div className="text-sm text-gray-600">
            <p>• 검색창에 주소나 장소명을 입력하여 검색하거나, 지도를 직접 클릭하여 위치를 선택하세요.</p>
            <p>• 검색 결과에서 원하는 장소를 클릭하면 지도가 해당 위치로 이동하고 마커가 표시됩니다.</p>
            <p>• 선택한 위치의 주소는 회사 주소 입력칸에 자동으로 입력됩니다.</p>
          </div>
        </div>
      </div>
    </div>
  );
} 