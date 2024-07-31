from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from starlette.templating import Jinja2Templates
from image import ImageSchema
from database import image_collection
from mouse_position import detect_mouse_position
from threading import Thread
import cv2
import mouse
import datetime
import time
import pyautogui

camera = cv2.VideoCapture(0)

templates = Jinja2Templates(directory="page")

app = FastAPI()

async def save_image(frame):
    x, y = pyautogui.position()
    now = datetime.datetime.now()
    img_name = 'opencv_frame_{}.png'.format(str(now).replace(':', ''))
    cv2.imwrite(img_name, frame)
    print('Screenshot taken')
    image_data = ImageSchema(img_source=img_name, position_x=x, position_y=y)
    await image_collection.insert_one(dict(image_data))
    print("Successfully added to the database")

async def gen_frames():
    count = 1
    thread = Thread(target=detect_mouse_position)
    thread.start()
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            if mouse.is_pressed('left') and count == 1:
                count = 0
                await save_image(frame)
                time.sleep(1)
                count = 1

            ret, buffer = cv2.imencode('.jpg', cv2.flip(frame,1))
            frame = buffer.tobytes()
            yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.get('/', response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get('/video_feed')
async def video_feed():
    return StreamingResponse(gen_frames(), media_type='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host='127.0.0.1', port=8000, reload=True)
