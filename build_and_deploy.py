#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HanaKiosk & SuperKioskBuilder 빌드 및 GitHub Release 배포 도구
=============================================================
사용법: python build_and_deploy.py [옵션]

옵션:
  --kiosk       HanaKiosk만 빌드
  --builder     SuperKioskBuilder만 빌드
  --all         둘 다 빌드 (기본값)
  --deploy      빌드 후 GitHub Release에 업로드
  --version     버전 태그 지정 (예: --version v1.0.3)
"""

import os
import sys
import subprocess
import shutil
import argparse
from datetime import datetime

# ============================================================
# 경로 설정
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# HanaKiosk 프로젝트 (현재 kiosk_builder 폴더 사용)
HANAKIOSK_DIR = BASE_DIR
HANAKIOSK_SPEC = os.path.join(HANAKIOSK_DIR, "super-kiosk.spec")
HANAKIOSK_DIST = os.path.join(HANAKIOSK_DIR, "dist", "HanaKiosk.exe")

# SuperKioskBuilder 프로젝트
BUILDER_DIR = os.path.join(BASE_DIR, "kiosk-builder-app")
BUILDER_SPEC = os.path.join(BUILDER_DIR, "run_gui.spec")
BUILDER_DIST = os.path.join(BUILDER_DIR, "dist", "SuperKioskBuilder.exe")

# 릴리즈 출력 폴더
RELEASE_DIR = os.path.join(BASE_DIR, "release")

# GitHub 저장소
GITHUB_REPO = "Hana-EventTech-Labs/kiosk_builder"


def print_header(text):
    """헤더 출력"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_step(step, text):
    """단계 출력"""
    print(f"\n[{step}] {text}")
    print("-" * 40)


def run_command(cmd, cwd=None, shell=True):
    """명령어 실행"""
    print(f"  > {cmd}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            shell=shell,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"  [오류] {result.stderr}")
            return False
        if result.stdout:
            # 주요 출력만 표시
            lines = result.stdout.strip().split('\n')
            for line in lines[-5:]:  # 마지막 5줄만
                print(f"  {line}")
        return True
    except Exception as e:
        print(f"  [오류] {e}")
        return False


def check_prerequisites():
    """필수 도구 확인"""
    print_step("0", "필수 도구 확인")

    # Python 버전
    print(f"  Python: {sys.version.split()[0]}")

    # PyInstaller
    try:
        result = subprocess.run(
            ["pyinstaller", "--version"],
            capture_output=True,
            text=True
        )
        print(f"  PyInstaller: {result.stdout.strip()}")
    except:
        print("  [경고] PyInstaller가 설치되지 않았습니다.")
        print("  > pip install pyinstaller")
        return False

    # GitHub CLI (배포용)
    try:
        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            text=True
        )
        version = result.stdout.split('\n')[0]
        print(f"  GitHub CLI: {version}")
    except:
        print("  [경고] GitHub CLI가 설치되지 않았습니다. (배포 기능 사용 불가)")

    return True


def build_hanakiosk():
    """HanaKiosk 빌드"""
    print_step("1", "HanaKiosk 빌드")

    if not os.path.exists(HANAKIOSK_DIR):
        print(f"  [오류] HanaKiosk 디렉토리를 찾을 수 없습니다: {HANAKIOSK_DIR}")
        return None

    if not os.path.exists(HANAKIOSK_SPEC):
        print(f"  [오류] spec 파일을 찾을 수 없습니다: {HANAKIOSK_SPEC}")
        return None

    # 기존 빌드 정리
    dist_dir = os.path.join(HANAKIOSK_DIR, "dist")
    build_dir = os.path.join(HANAKIOSK_DIR, "build", "HanaKiosk")
    if os.path.exists(build_dir):
        print("  기존 빌드 파일 정리 중...")
        shutil.rmtree(build_dir, ignore_errors=True)

    # PyInstaller 빌드
    print("  빌드 시작...")
    cmd = f'pyinstaller "{HANAKIOSK_SPEC}" --noconfirm'
    if not run_command(cmd, cwd=HANAKIOSK_DIR):
        return None

    # 결과 확인
    if os.path.exists(HANAKIOSK_DIST):
        size_mb = os.path.getsize(HANAKIOSK_DIST) / (1024 * 1024)
        print(f"  ✓ 빌드 완료: HanaKiosk.exe ({size_mb:.1f} MB)")
        return HANAKIOSK_DIST
    else:
        print("  [오류] 빌드 파일이 생성되지 않았습니다.")
        return None


def build_builder():
    """SuperKioskBuilder 빌드"""
    print_step("2", "SuperKioskBuilder 빌드")

    if not os.path.exists(BUILDER_DIR):
        print(f"  [오류] Builder 디렉토리를 찾을 수 없습니다: {BUILDER_DIR}")
        return None

    if not os.path.exists(BUILDER_SPEC):
        print(f"  [오류] spec 파일을 찾을 수 없습니다: {BUILDER_SPEC}")
        return None

    # 기존 빌드 정리
    build_dir = os.path.join(BUILDER_DIR, "build", "run_gui")
    if os.path.exists(build_dir):
        print("  기존 빌드 파일 정리 중...")
        shutil.rmtree(build_dir, ignore_errors=True)

    # PyInstaller 빌드
    print("  빌드 시작...")
    cmd = f'pyinstaller "{BUILDER_SPEC}" --noconfirm'
    if not run_command(cmd, cwd=BUILDER_DIR):
        return None

    # 결과 확인
    if os.path.exists(BUILDER_DIST):
        size_mb = os.path.getsize(BUILDER_DIST) / (1024 * 1024)
        print(f"  ✓ 빌드 완료: SuperKioskBuilder.exe ({size_mb:.1f} MB)")
        return BUILDER_DIST
    else:
        print("  [오류] 빌드 파일이 생성되지 않았습니다.")
        return None


def collect_release_files(kiosk_exe, builder_exe):
    """릴리즈 파일 수집"""
    print_step("3", "릴리즈 파일 수집")

    # 릴리즈 폴더 생성
    os.makedirs(RELEASE_DIR, exist_ok=True)

    collected = []

    if kiosk_exe and os.path.exists(kiosk_exe):
        dest = os.path.join(RELEASE_DIR, "HanaKiosk.exe")
        shutil.copy2(kiosk_exe, dest)
        size_mb = os.path.getsize(dest) / (1024 * 1024)
        print(f"  ✓ HanaKiosk.exe ({size_mb:.1f} MB)")
        collected.append(dest)

    if builder_exe and os.path.exists(builder_exe):
        dest = os.path.join(RELEASE_DIR, "SuperKioskBuilder.exe")
        shutil.copy2(builder_exe, dest)
        size_mb = os.path.getsize(dest) / (1024 * 1024)
        print(f"  ✓ SuperKioskBuilder.exe ({size_mb:.1f} MB)")
        collected.append(dest)

    if collected:
        print(f"\n  릴리즈 폴더: {RELEASE_DIR}")

    return collected


def deploy_to_github(files, version):
    """GitHub Release에 업로드"""
    print_step("4", f"GitHub Release 배포 ({version})")

    if not files:
        print("  [오류] 업로드할 파일이 없습니다.")
        return False

    # GitHub CLI 확인
    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
    except:
        print("  [오류] GitHub CLI가 설치되지 않았습니다.")
        print("  > winget install GitHub.cli")
        print("  > gh auth login")
        return False

    # 릴리즈 노트 생성
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    notes = f"""## 릴리즈 {version}

빌드 시간: {now}

### 포함된 파일
"""
    for f in files:
        name = os.path.basename(f)
        size_mb = os.path.getsize(f) / (1024 * 1024)
        notes += f"- `{name}` ({size_mb:.1f} MB)\n"

    notes += """
### 변경사항
- 자동 빌드 및 배포

### 사용법
1. `HanaKiosk.exe` - 키오스크 실행 파일
2. `SuperKioskBuilder.exe` - 설정 프로그램
"""

    # 릴리즈 생성 및 업로드
    files_args = " ".join([f'"{f}"' for f in files])

    # 기존 릴리즈가 있는지 확인
    check_cmd = f'gh release view {version} --repo {GITHUB_REPO}'
    result = subprocess.run(check_cmd, shell=True, capture_output=True)

    if result.returncode == 0:
        # 기존 릴리즈에 파일 업로드 (덮어쓰기)
        print(f"  기존 릴리즈 {version}에 파일 업로드...")
        cmd = f'gh release upload {version} {files_args} --clobber --repo {GITHUB_REPO}'
    else:
        # 새 릴리즈 생성
        print(f"  새 릴리즈 {version} 생성...")
        notes_file = os.path.join(RELEASE_DIR, "release_notes.md")
        with open(notes_file, 'w', encoding='utf-8') as f:
            f.write(notes)

        cmd = f'gh release create {version} {files_args} --title "Release {version}" --notes-file "{notes_file}" --repo {GITHUB_REPO}'

    if run_command(cmd):
        print(f"\n  ✓ GitHub Release 배포 완료!")
        print(f"  https://github.com/{GITHUB_REPO}/releases/tag/{version}")
        return True
    else:
        print("  [오류] GitHub Release 배포 실패")
        return False


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="HanaKiosk & SuperKioskBuilder 빌드 및 배포 도구"
    )
    parser.add_argument('--kiosk', action='store_true', help='HanaKiosk만 빌드')
    parser.add_argument('--builder', action='store_true', help='SuperKioskBuilder만 빌드')
    parser.add_argument('--all', action='store_true', help='둘 다 빌드 (기본값)')
    parser.add_argument('--deploy', action='store_true', help='GitHub Release에 업로드')
    parser.add_argument('--version', type=str, default=None, help='버전 태그 (예: v1.0.3)')

    args = parser.parse_args()

    # 기본값: 둘 다 빌드
    if not args.kiosk and not args.builder:
        args.all = True

    build_kiosk = args.kiosk or args.all
    build_bldr = args.builder or args.all

    print_header("HanaKiosk & SuperKioskBuilder 빌드 도구")
    print(f"  작업 디렉토리: {BASE_DIR}")
    print(f"  빌드 대상: {'HanaKiosk ' if build_kiosk else ''}{'SuperKioskBuilder' if build_bldr else ''}")
    if args.deploy:
        print(f"  배포: GitHub Release ({args.version or '자동 생성'})")

    # 필수 도구 확인
    if not check_prerequisites():
        print("\n[중단] 필수 도구를 설치해주세요.")
        return 1

    # 빌드 실행
    kiosk_exe = None
    builder_exe = None

    if build_kiosk:
        kiosk_exe = build_hanakiosk()

    if build_bldr:
        builder_exe = build_builder()

    # 결과 수집
    files = collect_release_files(kiosk_exe, builder_exe)

    # GitHub 배포
    if args.deploy and files:
        version = args.version
        if not version:
            # 자동 버전 생성
            now = datetime.now()
            version = f"v{now.strftime('%Y.%m.%d')}"

        deploy_to_github(files, version)

    # 최종 결과
    print_header("빌드 완료")

    if kiosk_exe:
        print(f"  ✓ HanaKiosk.exe")
    elif build_kiosk:
        print(f"  ✗ HanaKiosk.exe (빌드 실패)")

    if builder_exe:
        print(f"  ✓ SuperKioskBuilder.exe")
    elif build_bldr:
        print(f"  ✗ SuperKioskBuilder.exe (빌드 실패)")

    print(f"\n  릴리즈 폴더: {RELEASE_DIR}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
