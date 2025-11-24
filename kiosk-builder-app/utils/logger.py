import logging
import logging.handlers
import os

LOG_DIR = "logs"
LOG_FILENAME = os.path.join(LOG_DIR, "kiosk_builder.log")

def setup_logging():
    """
    로깅 시스템을 설정합니다.
    로그는 콘솔과 파일에 모두 출력됩니다.
    """
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    # 로거 인스턴스 생성
    logger = logging.getLogger()
    logger.setLevel(logging.INFO) # 기본 로그 레벨 설정

    # 로그 포맷 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 콘솔 핸들러 설정 (스트림 핸들러)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 파일 핸들러 설정 (RotatingFileHandler)
    # 로그 파일이 5MB를 초과하면 새 파일을 만들고, 최대 5개의 백업 파일을 유지합니다.
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILENAME, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)

    # 로거에 핸들러 추가
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler) 