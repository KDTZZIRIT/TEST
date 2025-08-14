"use client";

import React, { useEffect, useRef, useState } from 'react';
import { MapPin } from 'lucide-react';
import { loadKakaoSdk } from '@/lib/kakao';
interface KakaoMapProps {
  onLocationSelect: (address: string, lat: number, lng: number) => void;
  selectedLocation?: { address: string; lat: number; lng: number };
}

const KAKAO_KEY = process.env.NEXT_PUBLIC_KAKAO_JS_KEY ?? "";

export default function KakaoMap({ onLocationSelect, selectedLocation }: KakaoMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<any>(null);
  const [marker, setMarker] = useState<any>(null);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);

  useEffect(() => {
    let cancelled = false;
  
    (async () => {
      try {
        await loadKakaoSdk(KAKAO_KEY, ["services"]);
        if (cancelled || !mapRef.current) return;
  
        const options = {
          center: new window.kakao.maps.LatLng(37.5665, 126.9780),
          level: 3,
        };
        const kakaoMap = new window.kakao.maps.Map(mapRef.current, options);
        setMap(kakaoMap);
  
        // 지도 클릭 이벤트
        window.kakao.maps.event.addListener(kakaoMap, 'click', (mouseEvent: any) => {
          const latlng = mouseEvent.latLng;
  
          if (marker) marker.setMap(null);
  
          const newMarker = new window.kakao.maps.Marker({ position: latlng });
          newMarker.setMap(kakaoMap);
          setMarker(newMarker);
  
          const geocoder = new window.kakao.maps.services.Geocoder();
          geocoder.coord2Address(latlng.getLng(), latlng.getLat(), (result: any, status: any) => {
            if (status === window.kakao.maps.services.Status.OK) {
              const address = result[0].address.address_name;
              onLocationSelect(address, latlng.getLat(), latlng.getLng());
            }
          });
        });
      } catch (e) {
        console.error("KakaoMap: SDK load/init failed:", e);
      }
    })();
  
    return () => { cancelled = true; };
  }, []);
  

  // 검색 기능
  const searchLocation = () => {
    if (!searchKeyword.trim() || !window.kakao) return;

    const places = new window.kakao.maps.services.Places();
    places.keywordSearch(searchKeyword, (results: any, status: any) => {
      if (status === window.kakao.maps.services.Status.OK) {
        setSearchResults(results);
      }
    });
  };

  // 검색 결과 선택
  const selectSearchResult = (place: any) => {
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

    onLocationSelect(place.address_name, place.y, place.x);
    setSearchResults([]);
    setSearchKeyword('');
  };

  return (
    <div className="w-full">
      <div className="mb-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && searchLocation()}
            placeholder="주소를 검색하세요"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={searchLocation}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            검색
          </button>
        </div>
        
        {/* 검색 결과 */}
        {searchResults.length > 0 && (
          <div className="mt-2 max-h-40 overflow-y-auto border border-gray-200 rounded-md">
            {searchResults.map((place, index) => (
              <div
                key={index}
                onClick={() => selectSearchResult(place)}
                className="p-2 hover:bg-gray-100 cursor-pointer border-b border-gray-100 last:border-b-0"
              >
                <div className="font-medium">{place.place_name}</div>
                <div className="text-sm text-gray-600">{place.address_name}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 지도 */}
      <div 
        ref={mapRef} 
        className="w-full h-64 rounded-lg border border-gray-300"
      />

      {/* 선택된 위치 표시 */}
      {selectedLocation && (
        <div className="mt-3 p-3 bg-gray-50 rounded-md">
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-blue-600" />
            <span className="text-sm font-medium">선택된 위치:</span>
          </div>
          <div className="mt-1 text-sm text-gray-600">{selectedLocation.address}</div>
        </div>
      )}
    </div>
  );
} 