# 1. 加入 相關 模組
import cv2, time
import numpy as np
from djitellopy import Tello
import csv

# 2. 建立 Tello 物件與 Tello 初始化
tello = Tello()
# Tello 進入 SDK Mode
tello.connect()
Battery = "Battery: {}%".format(tello.get_battery())
print(Battery)

# 開啟 Tello 視訊
tello.streamoff()
tello.streamon()

# Tello 起飛
tello.takeoff()

# 送出飛行控制訊號：依據偵測人臉位置調整
# 例如: 若太低，調整 up值: (0, 0, 10, 0)
# tello.send_rc_control(0, 0, 0, 0)
# time.sleep(2.5)

# 3. 參數設定
w, h = 360, 240
faceAreaRange=[6250, 6850]
pid = [1.0, 0.5, 0]
# PID運算紀錄上一次誤差的變數
pError = 0
Error = 0

def findFace(img):
    # 將 img 轉為灰階圖片
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 建立 人臉識別分類器
    faceCascade = cv2.CascadeClassifier('haarcascade_frontalface_alt2.xml')
    # 偵測 img中的人臉
    faces = faceCascade.detectMultiScale(gray, 1.1, 5)
    # 紀錄 img 中人臉的中心點座標與人臉大小
    faceCenters, faceAreas = [], []
    # 依序 取出每張人臉資訊
    for (x, y, w, h) in faces:
        # 框住人臉
        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 0, 255), 2)
        # 計算人臉的中心點座標與大小
        cx=x+w//2; cy=y+h//2; area=w*h
        # 以中心點為圓心半徑為5畫一個實心圓
        cv2.circle(img, (cx, cy), 5, (0, 255, 0), cv2.FILLED)
        # 將人臉中心點座標紀錄在串列中
        faceCenters.append([cx, cy])
        # 將人臉大小紀錄在串列中
        faceAreas.append(area)

    # 找出 圖片中最大人臉的位置回傳紀錄的資料
    if len(faceAreas)>0:
        # 找出串列中最大值的索引位置
        idx = faceAreas.index(max(faceAreas))
        # 回傳 最大人臉資訊
        return img, [faceCenters[idx], faceAreas[idx]]
    else: 
        # 沒有偵測到人臉
        return img, [[0,0], 0]

def traceFace(info, w, pid, pError):
    x, y = info[0]    # 人臉 x,y座標
    area = info[1]    # 人臉大小
    fb = 0            # 前進後退的值
    error = x-w//2    # 以設定的寬度中心為基準的誤差
    # 計算 PID控制後的yaw速度
    speed = pid[0]*error + pid[1]*(error-pError)
    # 將 speed 控制在 -50~50之間
    speed = int(np.clip(speed, -50, 50))
    # 人臉大小位置在範圍內，不調整
    if area>faceAreaRange[0] and area<faceAreaRange[1]: fb=0
    # 人臉大小太大，往後退
    elif area>faceAreaRange[1]: fb=-20
    # 人臉大小太小，往前進
    elif area<faceAreaRange[0] and area!=0: fb=20

    # 沒偵測到人臉
    if x==0:
        speed=0; error=0

    # 調整飛行
    tello.send_rc_control(0, fb, 0, speed)
    print('x & y:', info[0])
    print('area: ', area)
    print('speed:', speed)
    if info[0] != [0,0]:
        csvCursor.writerow([info[0], area, speed])
    # error為下一次 PID運算的pError
    return error

file = open('data.csv', 'w')
csvCursor = csv.writer(file)
header = ['x & y', 'area', 'speed']
csvCursor.writerow(header)

while True:
    img = tello.get_frame_read().frame
    cv2.putText(img, Battery, (5, 720 - 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    img = cv2.resize(img, (w, h))
    img, info = findFace(img)
    pError = traceFace(info, w, pid, pError)
    
    print('[faceCenters], [faceAreas]', info)
    cv2.imshow('Tello', img)
    if cv2.waitKey(1) & 0xff==27:
        tello.land()
        tello.end()
        break