// src/services/modelGateway.ts
// Flask 모델 서버와의 통신을 담당하는 게이트웨이 서비스
// 박세진 작성

import { http } from "../clients/http";

// 예측 요청 인터페이스
interface PredictRequest {
  years: number[];
  service_days: number;
  pack_size: number;
  moq: number;
  holding_rate_per_day: number;
  penalty_multiplier: number;
}

// 예측 옵션 인터페이스
interface PredictOptions {
  limit: number;
  warningOnly: boolean;
}

// 모델 메타데이터 응답 인터페이스
interface ModelMeta {
  model_name: string;
  version: string;
  last_trained: string;
  accuracy?: number;
  features?: string[];
}

// 예측 결과 인터페이스
interface PredictResult {
  part_id: number;
  part_number: string;
  predicted_demand: number;
  current_stock: number;
  recommended_order: number;
  confidence: number;
  warning_level: 'low' | 'medium' | 'high';
  details?: any;
}

export class FlaskModelGateway {
  private readonly baseUrl: string;

  constructor() {
    // 환경변수에서 Flask 서버 URL 가져오기, 기본값 설정
    this.baseUrl = process.env.FLASK_MODEL_URL || "http://127.0.0.1:5001";
  }

  /**
   * Flask 모델 서버 헬스 체크
   */
  async health(): Promise<boolean> {
    try {
      const response = await http.get(`${this.baseUrl}/health`, {
        timeout: 5000, // 5초 타임아웃
      });
      return response.status === 200 && response.data?.status === "healthy";
    } catch (error) {
      console.error("Model server health check failed:", error);
      return false;
    }
  }

  /**
   * 모델 메타데이터 조회
   */
  async meta(): Promise<ModelMeta> {
    try {
      const response = await http.get(`${this.baseUrl}/model/meta`);
      
      if (response.status !== 200) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return response.data;
    } catch (error: any) {
      console.error("Failed to fetch model metadata:", error);
      throw new Error(`Model metadata request failed: ${error.message}`);
    }
  }

  /**
   * 예측 요청 실행
   */
  async predict(
    request: PredictRequest, 
    options: PredictOptions
  ): Promise<PredictResult[]> {
    try {
      // 요청 데이터 검증
      this.validatePredictRequest(request);

      const response = await http.post(`${this.baseUrl}/predict`, {
        ...request,
        options: {
          limit: options.limit,
          warning_only: options.warningOnly,
        }
      });

      if (response.status !== 200) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // 응답 데이터 검증 및 변환
      const results = this.transformPredictResponse(response.data);
      
      // limit 옵션 적용
      const limitedResults = results.slice(0, options.limit);
      
      // warningOnly 옵션 적용
      if (options.warningOnly) {
        return limitedResults.filter(result => 
          result.warning_level === 'medium' || result.warning_level === 'high'
        );
      }

      return limitedResults;
    } catch (error: any) {
      console.error("Prediction request failed:", error);
      throw new Error(`Prediction failed: ${error.message}`);
    }
  }

  /**
   * 요청 데이터 검증
   */
  private validatePredictRequest(request: PredictRequest): void {
    if (!Array.isArray(request.years) || request.years.length === 0) {
      throw new Error("Years must be a non-empty array");
    }

    if (request.service_days <= 0) {
      throw new Error("Service days must be positive");
    }

    if (request.pack_size <= 0) {
      throw new Error("Pack size must be positive");
    }

    if (request.holding_rate_per_day < 0) {
      throw new Error("Holding rate per day cannot be negative");
    }

    if (request.penalty_multiplier < 0) {
      throw new Error("Penalty multiplier cannot be negative");
    }
  }

  /**
   * Flask 응답을 표준 형식으로 변환
   */
  private transformPredictResponse(data: any): PredictResult[] {
    if (!Array.isArray(data.predictions)) {
      throw new Error("Invalid response format: predictions array not found");
    }

    return data.predictions.map((item: any, index: number) => {
      // 안전한 데이터 변환
      const result: PredictResult = {
        part_id: Number(item.part_id || index + 1),
        part_number: String(item.part_number || `PART_${index + 1}`),
        predicted_demand: Number(item.predicted_demand || 0),
        current_stock: Number(item.current_stock || 0),
        recommended_order: Number(item.recommended_order || 0),
        confidence: Math.min(Math.max(Number(item.confidence || 0), 0), 1), // 0-1 범위로 제한
        warning_level: this.determineWarningLevel(item),
        details: item.details || null,
      };

      return result;
    });
  }

  /**
   * 경고 레벨 결정 로직
   */
  private determineWarningLevel(item: any): 'low' | 'medium' | 'high' {
    const stockRatio = Number(item.current_stock || 0) / Number(item.predicted_demand || 1);
    const confidence = Number(item.confidence || 0);

    // 재고가 예측 수요의 20% 미만이고 신뢰도가 높으면 high
    if (stockRatio < 0.2 && confidence > 0.8) {
      return 'high';
    }
    
    // 재고가 예측 수요의 50% 미만이면 medium
    if (stockRatio < 0.5) {
      return 'medium';
    }

    return 'low';
  }
}