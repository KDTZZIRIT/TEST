// Kakao Maps 전용 유틸 (싱글톤 로더 + 진단 로깅)
// 사용법:
//   import { loadKakaoSdk, KAKAO_JS_KEY } from "@/lib/kakao";
//   await loadKakaoSdk(KAKAO_JS_KEY, ["services"]);
//
// 환경변수 (.env.local):
//   NEXT_PUBLIC_KAKAO_JS_KEY=자바스크립트키
//
// 주의: 컴포넌트 파일들에 중복으로
//   declare global { interface Window { kakao: any } }
// 를 넣지 마세요. (타입 충돌 유발) — 본 파일에만 정의합니다.

export {};

declare global {
  interface Window {
    kakao?: any; // SDK 로드 전엔 undefined 가능하므로 옵셔널
  }
}

export const KAKAO_JS_KEY: string = process.env.NEXT_PUBLIC_KAKAO_JS_KEY ?? "";

let kakaoSdkPromise: Promise<void> | null = null;
let diagnosticsAttached = false;

/**
 * CSP/리소스 로드 에러를 콘솔에 더 자세히 찍어주는 리스너 (한 번만 등록)
 */
function attachDiagnosticsOnce() {
  if (diagnosticsAttached) return;
  diagnosticsAttached = true;

  // CSP 위반 로깅
  document.addEventListener("securitypolicyviolation", (e: any) => {
    // 일부 브라우저에서만 동작
    // eslint-disable-next-line no-console
    console.error("[CSP] violation:", {
      violatedDirective: e?.violatedDirective,
      effectiveDirective: e?.effectiveDirective,
      blockedURI: e?.blockedURI,
      sourceFile: e?.sourceFile,
      lineNumber: e?.lineNumber,
      sample: e?.sample,
    });
  });

  // 리소스 로드 에러 (스크립트 포함)
  window.addEventListener("error", (event: any) => {
    const target = event?.target as HTMLScriptElement | undefined;
    if (target && (target as any).src) {
      // eslint-disable-next-line no-console
      console.error("[ResourceError]", { src: (target as any).src });
    }
  }, true);
}

/**
 * 런타임에서 키/오리진 등 빠르게 점검할 때 사용
 */
export function debugKakaoEnv(appKey: string) {
  try {
    // eslint-disable-next-line no-console
    console.log("[KakaoDebug] origin:", window.location.origin);
  } catch (_) {}
  // eslint-disable-next-line no-console
  console.log("[KakaoDebug] appKey length:", appKey ? appKey.length : 0);
  // eslint-disable-next-line no-console
  console.log("[KakaoDebug] appKey prefix:", appKey ? appKey.slice(0, 4) : "(none)");
}

/**
 * Kakao Maps JS SDK를 단 한 번만 로드 (싱글톤)
 * - JavaScript 키만 사용 (REST 키 X)
 * - autoload=false + kakao.maps.load()로 초기화 보장
 */
export function loadKakaoSdk(appKey: string, libraries: string[] = ["services"]): Promise<void> {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("SSR"));
  }
  if (!appKey) {
    return Promise.reject(new Error("Kakao JS key missing"));
  }

  // 이미 로드된 경우
  if (window.kakao?.maps) return Promise.resolve();

  // 진행 중인 로드 재사용
  if (kakaoSdkPromise) return kakaoSdkPromise;

  attachDiagnosticsOnce();

  kakaoSdkPromise = new Promise<void>((resolve, reject) => {
    const ID = "kakao-maps-sdk";
    const prev = document.getElementById(ID);
    if (prev?.parentNode) prev.parentNode.removeChild(prev);

    const script = document.createElement("script");
    script.id = ID;
    script.async = true;
    script.defer = true;
    const libs = encodeURIComponent(libraries.join(","));
    const src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${appKey}&autoload=false&libraries=${libs}`;
    script.src = src;

    script.onerror = () => {
      // eslint-disable-next-line no-console
      console.error("Kakao SDK script load error details:", {
        src,
        origin: typeof window !== "undefined" ? window.location.origin : "(no window)",
      });
      reject(new Error("Kakao SDK script load error"));
    };

    script.onload = () => {
      try {
        window.kakao!.maps.load(() => resolve());
      } catch (e) {
        reject(e instanceof Error ? e : new Error("kakao.maps.load failed"));
      }
    };

    document.head.appendChild(script);
  });

  return kakaoSdkPromise;
}
