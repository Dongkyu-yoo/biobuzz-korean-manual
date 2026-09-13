# BIOBUZZ 한국어 매뉴얼 — GitBook 업로드 안내

이 묶음은 첨부된 HTML의 내용을 GitBook용으로 변환한 것입니다. 원문 대조 번역이나 규칙의 최신성 검증은 수행하지 않았습니다.

## 1. GitHub에 파일 올리기

1. ZIP을 압축 해제합니다.
2. 매뉴얼 전용 GitHub 저장소를 준비합니다. 저장소 이름 예: `biobuzz-korean-manual`.
3. 압축 해제한 폴더 안의 파일과 폴더를 저장소 최상위에 올립니다. ZIP 자체를 올리는 방식이 아닙니다.
4. 저장소 최상위에 `.gitbook.yaml`, `docs/`가 있고, `docs/` 안에 `README.md`, `SUMMARY.md`, `section-01.md`부터 `section-16.md`, `assets/`가 있는지 확인합니다.

GitHub 웹 업로드에서 파일 수 제한이 나타나면 이미지 폴더와 문서 파일을 나누어 업로드할 수 있습니다. `.gitbook.yaml`도 반드시 포함해야 합니다. 업로드가 끝난 뒤 GitBook을 연결하십시오.

## 2. GitBook 연결하기

1. GitBook에서 새 사이트와 비어 있는 문서 공간(Space)을 만듭니다.
2. 사이트의 **Git Sync**에서 **GitHub**를 연결합니다.
3. 매뉴얼 저장소와 파일을 올린 브랜치(보통 `main`)를 선택합니다.
4. 초기 동기화 방향을 **GitHub → GitBook**으로 선택합니다.
5. **Project directory**는 저장소 루트로 둡니다. 이 묶음의 `.gitbook.yaml`은 루트에 있고, 문서 경로를 `./docs/`로 지정합니다.
6. **Content mapping**을 요구하면 해당 공간을 프로젝트 루트 `./`에 연결합니다. `.gitbook.yaml`의 `root`가 실제 문서 폴더를 지정합니다. 공간 단위 Git Sync 화면에서는 루트의 `.gitbook.yaml`을 사용합니다.
7. **Sync**를 실행합니다. 이미 내용이 있는 공간에서는 초기 동기화가 그 내용을 바꿀 수 있으므로 이 매뉴얼용 빈 공간을 사용합니다.

## 3. 게시 전 화면 확인

- 표지와 16개 섹션이 목차에 나타나는지 확인합니다.
- 로고와 경기장 그림 등 이미지가 표시되는지 확인합니다.
- Section 6의 Award 표, Section 10의 점수 표를 확인합니다.
- Section 13의 경기 일정 표에서 휴식 시간과 Award 문구가 같은 셀에 있는지 확인합니다.
- 셀 병합, 여러 줄 머리글, 규칙 번호, 캡션, 설명 상자가 잘 보이는지 확인합니다.
- 확인 후 GitBook의 게시 기능으로 공개합니다. 아직 이 묶음은 실제 GitBook에 게시하거나 렌더링 검증한 상태가 아닙니다.

## 변환 내용

- 본문, 영어·한국어 표현, 규칙 번호, 숫자, 캡션을 그대로 유지했습니다.
- 39개 표를 HTML 표 형식으로 보존하여 일반 Markdown 표 변환으로 인한 셀 병합 손실을 피했습니다.
- 원본의 2×2 머리글 두 곳은 GitBook의 직사각형 병합 제한에 맞춰 가로 병합된 두 행으로 나누었습니다. 원래 문구는 첫 행에 두고 둘째 행은 비웠습니다. 다른 가로·세로 병합은 유지했습니다.
- 원본 이미지 URL의 파일과 HTML에 들어 있던 두 로고를 이미지 파일로 보관했습니다.
- 검색창, 웹페이지 전용 버튼, 인쇄 스크립트와 CSS는 문서 본문에서 제외했습니다. GitBook에서 해당 기능과 디자인을 제공합니다.
- 원본 HTML은 `original/`에 보존했습니다. `tools/convert.py`는 재변환 도구이며 `conversion-report.json`은 이미지 출처·해시 및 변환 집계입니다.
- 원본의 비공식 번역 안내를 보존하고 상단의 Official Manual 링크를 표지로 옮겼습니다. 원본의 이 링크는 영문 V1 HTML을 가리키며, 안내 문구에서 말하는 최신 PDF 링크와는 다릅니다.

## 공식 참고 문서

- [GitBook GitHub Sync](https://gitbook.com/docs/docs-as-code/git-sync/enabling-github-sync)
- [문서 경로와 목차 설정](https://gitbook.com/docs/docs-as-code/git-sync/content-configuration)
- [표와 셀 병합 지원](https://gitbook.com/docs/create-content/blocks/table)

문서 생성 기준일: 2026-09-13. GitBook의 계정과 화면 버전에 따라 메뉴 배치가 다를 수 있습니다.
