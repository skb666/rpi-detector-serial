import sys
import time
from SerialPort import *
from Detector import *
from threading import Thread

DEBUG = False
DISPLAY = False

task = None
task_end_flag= False
task_running = False

hsv = None
color_dict = {'red': 1, 'red1': 1, 'green': 2, 'blue': 3}

# 颜色采集
def mouse_click(event, x, y, flags, para):
    global hsv
    if event == cv2.EVENT_LBUTTONDOWN:  # 左边鼠标点击
        print('#'*25)
        print('PIX:', x, y)
        #print("BGR:", frame[y, x])
        #print("GRAY:", gray[y, x])
        print("HSV:", hsv[y, x])

def display():
    global hsv, task_end_flag, task_running, DISPLAY
    task_running = True
    detector = Detector()
    #cv2.namedWindow("cam", 1)
    #video = "http://admin:admin@192.168.43.1:8081/"
    #cam = cv2.VideoCapture(video)
    cv2.namedWindow("cam", cv2.WINDOW_NORMAL)
    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    cv2.setMouseCallback("cam", mouse_click)
    result_last = {}
    while True:
        # 读取当前帧
        ret, frame = cam.read()
        #gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # 对图像进行识别
        detector.run(frame)
        if detector.status and result_last != detector.result:
            result_last = detector.result.copy()
            for result in detector.result:
                if detector.status == 1:
                    print(f"检测到二维码> 类别: {result['type']}, 内容: {result['content']}")
                else:
                    print(f"检测到色块> 颜色: {result['content']}, 大小: {result['size']}")
        cv2.imshow("cam", detector.img)
        # 按ESC键退出
        if (cv2.waitKey(5) == 27):
            DISPLAY = False
            break
        if task_end_flag:
            break
    cam.release()
    cv2.destroyAllWindows()
    task_running = False

def waiting():
    global task_end_flag, task_running
    task_running = True
    while True:
        time.sleep(0.001)
        if task_end_flag:
            break
    task_running = False

def detect_qrcode(detector, sp, sign=0):
    global task_end_flag, DEBUG, task_running, color_dict
    task_running = True
    cam = cv2.VideoCapture(0)
    if sign == 2:
        cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cam.set(cv2.CAP_PROP_FRAME_HEIGHT,480)
    else:
        cam.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        cam.set(cv2.CAP_PROP_FRAME_HEIGHT,240)
    code128 = []
    # 识别二维码
    code128.clear()
    while True:
        # 读取当前帧
        ret, frame = cam.read()
        # 对图像进行识别
        detector.detectQrcode(frame)

        # 判断识别状态(0: 3数字二维码, 1: 3+3数字二维码, 2: 3颜色条形码)
        if sign == 0:
            if detector.status == 1:
                res_qrcode = list(detector.result[0]['content'])
                t = [int(c) for c in res_qrcode]
                if DEBUG:
                    print(res_qrcode, t)
                sp.sendData(_byte=t)
                break
        elif sign == 1:
            if detector.status == 1:
                res_qrcode = list(detector.result[0]['content'].replace('+', ''))
                t = [int(c) for c in res_qrcode]
                if DEBUG:
                    print(res_qrcode, t)
                sp.sendData(_byte=t)
                break
        elif sign == 2:
            if len(code128) < 3:
                if detector.status == 1:
                    res_qrcode = detector.result[0]['content'].strip()
                    if res_qrcode not in code128:
                        if DEBUG:
                            print(res_qrcode)
                        code128.append(res_qrcode)
            else:
                t = [color_dict.get(c, 0) for c in code128]
                if 0 in t:
                    if t.count(0) == 1:
                        for i in range(3):
                            if t[i] == 0:
                                if 1 not in t:
                                    t[i] = 1
                                elif 2 not in t:
                                    t[i] = 2
                                else:
                                    t[i] = 3
                                break
                    else:
                        if DEBUG:
                            print('多于1个条形码识别错误')
                        else:
                            raise Exception('多于1个条形码识别错误')
                if DEBUG:
                    print(code128, t)
                sp.sendData(_byte=t)
                break

        if task_end_flag:
            break
    cam.release()
    task_running = False

def detect_color(detector, sp):
    global task_end_flag, DEBUG, task_running, color_dict
    task_running = True
    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT,240)
    res_color = []
    # 识别色块
    res_color.clear()
    cnt = 0
    while cnt < 3:
        # 读取当前帧
        ret, frame = cam.read()
        # 对图像进行识别
        detector.detectColor(frame)
        # 判断识别状态
        if detector.status == 2:
            for result in detector.result:
                if result['content'] not in res_color:
                    if DEBUG:
                        print(result['content'], result['size'])
                    if result['content'] in ['red', 'red1']:
                        if 'red' not in res_color:
                            res_color.append('red')
                            cnt += 1
                    else:
                        res_color.append(result['content'])
                        cnt += 1
        if task_end_flag:
            break
    if not task_end_flag:
        t = [color_dict[color] for color in res_color]
        if DEBUG:
            print(res_color, t)
        sp.sendData(_byte=t)
    cam.release()
    task_running = False

def main():
    global task_end_flag, task, DEBUG, task_running

    detector = Detector()

    with SerialPort('/dev/serial0', 9600, None) as sp:
        while True:
            if sp.receiveData():
                # 复位检测器
                detector.reset()
                try:
                    detect_type = sp.getReceive()['byte'][0]
                    if DEBUG:
                        print(detect_type)
                    # 等待
                    if detect_type == 0:
                        if task is not None and task_running:
                            task_end_flag = True
                            task.join()
                            task_end_flag = False
                        task = Thread(target=waiting)
                        task.start()
                    # 3数字二维码
                    if detect_type == 1:
                        if task is not None and task_running:
                            task_end_flag = True
                            task.join()
                            task_end_flag = False
                        task = Thread(target=detect_qrcode, args=[detector, sp,])
                        task.start()
                    # 3色块
                    elif detect_type == 2:
                        if task is not None and task_running:
                            task_end_flag = True
                            task.join()
                            task_end_flag = False
                        task = Thread(target=detect_color, args=[detector, sp,])
                        task.start()
                    # 3+3数字二维码
                    elif detect_type == 3:
                        if task is not None and task_running:
                            task_end_flag = True
                            task.join()
                            task_end_flag = False
                        task = Thread(target=detect_qrcode, args=[detector, sp, 1])
                        task.start()
                    # 3颜色条形码
                    elif detect_type == 4:
                        if task is not None and task_running:
                            task_end_flag = True
                            task.join()
                            task_end_flag = False
                        task = Thread(target=detect_qrcode, args=[detector, sp, 2])
                        task.start()
                except:
                    pass
            else:
                if not task_running and DISPLAY:
                    task = Thread(target=display)
                    task.start()

if __name__ == '__main__':
    if 'DEBUG' in sys.argv:
        DEBUG = True

    if 'DISPLAY' in sys.argv:
        DISPLAY = True
        task = Thread(target=display)
        task.start()

    main()
