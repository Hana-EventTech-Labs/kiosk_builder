"""
Kiosk Builder - 빌드 및 GitHub Release 자동 배포 스크립트

사용법:
    python build.py                    # 빌드만 실행
    python build.py --release          # 빌드 + GitHub Release 배포
    python build.py --release --tag v1.0.1  # 특정 버전으로 배포
"""

import os
import subprocess
import shutil
import argparse
import re
from datetime import datetime


# ═══════════════════════════════════════════════════════════
# 설정
# ═══════════════════════════════════════════════════════════

GITHUB_REPO = "Hana-EventTech-Labs/kiosk_builder"

# 빌드 대상 정의
BUILD_TARGETS = {
    "super-kiosk": {
        "entry": "main.py",
        "output_name": "super-kiosk",
        "description": "키오스크 실행 프로그램",
        "add_data": [
            "resources;resources",
            "screens;screens",
            "components;components",
            "printer_utils;printer_utils",
            "webcam_utils;webcam_utils",
            "config.json;.",
        ]
    },
    "super-kiosk-builder": {
        "entry": "kiosk-builder-app/run_gui.py",
        "output_name": "super-kiosk-builder",
        "description": "키오스크 빌더 (설정 프로그램)",
        "add_data": [
            "kiosk-builder-app/resources;resources",
            "kiosk-builder-app/ui;ui",
            "kiosk-builder-app/config.json;.",
            "kiosk-builder-app/api_client.py;.",
        ]
    }
}


# ═══════════════════════════════════════════════════════════
# 빌드 함수
# ═══════════════════════════════════════════════════════════

def run_pyinstaller(target_name: str, target_config: dict) -> bool:
    """PyInstaller로 실행 파일 빌드"""
    print(f"\n{'='*60}")
    print(f"빌드 시작: {target_config['description']}")
    print(f"{'='*60}")

    command = [
        "pyinstaller",
        "--clean",
        "--onefile",
        "--windowed",
        "--name", target_config["output_name"],
    ]

    # add-data 옵션 추가
    for data in target_config["add_data"]:
        command.extend(["--add-data", data])

    command.append(target_config["entry"])

    print(f"실행 명령: {' '.join(command)}")

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ {target_name} 빌드 실패:")
        print(result.stderr)
        return False

    # 빌드된 파일 확인
    exe_path = os.path.join("dist", f"{target_config['output_name']}.exe")
    if os.path.exists(exe_path):
        file_size = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"✅ {target_name} 빌드 성공!")
        print(f"   파일: {exe_path}")
        print(f"   크기: {file_size:.2f} MB")
        return True
    else:
        print(f"❌ {target_name} 빌드 실패: 출력 파일을 찾을 수 없습니다.")
        return False


def build_all() -> dict:
    """모든 타겟 빌드"""
    results = {}

    for target_name, target_config in BUILD_TARGETS.items():
        # 엔트리 파일 존재 확인
        if not os.path.exists(target_config["entry"]):
            print(f"⚠️ {target_name}: 엔트리 파일을 찾을 수 없습니다 ({target_config['entry']})")
            results[target_name] = False
            continue

        success = run_pyinstaller(target_name, target_config)
        results[target_name] = success

    return results


# ═══════════════════════════════════════════════════════════
# GitHub Release 함수
# ═══════════════════════════════════════════════════════════

def check_gh_cli() -> bool:
    """GitHub CLI 설치 확인"""
    try:
        result = subprocess.run(["gh", "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def check_gh_auth() -> bool:
    """GitHub CLI 인증 상태 확인"""
    result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    return result.returncode == 0


def get_latest_release_tag() -> str:
    """최신 릴리즈 태그 가져오기"""
    result = subprocess.run(
        ["gh", "release", "list", "--repo", GITHUB_REPO, "--limit", "1"],
        capture_output=True, text=True
    )

    if result.returncode == 0 and result.stdout.strip():
        # 첫 번째 줄에서 태그 추출 (형식: "title\tstatus\ttag\tdate")
        first_line = result.stdout.strip().split('\n')[0]
        parts = first_line.split('\t')
        if len(parts) >= 3:
            return parts[2]  # 태그는 세 번째 컬럼

    return "v0.0.0"


def increment_version(version: str) -> str:
    """버전 증가 (v1.0.0 -> v1.0.1)"""
    match = re.match(r'v?(\d+)\.(\d+)\.(\d+)', version)
    if match:
        major, minor, patch = map(int, match.groups())
        return f"v{major}.{minor}.{patch + 1}"
    return "v1.0.0"


def create_release(tag: str, build_results: dict) -> bool:
    """GitHub Release 생성 및 파일 업로드"""
    print(f"\n{'='*60}")
    print(f"GitHub Release 생성: {tag}")
    print(f"{'='*60}")

    # 업로드할 파일 목록
    files_to_upload = []
    for target_name, success in build_results.items():
        if success:
            exe_name = f"{BUILD_TARGETS[target_name]['output_name']}.exe"
            exe_path = os.path.join("dist", exe_name)
            if os.path.exists(exe_path):
                files_to_upload.append(exe_path)

    if not files_to_upload:
        print("❌ 업로드할 파일이 없습니다.")
        return False

    print(f"업로드할 파일: {', '.join(files_to_upload)}")

    # 릴리즈 노트 생성
    release_notes = f"""## Kiosk Builder Release {tag}

### 빌드 정보
- 빌드 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 빌드 환경: Windows

### 포함된 파일
"""

    for target_name, success in build_results.items():
        if success:
            config = BUILD_TARGETS[target_name]
            exe_path = os.path.join("dist", f"{config['output_name']}.exe")
            if os.path.exists(exe_path):
                file_size = os.path.getsize(exe_path) / (1024 * 1024)
                release_notes += f"- **{config['output_name']}.exe** ({file_size:.2f} MB): {config['description']}\n"

    release_notes += """
### 사용 방법
1. `super-kiosk-builder.exe`를 실행하여 키오스크를 설정합니다.
2. "배포용 생성" 버튼을 클릭하면 자동으로 필요한 파일이 다운로드됩니다.
"""

    # 기존 릴리즈 삭제 (있는 경우)
    print(f"기존 릴리즈 확인 중...")
    delete_result = subprocess.run(
        ["gh", "release", "delete", tag, "--repo", GITHUB_REPO, "--yes"],
        capture_output=True, text=True
    )
    if delete_result.returncode == 0:
        print(f"기존 릴리즈 {tag} 삭제됨")

    # 기존 태그 삭제 (있는 경우)
    subprocess.run(
        ["git", "tag", "-d", tag],
        capture_output=True, text=True
    )
    subprocess.run(
        ["git", "push", "origin", f":refs/tags/{tag}"],
        capture_output=True, text=True
    )

    # 새 릴리즈 생성
    command = [
        "gh", "release", "create", tag,
        "--repo", GITHUB_REPO,
        "--title", f"Kiosk Builder {tag}",
        "--notes", release_notes,
    ]
    command.extend(files_to_upload)

    print(f"릴리즈 생성 중...")
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ GitHub Release {tag} 생성 완료!")
        print(f"   URL: https://github.com/{GITHUB_REPO}/releases/tag/{tag}")
        return True
    else:
        print(f"❌ GitHub Release 생성 실패:")
        print(result.stderr)
        return False


# ═══════════════════════════════════════════════════════════
# 메인 함수
# ═══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Kiosk Builder 빌드 및 배포 스크립트")
    parser.add_argument("--release", action="store_true", help="GitHub Release에 배포")
    parser.add_argument("--tag", type=str, help="릴리즈 태그 (예: v1.0.1)")
    parser.add_argument("--skip-build", action="store_true", help="빌드 건너뛰기 (기존 파일 사용)")
    args = parser.parse_args()

    print("\n" + "="*60)
    print("🔧 Kiosk Builder - 빌드 및 배포 스크립트")
    print("="*60)

    # 빌드 실행
    if args.skip_build:
        print("\n⏭️ 빌드 건너뛰기 (기존 파일 사용)")
        # 기존 파일 확인
        build_results = {}
        for target_name, target_config in BUILD_TARGETS.items():
            exe_path = os.path.join("dist", f"{target_config['output_name']}.exe")
            build_results[target_name] = os.path.exists(exe_path)
            if build_results[target_name]:
                print(f"  ✅ {target_config['output_name']}.exe 발견")
            else:
                print(f"  ❌ {target_config['output_name']}.exe 없음")
    else:
        build_results = build_all()

    # 빌드 결과 출력
    print("\n" + "="*60)
    print("📊 빌드 결과")
    print("="*60)

    for target_name, success in build_results.items():
        status = "✅ 성공" if success else "❌ 실패"
        print(f"  {BUILD_TARGETS[target_name]['description']}: {status}")

    # 릴리즈 배포
    if args.release:
        print("\n" + "="*60)
        print("🚀 GitHub Release 배포")
        print("="*60)

        # GitHub CLI 확인
        if not check_gh_cli():
            print("❌ GitHub CLI(gh)가 설치되어 있지 않습니다.")
            print("   설치: https://cli.github.com/")
            return

        if not check_gh_auth():
            print("❌ GitHub CLI 인증이 필요합니다.")
            print("   실행: gh auth login")
            return

        # 태그 결정
        if args.tag:
            tag = args.tag
        else:
            latest_tag = get_latest_release_tag()
            tag = increment_version(latest_tag)
            print(f"최신 태그: {latest_tag} → 새 태그: {tag}")

        # 릴리즈 생성
        if any(build_results.values()):
            create_release(tag, build_results)
        else:
            print("❌ 성공한 빌드가 없어 릴리즈를 생성할 수 없습니다.")

    print("\n" + "="*60)
    print("🏁 완료")
    print("="*60)


if __name__ == "__main__":
    main()
