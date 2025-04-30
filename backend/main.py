from fastapi import FastAPI, WebSocket, File, UploadFile, HTTPException, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, List, Optional
import uuid
import os
import shutil
import json
from pathlib import Path
import datetime
from pathlib import Path
from PIL import Image,ExifTags


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
            websocket, _ = self.mobile_connections[client_id]
            await websocket.send_json(message)

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


import asyncio

@app.websocket("/ws/kiosk/{event_id}")
async def websocket_kiosk_endpoint(websocket: WebSocket, event_id: str):
    await manager.connect_kiosk(websocket, event_id)

    # 🟡 Ping 루프: 30초마다 ping 메시지 보내기
    async def ping_loop():
        while True:
            try:
                await websocket.send_json({"type": "ping"})
                await asyncio.sleep(5)
            except Exception as e:
                print(f"[PING ERROR] {e}")
                break

    # Ping 루프 시작
    asyncio.create_task(ping_loop())

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
    except WebSocketDisconnect:
        await manager.disconnect_kiosk(event_id)

# 웹소켓 엔드포인트 - 모바일용
@app.websocket("/ws/mobile/{client_id}/{event_id}")
async def websocket_mobile_endpoint(websocket: WebSocket, client_id: str, event_id: str):
    await manager.connect_mobile(websocket, client_id, event_id)
    try:
        while True:
            data = await websocket.receive_json()
            # 모바일에서 이미지 선택 메시지 처리
            if data["type"] == "image_selected":
                await manager.send_to_kiosk(event_id, {
                    "type": "image_selected",
                    "client_id": client_id,
                    "image_id": data.get("image_id", "")
                })
            # 모바일에서 업로드 완료 메시지 처리
            elif data["type"] == "upload_confirmed":
                await manager.send_to_kiosk(event_id, {
                    "type": "upload_confirmed",
                    "client_id": client_id,
                    "image_id": data.get("image_id", "")
                })
    except WebSocketDisconnect:
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
                
                let socket;
                let selectedImageId;
                
                // 웹소켓 연결
                function connectWebSocket() {{
                    // 서버 도메인 기반으로 웹소켓 연결
                    const wsUrl = `${{wsProtocol}}://${{wsDomain}}/ws/mobile/${{clientId}}/${{eventId}}`;
                    socket = new WebSocket(wsUrl);
                    console.log(`연결 중: ${{wsUrl}}`);
                    
                    socket.onopen = function(e) {{
                        document.getElementById('connectionStatus').textContent = '연결됨';
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
                        }}
                    }};
                    
                    socket.onclose = function(event) {{
                        document.getElementById('connectionStatus').textContent = '연결 끊김. 재연결 중...';
                        setTimeout(connectWebSocket, 2000);
                    }};
                    
                    socket.onerror = function(error) {{
                        console.error('WebSocket 오류:', error);
                        document.getElementById('connectionStatus').textContent = '연결 오류';
                    }};
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
                            const file = e.target.files[0];
                            const reader = new FileReader();
                            
                            reader.onload = function(e) {{
                                document.getElementById('previewImage').src = e.target.result;
                                document.getElementById('step1').classList.add('hidden');
                                document.getElementById('step2').classList.remove('hidden');
                                
                                // 이미지 선택 알림
                                selectedImageId = new Date().getTime().toString();
                                socket.send(JSON.stringify({{
                                    type: 'image_selected',
                                    image_id: selectedImageId
                                }}));
                            }};
                            
                            reader.readAsDataURL(file);
                        }}
                    }});
                    
                    // 업로드 버튼 처리
                    document.getElementById('uploadButton').addEventListener('click', function() {{
                        const fileInput = document.getElementById('fileInput');
                        if (fileInput.files && fileInput.files[0]) {{
                            const formData = new FormData();
                            formData.append('file', fileInput.files[0]);
                            
                            // 서버 도메인 포함한 전체 URL 사용
                            fetch(`${{serverDomain}}/api/images/upload/${{eventId}}/${{clientId}}`, {{
                                method: 'POST',
                                body: formData
                            }})
                            .then(response => response.json())
                            .then(data => {{
                                console.log('Upload success:', data);
                                
                                // 업로드 확인 알림
                                socket.send(JSON.stringify({{
                                    type: 'upload_confirmed',
                                    image_id: selectedImageId
                                }}));
                            }})
                            .catch(error => {{
                                console.error('Upload error:', error);
                                alert('업로드 중 오류가 발생했습니다.');
                            }});
                        }}
                    }});
                    
                    // 취소 버튼 처리
                    document.getElementById('cancelButton').addEventListener('click', function() {{
                        document.getElementById('step2').classList.add('hidden');
                        document.getElementById('step1').classList.remove('hidden');
                        document.getElementById('fileInput').value = '';
                    }});
                    
                    // 새 업로드 버튼 처리
                    document.getElementById('newUploadButton').addEventListener('click', function() {{
                        document.getElementById('step3').classList.add('hidden');
                        document.getElementById('step1').classList.remove('hidden');
                        document.getElementById('fileInput').value = '';
                    }});
                }});
            </script>
        </body>
    </html>
    """
# @app.delete("/api/events/{event_id}")
# async def delete_event(event_id: str):
#     event_dir = UPLOAD_DIR / event_id
#     if event_dir.exists():
#         shutil.rmtree(event_dir)  # 폴더 통째로 삭제
#         print(f"Deleted event folder: {event_dir}")
#         return {"success": True, "message": "Event data deleted."}
#     raise HTTPException(status_code=404, detail="Event not found")
