from fastapi import FastAPI, WebSocket, File, UploadFile, HTTPException, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, List, Optional
import uuid
import os
import shutil
import json
import datetime
from pathlib import Path
from PIL import Image,ExifTags
import asyncio
from pydantic import BaseModel
import pymysql
import traceback

def apply_exif_orientation(image: Image.Image) -> Image.Image:
    try:
        exif = image._getexif()
        if exif is not None:
            for tag, value in exif.items():
                tag_name = ExifTags.TAGS.get(tag, None)
                if tag_name == "Orientation":
                    if value == 3:
                        image = image.rotate(180, expand=True)
                    elif value == 6:
                        image = image.rotate(270, expand=True)
                    elif value == 8:
                        image = image.rotate(90, expand=True)
                    break
    except Exception as e:
        print(f"EXIF 회전 정보 처리 중 오류: {e}")
    return image


# uploads 폴더가 없으면 자동으로 생성
Path("uploads").mkdir(exist_ok=True)

# 앱 생성
app = FastAPI(title="QR Code Image Server")
from pillow_heif import register_heif_opener
register_heif_opener()

# 이미지 접근을 위한 StaticFiles 마운트
from fastapi.staticfiles import StaticFiles
app.mount("/images", StaticFiles(directory="uploads"), name="images")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 특정 도메인만 허용하도록 변경
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 이미지 저장 경로 설정
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# 웹소켓 연결 관리
class ConnectionManager:
    def __init__(self):
        # 키오스크 연결 (event_id: WebSocket)
        self.kiosk_connections: Dict[str, WebSocket] = {}
        # 모바일 연결 (client_id: (WebSocket, event_id))
        self.mobile_connections: Dict[str, tuple[WebSocket, str]] = {}
    
    async def connect_kiosk(self, websocket: WebSocket, event_id: str):
        await websocket.accept()
        self.kiosk_connections[event_id] = websocket
        print(f"Kiosk connected for event: {event_id}")
    
    async def connect_mobile(self, websocket: WebSocket, client_id: str, event_id: str):
        await websocket.accept()
    
        # 동일 client_id 연결이 있다면 먼저 끊기
        if client_id in self.mobile_connections:
            old_websocket, _ = self.mobile_connections[client_id]
            try:
                await old_websocket.close(code=1000)
                print(f"[INFO] 기존 모바일 클라이언트 {client_id} 연결 종료")
            except Exception as e:
                print(f"[WARN] 이전 연결 종료 실패: {e}")
        
        # (선택적) 동일 event_id의 다른 client_id도 모두 끊기
        to_remove = [cid for cid, (_, eid) in self.mobile_connections.items() if eid == event_id and cid != client_id]
        for cid in to_remove:
            await self.disconnect_mobile(cid)
    
        # 새 연결 등록
        self.mobile_connections[client_id] = (websocket, event_id)
        print(f"Mobile client {client_id} connected for event: {event_id}")
    
        if event_id in self.kiosk_connections:
            await self.kiosk_connections[event_id].send_json({
                "type": "client_connected",
                "client_id": client_id
            })

    
    async def disconnect_kiosk(self, event_id: str):
        if event_id in self.kiosk_connections:
            del self.kiosk_connections[event_id]
            print(f"Kiosk disconnected for event: {event_id}")
    
    async def disconnect_mobile(self, client_id: str):
        if client_id in self.mobile_connections:
            websocket, event_id = self.mobile_connections[client_id]
            del self.mobile_connections[client_id]
            print(f"Mobile client {client_id} disconnected")
            
            # 연결된 키오스크에 모바일 연결 해제 알림
            if event_id in self.kiosk_connections:
                await self.kiosk_connections[event_id].send_json({
                    "type": "client_disconnected",
                    "client_id": client_id
                })
    
    async def send_to_kiosk(self, event_id: str, message: dict):
        if event_id in self.kiosk_connections:
            try:
                await self.kiosk_connections[event_id].send_json(message)
            except Exception as e:
                print(f"[ERROR] WebSocket 전송 실패 (kiosk): {e}")
                await self.disconnect_kiosk(event_id)

    async def send_to_mobile(self, client_id: str, message: dict):
        if client_id in self.mobile_connections:
            try:
                websocket, _ = self.mobile_connections[client_id]
                await websocket.send_json(message)
            except Exception as e:
                print(f"[ERROR] WebSocket 전송 실패 (mobile, {client_id}): {e}")
                await self.disconnect_mobile(client_id)

# 연결 관리자 인스턴스 생성
manager = ConnectionManager()

# 이벤트 폴더 생성 및 관리
def create_event_directory(event_id: str) -> Path:
    event_dir = UPLOAD_DIR / event_id
    event_dir.mkdir(exist_ok=True)
    return event_dir

# 행사 등록 및 QR URL 생성 API - 수정된 부분
@app.post("/api/events/register")
async def register_event(event_name: str):
    event_id = str(uuid.uuid4())
    event_dir = create_event_directory(event_id)
    
    # 이벤트 정보 저장 - Path.ctime 대신 현재 시간 사용
    with open(event_dir / "info.json", "w") as f:
        json.dump({
            "event_id": event_id,
            "event_name": event_name,
            "created_at": str(datetime.datetime.now())
        }, f)
    
    # QR 코드용 URL 생성
    qr_url = f"/event/{event_id}"
    from config import settings
    absolute_url = f"{settings.DOMAIN}{qr_url}"
    
    return {
        "event_id": event_id,
        "event_name": event_name,
        "qr_url": absolute_url
    }


@app.websocket("/ws/kiosk/{event_id}")
async def websocket_kiosk_endpoint(websocket: WebSocket, event_id: str):
    await manager.connect_kiosk(websocket, event_id)

    # Ping 루프: 30초마다 ping 메시지 보내기
    async def ping_loop():
        while True:
            try:
                await websocket.send_json({"type": "ping"})
                await asyncio.sleep(5)
            except Exception as e:
                print(f"[PING ERROR] {e}")
                break

    # Ping 루프 시작
    ping_task = asyncio.create_task(ping_loop())

    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=600)
                json_data = json.loads(data)
                if json_data["type"] == "send_to_mobile" and "client_id" in json_data:
                    await manager.send_to_mobile(json_data["client_id"], {
                        "type": "message_from_kiosk",
                        "content": json_data.get("content", "")
                    })
            except asyncio.TimeoutError:
                print(f"[INFO] 키오스크({event_id})에서 메시지 없음 (유지 중)")
                continue
            except Exception as e:
                print(f"[ERROR] 키오스크({event_id}) 메시지 처리 오류: {e}")
                break
    except WebSocketDisconnect:
        print(f"[INFO] 키오스크({event_id}) WebSocketDisconnect 발생")
    except Exception as e:
        print(f"[ERROR] 키오스크({event_id}) 웹소켓 오류: {e}")
    finally:
        ping_task.cancel()
        await manager.disconnect_kiosk(event_id)

# 웹소켓 엔드포인트 - 모바일용 (개선됨)
@app.websocket("/ws/mobile/{client_id}/{event_id}")
async def websocket_mobile_endpoint(websocket: WebSocket, client_id: str, event_id: str):
    await manager.connect_mobile(websocket, client_id, event_id)
    
    # Ping 루프: 30초마다 ping 메시지 보내기
    async def ping_loop():
        while True:
            try:
                await websocket.send_json({"type": "ping"})
                await asyncio.sleep(30)  # 30초마다 ping
            except Exception as e:
                print(f"[PING ERROR] Mobile({client_id}): {e}")
                break
    
    # Ping 루프 시작
    ping_task = asyncio.create_task(ping_loop())
    
    try:
        while True:
            try:
                # 타임아웃 설정 (10분)
                data = await asyncio.wait_for(websocket.receive_json(), timeout=600)
                
                # 기존 메시지 처리 로직
                if data["type"] == "image_selected":
                    await manager.send_to_kiosk(event_id, {
                        "type": "image_selected",
                        "client_id": client_id,
                        "image_id": data.get("image_id", "")
                    })
                elif data["type"] == "upload_confirmed":
                    await manager.send_to_kiosk(event_id, {
                        "type": "upload_confirmed",
                        "client_id": client_id,
                        "image_id": data.get("image_id", "")
                    })
                # 새로운 메시지 타입 처리
                elif data["type"] == "reconnected":
                    print(f"[INFO] 클라이언트 {client_id} 재연결 (상태: {data.get('upload_status', 'unknown')})")
                    # 키오스크에 모바일 재연결 알림
                    await manager.send_to_kiosk(event_id, {
                        "type": "client_reconnected", 
                        "client_id": client_id,
                        "image_id": data.get("image_id", ""),
                        "upload_status": data.get("upload_status", "unknown")
                    })
                elif data["type"] == "pong":
                    # 클라이언트 pong 응답은 로깅만
                    print(f"[DEBUG] 클라이언트 {client_id} pong 응답")
                    pass
                
            except asyncio.TimeoutError:
                print(f"[INFO] 모바일({client_id})에서 메시지 없음 (유지 중)")
                continue
            except Exception as e:
                print(f"[ERROR] 모바일({client_id}) 메시지 처리 오류: {e}")
                # 예외 발생 시 연결 종료
                break
                
    except WebSocketDisconnect:
        print(f"[INFO] 모바일({client_id}) WebSocketDisconnect 발생")
    except Exception as e:
        print(f"[ERROR] 모바일({client_id}) 웹소켓 오류: {e}")
    finally:
        # 최종 정리
        ping_task.cancel()
        await manager.disconnect_mobile(client_id)

@app.post("/api/images/upload/{event_id}/{client_id}")
async def upload_image(event_id: str, client_id: str, file: UploadFile = File(...)):
    try:
        event_dir = UPLOAD_DIR / event_id
        if not event_dir.exists():
            event_dir.mkdir(parents=True)

        filename = f"{uuid.uuid4()}.jpg"
        file_path = event_dir / filename

        # 이미지 열기 시도
        try:
            image = Image.open(file.file)
            image = apply_exif_orientation(image).convert("RGB")
        except Exception as e:
            print(f"[ERROR] 이미지 열기 실패: {e}")
            raise HTTPException(status_code=400, detail="이미지 처리 실패 (지원되지 않는 형식)")

        # 저장 시도
        try:
            image.save(file_path, format="JPEG", quality=95)
        except Exception as e:
            print(f"[ERROR] 이미지 저장 실패: {e}")
            raise HTTPException(status_code=500, detail="이미지 저장 실패")

        # WebSocket 알림 (개별 try로 감싸기)
        try:
            await manager.send_to_kiosk(event_id, {
                "type": "image_uploaded",
                "client_id": client_id,
                "image_url": f"/images/{event_id}/{filename}"
            })
        except Exception as e:
            print(f"[ERROR] WebSocket to kiosk failed: {e}")

        try:
            await manager.send_to_mobile(client_id, {
                "type": "upload_success",
                "image_url": f"/images/{event_id}/{filename}"
            })
        except Exception as e:
            print(f"[ERROR] WebSocket to mobile failed: {e}")

        return {
            "success": True,
            "filename": filename,
            "image_url": f"/images/{event_id}/{filename}"
        }

    except HTTPException as e:
        raise e  # FastAPI에 전달
    except Exception as e:
        print(f"[FATAL] 예상치 못한 오류: {e}")
        raise HTTPException(status_code=500, detail="서버 내부 오류 발생")


# 이벤트 페이지 - 모바일 사용자가 QR 코드 스캔 후 접속하는 페이지
@app.get("/event/{event_id}", response_class=HTMLResponse)
async def get_event_page(event_id: str):
    # 이벤트 폴더 확인
    event_dir = UPLOAD_DIR / event_id
    
    # 이벤트가 없으면 자동으로 생성
    if not event_dir.exists():
        print(f"이벤트 {event_id}가 없어 자동으로 생성합니다")
        event_dir.mkdir(parents=True, exist_ok=True)
        
        # 기본 정보 파일 생성
        with open(event_dir / "info.json", "w") as f:
            json.dump({
                "event_id": event_id,
                "event_name": "Auto Generated Event",
                "created_at": str(datetime.datetime.now())
            }, f)
    
    # 서버 도메인 가져오기
    from config import settings
    server_domain = settings.DOMAIN
    
    # 웹소켓 프로토콜 설정
    ws_protocol = "wss" if server_domain.startswith("https") else "ws"
    ws_domain = server_domain.replace("https://", "").replace("http://", "")
    
    # 클라이언트 ID 생성
    client_id = str(uuid.uuid4())
    
    return f"""
    <!DOCTYPE html>
    <html>
        <head>
            <title>QR Code Image Upload</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <!-- 변수를 메타 태그로 저장 -->
            <meta id="event-id" content="{event_id}">
            <meta id="client-id" content="{client_id}">
            <meta id="server-domain" content="{server_domain}">
            <meta id="ws-protocol" content="{ws_protocol}">
            <meta id="ws-domain" content="{ws_domain}">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    max-width: 500px;
                    margin: 0 auto;
                }}
                h1 {{
                    font-size: 24px;
                    text-align: center;
                }}
                .upload-area {{
                    border: 2px dashed #ccc;
                    padding: 20px;
                    text-align: center;
                    margin: 20px 0;
                    cursor: pointer;
                }}
                .preview-area {{
                    max-width: 100%;
                    margin: 20px 0;
                    text-align: center;
                }}
                .preview-area img {{
                    max-width: 100%;
                    max-height: 300px;
                }}
                .button {{
                    background-color: #4CAF50;
                    border: none;
                    color: white;
                    padding: 10px 20px;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    font-size: 16px;
                    margin: 4px 2px;
                    cursor: pointer;
                    border-radius: 4px;
                    width: 100%;
                }}
                .hidden {{
                    display: none;
                }}
                .status {{
                    text-align: center;
                    color: #666;
                    margin-top: 10px;
                }}
            </style>
        </head>
        <body>
            <h1>이미지 공유하기</h1>
            
            <div id="step1">
                <div class="upload-area" id="uploadArea">
                    사진을 선택하려면 클릭하세요
                </div>
                <input type="file" id="fileInput" class="hidden" accept="image/*">
                <div class="status" id="connectionStatus">연결 중...</div>
            </div>
            
            <div id="step2" class="hidden">
                <div class="preview-area">
                    <img id="previewImage" src="">
                </div>
                <button class="button" id="uploadButton">이 사진 업로드하기</button>
                <button class="button" id="cancelButton" style="background-color: #f44336;">취소</button>
            </div>
            
            <div id="step3" class="hidden">
                <div class="preview-area">
                    <img id="finalImage" src="">
                </div>
                <div class="status">업로드 완료!</div>
                <button class="button" id="newUploadButton">새 사진 업로드</button>
            </div>
            
            <script>
                // 메타 태그에서 변수 가져오기
                const eventId = document.getElementById('event-id').getAttribute('content');
                const clientId = document.getElementById('client-id').getAttribute('content');
                const serverDomain = document.getElementById('server-domain').getAttribute('content');
                const wsProtocol = document.getElementById('ws-protocol').getAttribute('content');
                const wsDomain = document.getElementById('ws-domain').getAttribute('content');
                
                // 전역 변수 추가
                let socket;
                let selectedImageId;
                let selectedFile = null;
                let isUploading = false;
                let reconnectAttempts = 0;
                let maxReconnectAttempts = 10;
                let reconnectDelay = 2000;
                let uploadAttempted = false;
                let lastUploadStatus = null;
                
                // 웹소켓 연결 함수 개선
                function connectWebSocket() {{
                    // 서버 도메인 기반으로 웹소켓 연결
                    const wsUrl = `${{wsProtocol}}://${{wsDomain}}/ws/mobile/${{clientId}}/${{eventId}}`;
                    socket = new WebSocket(wsUrl);
                    console.log(`연결 중: ${{wsUrl}}`);
                    
                    document.getElementById('connectionStatus').textContent = '연결 중...';
                    
                    socket.onopen = function(e) {{
                        document.getElementById('connectionStatus').textContent = '연결됨';
                        reconnectAttempts = 0; // 연결 성공 시 재시도 카운터 초기화
                        
                        // 연결 복구 시 마지막 상태 복원
                        if (selectedImageId && uploadAttempted) {{
                            // 재연결 시 서버에 현재 상태 알림
                            socket.send(JSON.stringify({{
                                type: 'reconnected',
                                image_id: selectedImageId,
                                upload_status: lastUploadStatus
                            }}));
                            
                            // 업로드 중이었다면 업로드 재시도
                            if (isUploading && selectedFile) {{
                                uploadImage(selectedFile);
                            }}
                        }}
                    }};
                    
                    socket.onmessage = function(event) {{
                        const data = JSON.parse(event.data);
                        console.log('메시지 수신:', data);
                        
                        if (data.type === 'upload_success') {{
                            // 업로드 성공 시 최종 이미지 표시
                            const imageUrl = data.image_url.startsWith('/') ? `${{serverDomain}}${{data.image_url}}` : data.image_url;
                            document.getElementById('finalImage').src = imageUrl;
                            document.getElementById('step2').classList.add('hidden');
                            document.getElementById('step3').classList.remove('hidden');
                            isUploading = false;
                            lastUploadStatus = 'completed';
                        }} else if (data.type === 'ping') {{
                            // 서버의 ping에 응답
                            socket.send(JSON.stringify({{
                                type: 'pong'
                            }}));
                        }}
                    }};
                    
                    socket.onclose = function(event) {{
                        console.log('WebSocket 연결 종료:', event);
                        
                        if (reconnectAttempts < maxReconnectAttempts) {{
                            reconnectAttempts++;
                            const waitTime = reconnectDelay * Math.min(reconnectAttempts, 5); // 지수 백오프
                            document.getElementById('connectionStatus').textContent = `연결 끊김. ${{waitTime/1000}}초 후 재연결 시도 (${{reconnectAttempts}}/${{maxReconnectAttempts}})`;
                            setTimeout(connectWebSocket, waitTime);
                        }} else {{
                            document.getElementById('connectionStatus').textContent = '재연결 실패. 페이지를 새로고침해 주세요.';
                        }}
                    }};
                    
                    socket.onerror = function(error) {{
                        console.error('WebSocket 오류:', error);
                        document.getElementById('connectionStatus').textContent = '연결 오류';
                    }};
                }}
                
                // 이미지 업로드 함수 (분리하여 재사용 가능하게)
                function uploadImage(file) {{
                    if (!file) return;
                    
                    isUploading = true;
                    document.getElementById('uploadButton').disabled = true;
                    document.getElementById('uploadButton').textContent = '업로드 중...';
                    
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    // 업로드 상태 표시 추가
                    document.getElementById('connectionStatus').textContent = '이미지 업로드 중...';
                    uploadAttempted = true;
                    lastUploadStatus = 'uploading';
                    
                    // 서버 도메인 포함한 전체 URL 사용
                    fetch(`${{serverDomain}}/api/images/upload/${{eventId}}/${{clientId}}`, {{
                        method: 'POST',
                        body: formData,
                        // 타임아웃 설정 (브라우저 fetch API는 기본 타임아웃이 없으므로 AbortController로 구현 필요)
                    }})
                    .then(response => {{
                        if (!response.ok) {{
                            throw new Error(`HTTP error! Status: ${{response.status}}`);
                        }}
                        return response.json();
                    }})
                    .then(data => {{
                        console.log('Upload success:', data);
                        document.getElementById('connectionStatus').textContent = '업로드 완료, 처리 중...';
                        lastUploadStatus = 'uploaded';
                        
                        // 업로드 확인 알림
                        if (socket && socket.readyState === WebSocket.OPEN) {{
                            socket.send(JSON.stringify({{
                                type: 'upload_confirmed',
                                image_id: selectedImageId
                            }}));
                        }} else {{
                            console.warn('WebSocket 연결이 없어 확인 메시지를 보낼 수 없습니다.');
                            document.getElementById('connectionStatus').textContent = '연결 복구 중... 업로드는 완료되었습니다.';
                        }}
                    }})
                    .catch(error => {{
                        console.error('Upload error:', error);
                        document.getElementById('connectionStatus').textContent = '업로드 실패. 다시 시도해 주세요.';
                        document.getElementById('uploadButton').disabled = false;
                        document.getElementById('uploadButton').textContent = '다시 시도';
                        isUploading = false;
                        lastUploadStatus = 'failed';
                    }});
                }}
                
                // 초기화
                window.addEventListener('load', function() {{
                    console.log("페이지 로드됨. 이벤트 ID:", eventId);
                    console.log("클라이언트 ID:", clientId);
                    console.log("서버 도메인:", serverDomain);
                    
                    connectWebSocket();
                    
                    // 업로드 영역 클릭 처리
                    document.getElementById('uploadArea').addEventListener('click', function() {{
                        document.getElementById('fileInput').click();
                    }});
                    
                    // 파일 선택 처리
                    document.getElementById('fileInput').addEventListener('change', function(e) {{
                        if (e.target.files && e.target.files[0]) {{
                            selectedFile = e.target.files[0];
                            const reader = new FileReader();
                            
                            reader.onload = function(e) {{
                                document.getElementById('previewImage').src = e.target.result;
                                document.getElementById('step1').classList.add('hidden');
                                document.getElementById('step2').classList.remove('hidden');
                                
                                // 이미지 선택 알림
                                selectedImageId = new Date().getTime().toString();
                                
                                // 웹소켓이 열려 있는 경우에만 메시지 전송
                                if (socket && socket.readyState === WebSocket.OPEN) {{
                                    socket.send(JSON.stringify({{
                                        type: 'image_selected',
                                        image_id: selectedImageId
                                    }}));
                                }} else {{
                                    console.warn('웹소켓 연결이 없어 이미지 선택 메시지를 보낼 수 없습니다.');
                                    document.getElementById('connectionStatus').textContent = '연결 복구 중... 이미지는 선택되었습니다.';
                                }}
                            }};
                            
                            reader.readAsDataURL(selectedFile);
                        }}
                    }});
                    
                    // 업로드 버튼 처리
                    document.getElementById('uploadButton').addEventListener('click', function() {{
                        uploadImage(selectedFile);
                    }});
                    
                    // 취소 버튼 처리
                    document.getElementById('cancelButton').addEventListener('click', function() {{
                        document.getElementById('step2').classList.add('hidden');
                        document.getElementById('step1').classList.remove('hidden');
                        document.getElementById('fileInput').value = '';
                        selectedFile = null;
                        uploadAttempted = false;
                    }});
                    
                    // 새 업로드 버튼 처리
                    document.getElementById('newUploadButton').addEventListener('click', function() {{
                        document.getElementById('step3').classList.add('hidden');
                        document.getElementById('step1').classList.remove('hidden');
                        document.getElementById('fileInput').value = '';
                        selectedFile = null;
                        uploadAttempted = false;
                    }});
                }});
            </script>
        </body>
    </html>
    """



# 요청 모델 정의
class LoginRequest(BaseModel):
    login_id: str
    password: str

# 로그 요청 모델 정의
class LogRequest(BaseModel):
    user_id: int
    app_name: str = None
    action: str = "button_click"

from fastapi import HTTPException
import traceback

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    try:
        conn = pymysql.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            db=os.getenv("DB_NAME"),
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )

        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE login_id = %s AND is_active = 1", (request.login_id,))
            user = cursor.fetchone()
        
            if not user:
                raise HTTPException(status_code=401, detail="존재하지 않는 사용자입니다.")
            
            # 날짜 타입 체크 및 변환
            if user["usage_period"]:
                if isinstance(user["usage_period"], str):
                    user["usage_period"] = datetime.datetime.strptime(user["usage_period"], "%Y-%m-%d").date()
                elif isinstance(user["usage_period"], datetime.datetime):
                    user["usage_period"] = user["usage_period"].date()

                if user["usage_period"] < datetime.date.today():
                    raise HTTPException(status_code=403, detail="계정 사용 기간이 만료되었습니다.")
            
            if request.password != user["password"]:
                raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않습니다.")
            
            return {
                "success": True,
                "user_id": user["user_id"],
                "username": user["username"],
                "role": user["role"]
            }

    except HTTPException as e:
        raise e  # FastAPI가 처리할 수 있게 그대로 전달
    except Exception as e:
        print(f"[LOGIN ERROR] {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="서버 내부 오류")

# 로그 기록 API 엔드포인트
@app.post("/api/logs/create")
async def create_log(request: LogRequest):
    try:
        # 사용자 ID 검증
        if request.user_id <= 0:
            raise HTTPException(status_code=400, detail="유효하지 않은 사용자 ID")
        
        # 데이터베이스 연결
        conn = pymysql.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            db=os.getenv("DB_NAME"),
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )

        with conn.cursor() as cursor:
            # 현재 시간 가져오기
            now = datetime.datetime.now()
            
            # 로그 저장
            sql = """
            INSERT INTO sk_builder.usage_logs 
            (user_id, app_name, action, created_at) 
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (request.user_id, request.app_name, request.action, now))
            conn.commit()
            
            # 해당 유저와 앱 이름에 대한 사용 횟수 조회 (선택적)
            count_sql = """
            SELECT COUNT(*) as count 
            FROM sk_builder.usage_logs 
            WHERE user_id = %s AND app_name = %s AND action = %s
            """
            cursor.execute(count_sql, (request.user_id, request.app_name, request.action))
            count_result = cursor.fetchone()
            count = count_result["count"] if count_result else 0
            
        return {
            "success": True, 
            "message": "로그가 성공적으로 기록되었습니다.",
            "count": count
        }
        
    except HTTPException as e:
        raise e  # FastAPI가 처리할 수 있게 그대로 전달
    except Exception as e:
        print(f"[LOG ERROR] {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="서버 내부 오류")

# 사용 횟수 조회 API 엔드포인트 (선택적)
@app.get("/api/logs/count/{user_id}/{app_name}")
async def get_app_usage_count(user_id: int, app_name: str, action: str = "button_click"):
    try:
        # 데이터베이스 연결
        conn = pymysql.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            db=os.getenv("DB_NAME"),
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )

        with conn.cursor() as cursor:
            # 해당 유저와 앱 이름에 대한 사용 횟수 조회
            sql = """
            SELECT COUNT(*) as count 
            FROM sk_builder.usage_logs 
            WHERE user_id = %s AND app_name = %s AND action = %s
            """
            cursor.execute(sql, (user_id, app_name, action))
            result = cursor.fetchone()
            count = result["count"] if result else 0
            
        return {"user_id": user_id, "app_name": app_name, "action": action, "count": count}
        
    except Exception as e:
        print(f"[LOG COUNT ERROR] {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="서버 내부 오류")

# @app.delete("/api/events/{event_id}")
# async def delete_event(event_id: str):
#     event_dir = UPLOAD_DIR / event_id
#     if event_dir.exists():
#         shutil.rmtree(event_dir)  # 폴더 통째로 삭제
#         print(f"Deleted event folder: {event_dir}")
#         return {"success": True, "message": "Event data deleted."}
#     raise HTTPException(status_code=404, detail="Event not found")
