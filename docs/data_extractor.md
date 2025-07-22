# PDF 범용 데이터 추출 파이프라인 기획서

## 📋 프로젝트 개요

### 목적
어떤 형태의 PDF 문서가 입력되어도 **"일단 뭔가는 추출한다"**는 원칙 하에, 실패율 0%를 목표로 하는 범용 PDF 데이터 추출 파이프라인을 구축한다.

### 핵심 가치
- **Universal**: 모든 PDF 형태 지원 (텍스트, 스캔본, 복합문서)
- **Resilient**: 절대 실패하지 않는 다중 fallback 구조
- **Practical**: 완벽하지 않아도 즉시 사용 가능한 결과 제공

---

## 🎯 프로젝트 목표

### 1차 목표: 범용 추출기 (Universal Extractor)
```
성공률 100% = 어떤 PDF든 뭔가는 나온다
```

| 우선순위 | 목표 | 성공 기준 |
|---------|------|-----------|
| P0 | 모든 PDF에서 텍스트 추출 | 실패율 0% |
| P1 | 표/이미지 등 구조적 요소 추출 | 추출율 80% 이상 |
| P2 | 메타데이터 및 레이아웃 정보 | 추출율 60% 이상 |

### 2차 목표: 점진적 구조화 (Progressive Structuring)
- 문서 유형 자동 분류
- 템플릿 기반 필드 매핑
- 데이터 검증 및 정제

---

## ⚡ 기술 아키텍처

### 핵심 엔진: docling 중심 Multi-Engine 구조

```
[PDF 입력]
    ↓
[1차: docling 추출 시도]
    ↓ (실패 시)
[2차: pdfplumber + OCR]
    ↓ (실패 시)  
[3차: 순수 OCR (Tesseract/CLOVA)]
    ↓
[통합 결과 출력]
```

### 기술 스택

| 구분 | 기술 | 역할 |
|------|------|------|
| **메인 엔진** | docling | 통합 PDF 분석 및 OCR 판단 |
| **보조 엔진** | pdfplumber | 텍스트 기반 PDF 처리 |
| **OCR** | Tesseract, CLOVA OCR | 스캔 문서 텍스트 인식 |
| **후처리** | Python (pandas, re) | 데이터 정제 및 구조화 |
| **출력** | JSON, CSV | 다양한 포맷 지원 |

---

## 🏗 시스템 설계

### 처리 파이프라인

#### 1단계: 문서 분석 및 전처리
```python
def analyze_pdf(file_path):
    return {
        "pages": int,
        "has_text": bool,
        "has_images": bool, 
        "estimated_scan_pages": list,
        "file_size": int,
        "processing_strategy": str
    }
```

#### 2단계: 다중 추출 엔진
```python
def multi_engine_extract(pdf_path, analysis_result):
    engines = [
        ("docling", docling_extract),
        ("pdfplumber", pdfplumber_extract), 
        ("ocr_tesseract", tesseract_extract),
        ("ocr_clova", clova_extract)
    ]
    
    for engine_name, extractor in engines:
        try:
            result = extractor(pdf_path)
            if is_valid_result(result):
                return result, engine_name
        except Exception as e:
            log_error(engine_name, e)
            continue
    
    # 최후의 수단: 빈 구조체라도 반환
    return empty_result_structure(), "fallback"
```

#### 3단계: 결과 통합 및 검증
```python
def validate_and_merge(extraction_results):
    return {
        "status": "success|partial|fallback",
        "confidence_score": float,
        "raw_content": {...},
        "structured_data": {...},
        "extraction_metadata": {...}
    }
```

### 출력 데이터 구조

```json
{
  "extraction_info": {
    "file_name": "document.pdf", 
    "processing_time": "2.3s",
    "engine_used": ["docling", "tesseract"],
    "status": "success",
    "confidence": 0.85
  },
  "content": {
    "raw_text": "전체 텍스트 내용...",
    "pages": [
      {
        "page_num": 1,
        "text": "페이지별 텍스트",
        "tables": [...],
        "images": [...]
      }
    ],
    "tables": [
      {
        "page": 1,
        "data": [["컬럼1", "컬럼2"], ["값1", "값2"]]
      }
    ],
    "images": [
      {
        "page": 2, 
        "type": "chart",
        "extracted_text": "OCR 결과"
      }
    ]
  },
  "metadata": {
    "total_pages": 5,
    "creation_date": "2023-06-30",
    "author": "...",
    "text_extraction_method": "native|ocr|hybrid"
  }
}
```

---

## 🛠 구현 계획

### Phase 1: MVP (4주)
**목표: "절대 실패하지 않는" 기본 추출기**

| 주차 | 작업 내용 | 산출물 |
|------|-----------|--------|
| 1주 | docling 기본 설치 및 테스트 | 기본 추출 스크립트 |
| 2주 | multi-engine fallback 구조 구현 | 다중 엔진 파이프라인 |
| 3주 | 에러 핸들링 및 로깅 시스템 | 안정성 확보 |
| 4주 | 테스트 케이스 및 성능 검증 | MVP 완성 |

### Phase 2: 고도화 (6주)
**목표: 정확도 향상 및 구조화**

- 문서 유형 자동 분류
- 템플릿 기반 필드 추출
- 웹 UI 개발
- 배치 처리 최적화

### Phase 3: 운영화 (2주)
**목표: 실제 서비스 배포**

- Docker 컨테이너화
- API 서버 구축
- 모니터링 및 알림 시스템

---

## 🧪 테스트 전략

### 테스트 케이스 분류

| 유형 | 설명 | 테스트 파일 예시 |
|------|------|------------------|
| **텍스트 PDF** | 일반 텍스트 문서 | 계약서, 보고서 |
| **스캔 PDF** | 이미지만 있는 문서 | 스캔된 서류 |
| **복합 PDF** | 텍스트+이미지+표 | 제안서, 카탈로그 |
| **손상된 PDF** | 깨지거나 암호화된 파일 | 에러 케이스 |
| **대용량 PDF** | 100페이지 이상 | 매뉴얼, 연구보고서 |

### 성공 기준

```python
# 필수 통과 조건
assert extraction_result["status"] != "failed"  # 절대 실패 금지
assert len(extraction_result["content"]["raw_text"]) > 0  # 뭔가는 나와야 함

# 품질 기준  
if pdf_type == "text_based":
    assert confidence_score >= 0.9
elif pdf_type == "scan_based": 
    assert confidence_score >= 0.7
```

---

## 📊 예상 성과

### 정량적 목표

| 지표 | 목표값 | 측정 방법 |
|------|--------|-----------|
| **처리 성공률** | 100% | 실패 케이스 0건 |
| **텍스트 추출 정확도** | 85%+ | 샘플 문서 대상 수동 검증 |
| **처리 속도** | 페이지당 2초 이내 | 평균 처리 시간 측정 |
| **지원 문서 유형** | 10+ 종류 | 계약서, 청구서, 보고서 등 |

### 정성적 기대 효과

- **즉시 활용 가능**: 완벽하지 않아도 바로 쓸 수 있는 데이터 제공
- **운영 안정성**: 예외 상황에서도 서비스 중단 없음  
- **확장성**: 새로운 문서 유형 쉽게 추가 가능
- **비용 효율**: 수작업 대비 80% 시간 단축

---

## 🚀 향후 발전 방향

### 단기 (3개월)
- LLM 연동으로 비정형 데이터 구조화
- 웹 기반 검수 도구 개발
- 다국어 문서 지원 확대

### 중기 (6개월)  
- AI 기반 문서 분류 자동화
- 실시간 처리 API 서비스
- 엔터프라이즈 연동 (ERP, CRM)

### 장기 (1년)
- 멀티모달 AI 연동 (이미지, 차트 해석)
- 블록체인 기반 문서 검증
- 글로벌 서비스 확장

---

## 💡 리스크 관리

### 기술적 리스크

| 리스크 | 영향도 | 대응 방안 |
|--------|--------|-----------|
| docling 의존성 이슈 | 중간 | 다중 엔진 fallback 구조로 완화 |
| OCR 정확도 한계 | 중간 | 여러 OCR 엔진 조합 사용 |
| 대용량 파일 처리 | 높음 | 스트리밍 처리 및 분할 처리 |

### 운영적 리스크

| 리스크 | 영향도 | 대응 방안 |
|--------|--------|-----------|
| 저작권 문제 | 높음 | 데이터 보안 및 접근 권한 관리 |
| 개인정보 노출 | 높음 | 민감정보 자동 마스킹 기능 |
| 서버 과부하 | 중간 | 큐 시스템 및 부하 분산 |

---

## ✅ 결론

본 프로젝트는 **"실패하지 않는 PDF 추출기"**라는 명확한 가치 제안을 통해, 완벽함보다는 실용성과 안정성에 초점을 맞춘 시스템을 구축한다. docling을 중심으로 한 다중 엔진 구조를 통해 어떤 형태의 PDF든 반드시 결과를 도출하며, 점진적 개선을 통해 정확도를 지속적으로 향상시킨다.

이를 통해 문서 처리 업무의 자동화 기반을 마련하고, 향후 AI 기반 고도화의 토대가 될 것으로 기대한다.