import serial
import struct
import warnings


class SerialPort(object):
    def __init__(self, port="/dev/serial0", baudrate=9600, timeout=None):
        # print('__init__')
        #超时设置,None：永远等待操作，0为立即返回请求结果，其他值为等待超时时间(单位为秒)
        self.__sp = serial.Serial(port, baudrate, timeout=timeout)
        self.__sendDict = {
            "_byte": [],
            "_short": [],
            "_int": [],
            "_float": [],
            "_longlong": [],
            "_double": [],
        }
        self.__receiveDict = {
            "byte": [],
            "short": [],
            "int": [],
            "float": [],
            "long long": [],
            "double": [],
        }
    
    def __enter__(self):
        # print('__enter__')
        return self

    def __exit__(self, _type, _value, _trace):
        # print('__exit__', _type, _value, _trace)
        if self.__sp.is_open:
            self.__sp.close()

    def __clearReceiveBuffer(self):
        for buf in self.__receiveDict.values():
            buf.clear()

    def clearBuffer(self):
        for buf in self.__sendDict.values():
            buf.clear()

    def setData(self, **vardict):
        for key, value in vardict.items():
            if type(value) in [list, tuple]:
                if self.__sendDict.get(key, None) != None:
                    self.__sendDict[key] = value
                else:
                    warnings.warn(f"wrong key: {key}")
            else:
                if self.__sendDict.get(key, None) != None:
                    self.__sendDict[key] = [value]
                else:
                    warnings.warn(f"wrong key: {key}")

    def appendData(self, **vardict):
        for key, value in vardict.items():
            if type(value) in [list, tuple]:
                if self.__sendDict.get(key, None) != None:
                    self.__sendDict[key].extend(value)
                else:
                    warnings.warn(f"wrong key: {key}")
            else:
                if self.__sendDict.get(key, None) != None:
                    self.__sendDict[key].append(value)
                else:
                    warnings.warn(f"wrong key: {key}")

    def getReceive(self):
        return self.__receiveDict

    def sendData(self, **vardict):
        if vardict:
            self.clearBuffer()
            self.setData(**vardict)
        # 包头
        _message = b'\xa5'
        # 数据数量
        lByte = len(self.__sendDict["_byte"])
        lShort = len(self.__sendDict["_short"])
        lInt = len(self.__sendDict["_int"])
        lFloat = len(self.__sendDict["_float"])
        lLongLong = len(self.__sendDict["_longlong"])
        lDouble = len(self.__sendDict["_double"])
        # 数据格式
        _message += struct.pack('BBBBBB', lByte, lShort, lInt, lFloat, lLongLong, lDouble)
        _format = '>' + 'B'*lByte + 'h'*lShort + 'i'*lInt + 'f'*lFloat + 'q'*lLongLong + 'd'*lDouble
        # 数据本体
        tmpList = [value for key, values in self.__sendDict.items() if values for value in values]
        _message += struct.pack(_format, *tmpList)
        # 校验和
        checksum = sum(_message[1:])
        _message += struct.pack('B', checksum%256)
        # 包尾 
        _message += b'\x5a'
        # 发送数据
        self.__sp.write(_message)

    def receiveData(self):
        bt = self.__sp.read()
        #print(bt.hex())
        # 检测包头
        if bt != b'\xa5':
            return False
        # 获取数据数量
        _message = self.__sp.read(6)
        num = sum(map((lambda x, y: x*y), [1, 2, 4, 4, 8, 8], _message))
        # 获取数据本体
        _message += self.__sp.read(num)
        # 检测校验和
        checksum = struct.pack('B', sum(_message)%256)
        if checksum == self.__sp.read():
            # 检测包尾
            bw = self.__sp.read()
            if bw == b'\x5a':
                # 解包数据数量
                lByte, lShort, lInt, lFloat, lLongLong, lDouble = struct.unpack('BBBBBB', _message[:6])
                # 清空接收缓存
                self.__clearReceiveBuffer()
                # 解包数据本体
                _format = '>' + 'B'*lByte + 'h'*lShort + 'i'*lInt + 'f'*lFloat + 'q'*lLongLong + 'd'*lDouble
                receiveUnpack = struct.unpack(_format, _message[6:])
                receiveUnpack=list(reversed(receiveUnpack))
                # print(receiveUnpack)
                # 将解包后的数据填入接收缓存
                if lByte:
                    while lByte:
                        self.__receiveDict["byte"].append(receiveUnpack.pop())
                        lByte -= 1
                if lShort:
                    while lShort:
                        self.__receiveDict["short"].append(receiveUnpack.pop())
                        lShort -= 1
                if lInt:
                    while lInt:
                        self.__receiveDict["int"].append(receiveUnpack.pop())
                        lInt -= 1
                if lFloat:
                    while lFloat:
                        self.__receiveDict["float"].append(receiveUnpack.pop())
                        lFloat -= 1
                if lLongLong:
                    while lLongLong:
                        self.__receiveDict["long long"].append(receiveUnpack.pop())
                        lLongLong -= 1
                if lDouble:
                    while lDouble:
                        self.__receiveDict["double"].append(receiveUnpack.pop())
                        lDouble -= 1
                return True
        return False


if __name__ == '__main__':
    import threading
    
    with SerialPort() as sp:
        def getInput():
            while True:
                try:
                    txt = input("please input a dict or a list or a byte:")
                    if txt in ['exit', 'q']:
                        break
                    #######危######
                    num = eval(txt)
                    ###############
                    if type(num) is dict:
                        sp.sendData(**num)
                    else:
                        sp.sendData(_byte=num)
                    print(f"you send: {num}")
                except:
                    print("Error: input error")

        task = threading.Thread(target=getInput)
        task.start()
        
        while True:
            if sign_exit:
                break
            if sp.receiveData():
                print(sp.getReceive())
