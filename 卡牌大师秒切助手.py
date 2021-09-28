import threading
import time
from ctypes import *  # 获取屏幕上某个坐标的颜

import PyHook3
import pythoncom

# <editor-fold desc="模拟点击部分">
PUL = POINTER(c_ulong)


class KeyBdInput(Structure):
    _fields_ = [("wVk", c_ushort),
                ("wScan", c_ushort),
                ("dwFlags", c_ulong),
                ("time", c_ulong),
                ("dwExtraInfo", PUL)]


class HardwareInput(Structure):
    _fields_ = [("uMsg", c_ulong),
                ("wParamL", c_short),
                ("wParamH", c_ushort)]


class MouseInput(Structure):
    _fields_ = [("dx", c_long),
                ("dy", c_long),
                ("mouseData", c_ulong),
                ("dwFlags", c_ulong),
                ("time", c_ulong),
                ("dwExtraInfo", PUL)]


class Input_I(Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]


class Input(Structure):
    _fields_ = [("type", c_ulong),
                ("ii", Input_I)]


class POINT(Structure):
    _fields_ = [("x", c_ulong),
                ("y", c_ulong)]


def get_mpos():
    orig = POINT()
    windll.user32.GetCursorPos(byref(orig))
    return int(orig.x), int(orig.y)


def set_mpos(pos):
    x, y = pos
    windll.user32.SetCursorPos(x, y)


def move_click(pos, move_back=False):
    origx, origy = get_mpos()
    set_mpos(pos)
    FInputs = Input * 2
    extra = c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(0, 0, 0, 2, 0, pointer(extra))
    ii2_ = Input_I()
    ii2_.mi = MouseInput(0, 0, 0, 4, 0, pointer(extra))
    x = FInputs((0, ii_), (0, ii2_))
    windll.user32.SendInput(2, pointer(x), sizeof(x[0]))
    if move_back:
        set_mpos((origx, origy))
        return origx, origy


def sendkey(scancode, pressed):
    FInputs = Input * 1
    extra = c_ulong(0)
    ii_ = Input_I()
    flag = 0x8
    ii_.ki = KeyBdInput(0, 0, flag, 0, pointer(extra))
    InputBox = FInputs((1, ii_))
    if scancode is None:
        return
    InputBox[0].ii.ki.wScan = scancode
    InputBox[0].ii.ki.dwFlags = 0x8

    if not (pressed):
        InputBox[0].ii.ki.dwFlags |= 0x2

    windll.user32.SendInput(1, pointer(InputBox), sizeof(InputBox[0]))


# </editor-fold>


def getRgb(x, y):
    gdi32 = windll.gdi32
    user32 = windll.user32
    hdc = user32.GetDC(None)  # 获取颜值
    pixel = gdi32.GetPixel(hdc, x, y)  # 提取RGB值
    r = pixel & 0x0000ff
    g = (pixel & 0x00ff00) >> 8
    b = pixel >> 16
    return [r, g, b]


def get_color(r, g, b):
    if r == g == b:
        return '灰'
    if (r <= 127 and g <= 127 and b >= 127):
        return ("蓝")
    elif (r <= 127 and g >= 127 and b <= 127):
        return ("绿")
    elif (r >= 127 and g <= 127 and b <= 127):
        return ('红')
    elif (r >= 127 and g >= 127 and b <= 127):
        return ("黄")
    elif (r >= 127 and g <= 127 and b >= 127):
        return ("紫")
    elif (r <= 127 and g >= 127 and b >= 127):
        return ("蓝")
    elif (r >= 127 and g >= 127 and b >= 127):
        return get_color(r - 1, g - 1, b - 1)
    elif (r <= 127 and g <= 127 and b <= 127):
        return get_color(r + 1, g + 1, b + 1)


def down(event):
    # 10 (Q), 11 (W), 12 (E), 13 (R)
    key = event.Key
    global alt_press, working

    # 增加开关功能
    if key == 'Home':
        working = True
        print("切牌开启")
        return False
    if key == 'End':
        working = False
        print("切牌关闭")
        return False

    if not working:
        return True

    if key == 'Lmenu' or key == 'Rmenu':
        alt_press = True
        return True
    # alt 按下中是升级技能操作，不响应抽牌
    if alt_press:
        return True

    if key == "E":
        if tryLisCard('黄'):
            return False
    elif key == "W":
        if tryLisCard('红'):
            return False
    elif key == "Capital":
        if tryLisCard('蓝'):
            return False

    return True


def up(event):
    key = event.Key
    global alt_press
    if key == 'Lmenu' or key == 'Rmenu':
        alt_press = False
    return True


def tryLisCard(color):
    global req_color, cardListening
    if cardListening:
        return False
    cardListening = True
    # 按 w 开始选牌
    click_W()
    # 更新当前需求的颜色为最近一次按下需要的颜色
    req_color = color
    # 开始监听选牌，没启动则启动线程
    threading.Thread(target=getCard).start()
    return True


def click_W():
    # 标记是本软件按下的W
    sendkey(0x11, 1)
    sendkey(0x11, 0)


# 是否抽牌中
cardListening = False
req_color = "黄"
alt_press = False
working = False


# 抽取卡牌
def getCard():
    global req_color, cardListening
    start_time = time.time()
    flag = True
    # 离上次按下的时间超过 3 秒还没选到牌，则选牌失败
    while time.time() - start_time < 3:
        if time.time() - start_time >= 0.15:
            if flag:
                flag = False
                print("开始抽牌", req_color)
            # 开始抽牌
            r, g, b = getRgb(x, y)
            color = get_color(r, g, b)
            if color == req_color:
                click_W()
                print('抽牌成功', req_color)
                cardListening = False
                return
        # 刷新频率，按照每秒 30 帧刷新
        time.sleep(0.034)
    print('抽牌失败', req_color)
    cardListening = False


# 设置获取颜色坐标
def setColorPosition(event):
    global x, y
    x = event.Position[0]
    y = event.Position[1]
    print("当前取色坐标：", x, y, '祝您游戏愉快')
    r, g, b = getRgb(x, y)
    print("当前颜色：", get_color(r, g, b))
    return True


def action():
    hm = PyHook3.HookManager()
    hm.KeyDown = down
    hm.KeyUp = up
    hm.MouseMiddleDown = setColorPosition
    hm.HookKeyboard()
    hm.HookMouse()
    pythoncom.PumpMessages()


x = 35
y = 233
action()
