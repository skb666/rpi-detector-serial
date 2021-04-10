# 树莓派颜色识别-二维码识别-串口收发

## 1、树莓派换国内源

```bash
sudo sed -i 's|raspbian.raspberrypi.org|mirrors.ustc.edu.cn/raspbian|g' /etc/apt/sources.list
sudo sed -i 's|//archive.raspberrypi.org|//mirrors.ustc.edu.cn/archive.raspberrypi.org|g' /etc/apt/sources.list.d/raspi.list
sudo apt update && sudo apt upgrade
```

## 2、软件包与python运行库安装

```bash
sudo apt install vim git python3 python3-pip python3-dev
#将python默认版本设置为python3
sudo update-alternatives --install /usr/bin/python python /usr/bin/python2 1
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 2
#切换python版本
sudo update-alternatives --config python
#pip换国内源
sudo python -m pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
#pip安装运行所需三方库
sudo python -m pip install -U pyzbar pyserial opencv-python
#ImportError: libcblas.so.3: cannot open shared object file
sudo apt install libatlas-base-dev
```

## 3、树莓派配置

```bash
sudo raspi-config
```

选择 "Interface Options" 开启 "Camera"

选择 "Interface Options" 关闭 "Serial Console" 开启 "Serial Port"

重启

```bash
ls -al /dev/serial*
#/dev/serial0 -> ttyS0
#/dev/serial1 -> ttyAMA0
sudo vim /boot/config.txt
```

在最后添加一行 "dtoverlay=pi3-disable-bt"

```bash
#开机自启设置
sudo vim /etc/rc.local
```

在 "exit 0 "前加入 "/usr/bin/python + main.py的绝对路径"

重启

## 4、硬件设置

树莓派 GPIO14(TX) | GPIO15(RX) 分别连接到单片机或其他串口通信设备的RX | TX

将两设备的GND相连

树莓派接上摄像头并重启

## 5、通信协议（可自定义）

| 功能（可自定义）  | 包头 | byte的数量 | short的数量 | int的数量 | float的数量 | longlong的数量 | double的数量 | 数据部分（按类型排序） | 检验和 | 包尾 |
| ----------------- | ---- | ---------- | ----------- | --------- | ----------- | -------------- | ------------ | ---------------------- | ------ | ---- |
| 3数字二维码识别   | 0xa5 | 0x01       | 0x00        | 0x00      | 0x00        | 0x00           | 0x00         | 0x01                   | 0x02   | 0x5a |
| 3色块顺序识别     | 0xa5 | 0x01       | 0x00        | 0x00      | 0x00        | 0x00           | 0x00         | 0x02                   | 0x03   | 0x5a |
| 3+3数字二维码识别 | 0Xa5 | 0x01       | 0x00        | 0x00      | 0x00        | 0x00           | 0x00         | 0x03                   | 0x04   | 0x5a |
| 3颜色条形码识别   | 0xa5 | 0x01       | 0x00        | 0x00      | 0x00        | 0x00           | 0x00         | 0x04                   | 0x05   | 0x5a |
| waiting状态       | 0xa5 | 0x01       | 0x00        | 0x00      | 0x00        | 0x00           | 0x00         | 0x00                   | 0x01   | 0x5a |

将3数字二维码识别的指令发送给树莓派，识别到后树莓派返回用同一协议封装的3个数字（byte）

将3色块顺序识别的指令发送给树莓派，识别到红绿蓝3种颜色的色块后树莓派返回用同一协议封装的颜色先后顺序（byte）

将3+3数字二维码识别的指令发送给树莓派，识别到后树莓派返回用同一协议封装的6个数字（byte）

将3颜色条形码识别的指令发送给树莓派，识别到后树莓派返回用同一协议封装的3个数字（byte）

## 6、运行

```bash
#后台无输出运行
python main.py
# DEBUG：显示串口接收、发送的内容，识别到的色块的尺寸
# DISPLAY：实时图像显示、取色、观察以方便调节机械臂
python main.py DEBUG
python main.py DISPLAY
python main.py DEBUG DISPLAY
```

