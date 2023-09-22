import threading
import time
from ctypes import POINTER, c_ulong, Structure, c_ushort, c_short, c_long, byref, windll, pointer, sizeof, Union

import PyHook3
import pythoncom
import wx

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


#
# mouse_button_down_mapping = {
#     MouseButton.LEFT.name: 0x0002,
#     MouseButton.MIDDLE.name: 0x0020,
#     MouseButton.RIGHT.name: 0x0008
# }
#
# mouse_button_up_mapping = {
#     MouseButton.LEFT.name: 0x0004,
#     MouseButton.MIDDLE.name: 0x0040,
#     MouseButton.RIGHT.name: 0x0010
# }
# 模拟鼠标点击
def send_mouse(scancode, pressed):
    if scancode is None:
        return
    if scancode == 'left' and pressed:
        scancode = 0x0002
    elif scancode == 'left' and not pressed:
        scancode = 0x0004
    elif scancode == 'right' and pressed:
        scancode = 0x0008
    elif scancode == 'right' and not pressed:
        scancode = 0x0010

    extra = c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(0, 0, 0, scancode, 0, pointer(extra))
    x = Input(c_ulong(0), ii_)
    windll.user32.SendInput(1, pointer(x), sizeof(x))


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

import wx.adv


# <editor-fold desc="系统托盘部分">
class TaskBarIcon(wx.adv.TaskBarIcon):
    ID_About = wx.NewId()
    ID_Close = wx.NewId()

    def __init__(self, frame):
        wx.adv.TaskBarIcon.__init__(self)
        self.frame = frame
        self.SetIcon(wx.Icon(name='icon.ico'), '走A吧少年！')  # wx.ico为ico图标文件
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.OnTaskBarLeftDClick)
        self.Bind(wx.EVT_MENU, self.OnAbout, id=self.ID_About)
        self.Bind(wx.EVT_MENU, self.OnClose, id=self.ID_Close)

    def OnTaskBarLeftDClick(self, event):
        if self.frame.IsIconized():
            self.frame.Iconize(False)
        if not self.frame.IsShown():
            self.frame.Show(True)
        self.frame.Raise()

    def OnAbout(self, event):
        wx.MessageBox("kamui777：把游戏里快捷攻击改成Z，默认Z键位攻击!", '使用帮助')

    def OnClose(self, event):
        self.Destroy()
        self.frame.Destroy()

    # 右键菜单
    def CreatePopupMenu(self):
        menu = wx.Menu()
        menu.Append(self.ID_About, '使用帮助')
        menu.Append(self.ID_Close, '退出')
        return menu


# </editor-fold>

class MainWindow(wx.Frame):
    key_a = 0x1e
    key_z = 0x2c
    sleepTime = 0.01
    press_flag = False
    currentKey = "A"
    press_the_trigger_button = False

    def onKeyDown(self, event):
        if event.Key == self.currentKey and not self.isPause:
            # 按住A键，开始输出
            self.press_the_trigger_button = True
            return self.press_flag
        elif not self.IsIconized() and event.Key == "Escape":
            self.Iconize(True)
            return False
        elif self.start_setting:
            self.currentKey = event.Key
            self.start_setting = False
            self.message_text.Label = "已经绑定到：" + self.currentKey
            self.Iconize(False)
            return False

        return True

    def onKeyUp(self, event):
        if event.Key == self.currentKey and not self.isPause:
            # 松开A键，结束输出
            self.press_the_trigger_button = False
            return self.press_flag

        return True

    def action(self):
        while True:
            if self.press_the_trigger_button and not self.isPause:
                self.press_one(self.key_z)
                
            time.sleep(self.sleepTime)

    def press_one(self, key):
        # 如果要把A键也涵盖进来就把self.press_flag代码放开
        # self.press_flag = True
        # 按下
        sendkey(key, 1)
        # 松开
        sendkey(key, 0)
        # 休息
        time.sleep(self.sleepTime)
        # self.press_flag = False

    def key_listener(self, ):
        hm = PyHook3.HookManager()
        hm.KeyDown = self.onKeyDown
        hm.KeyUp = self.onKeyUp
        hm.HookKeyboard()
        pythoncom.PumpMessages()

    def OnClose(self, event):
        # self.taskBarIcon.Destroy()
        # self.Destroy()
        self.Iconize(True)

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, pos=wx.DefaultPosition, style=wx.DEFAULT_FRAME_STYLE ^ (
                wx.MAXIMIZE_BOX | wx.SYSTEM_MENU) | wx.STAY_ON_TOP,
                          size=(176, 120))

        self.SetBackgroundColour("#ffffff")
        self.SetIcon(wx.Icon('icon.ico'))
        self.taskBarIcon = TaskBarIcon(self)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.isPause = False
        self.start_setting = False

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer3 = wx.BoxSizer(wx.HORIZONTAL)

        self.text1 = wx.StaticText(self, name="aa", label="停滞", size=(40, -1), style=wx.ALIGN_CENTER)
        self.text_num1 = wx.StaticText(self, name="aa", label=str(self.sleepTime), size=(60, -1),
                                       style=wx.ALIGN_CENTER)
        self.text1.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL))
        self.text_num1.SetFont(wx.Font(20, wx.SWISS, wx.NORMAL, wx.FONTWEIGHT_BOLD))
        self.text1.SetForegroundColour('#000000')
        self.text_num1.SetForegroundColour('#FF0000')
        self.button_up1 = wx.Button(self, name="up1", label="↑", size=(30, 30))
        self.button_down1 = wx.Button(self, name="down1", label="↓", size=(30, 30))
        self.Bind(wx.EVT_BUTTON, self.onClick, self.button_up1)
        self.Bind(wx.EVT_BUTTON, self.onClick, self.button_down1)
        self.sizer1.Add(self.text1, flag=wx.ALIGN_CENTER)
        self.sizer1.Add(self.text_num1, flag=wx.ALIGN_CENTER)
        self.sizer1.Add(self.button_down1, flag=wx.ALIGN_CENTER)
        self.sizer1.Add(self.button_up1, flag=wx.ALIGN_CENTER)

        self.button_start = wx.Button(self, name="start", label="开", size=(40, 30))
        self.button_stop = wx.Button(self, name="stop", label="关", size=(40, 30))
        self.button_setting = wx.Button(self, name="setting", label="设触发键", size=(80, 30))
        self.Bind(wx.EVT_BUTTON, self.onClick, self.button_start)
        self.Bind(wx.EVT_BUTTON, self.onClick, self.button_stop)
        self.Bind(wx.EVT_BUTTON, self.onClick, self.button_setting)
        self.sizer2.Add(self.button_start, flag=wx.ALIGN_CENTER)
        self.sizer2.Add(self.button_stop, flag=wx.ALIGN_CENTER)
        self.sizer2.Add(self.button_setting, flag=wx.ALIGN_CENTER)

        self.message_text = wx.StaticText(self, name="aa", label="已启动,按住[" + self.currentKey + "]攻击!")
        self.message_text.SetForegroundColour('#000000')
        self.sizer3.Add(self.message_text)

        self.sizer.Add(self.sizer1)
        self.sizer.Add(self.sizer2)
        self.sizer.Add(self.sizer3)

        self.SetSizer(self.sizer)
        self.Show(True)

        self.thread_key = threading.Thread(target=self.key_listener)
        self.thread_key.daemon = True
        self.thread_key.start()

        self.thread_action = threading.Thread(target=self.action)
        self.thread_action.daemon = True
        self.thread_action.start()

    def onClick(self, event):
        name = event.GetEventObject().GetName()
        if name == "up1":
            self.update_number(self.text_num1, True, 0.01, 0.5, 0.01)
        elif name == "down1":
            self.update_number(self.text_num1, False, 0.01, 0.5, 0.01)
        elif name == "start":
            self.isPause = False
            self.SetTransparent(255)  # 设置透明
            self.message_text.Label = "已启动,按住[" + self.currentKey + "]攻击!"
            pass
        elif name == "stop":
            self.isPause = True
            self.SetTransparent(90)  # 设置透明
            self.message_text.Label = "已关闭"
        elif name == "setting":
            self.start_setting = True
            self.currentKey = ""
            self.message_text.Label = "按任意键完成绑定"
            pass

    def update_number(self, who, isUp, min, max, min_diff):
        if isUp:
            num = float(who.Label) + min_diff
        else:
            num = float(who.Label) - min_diff
        num = round(num, 2)
        if num < min:
            num = min
        if num > max:
            num = max
        if who == self.text_num1:
            self.sleepTime = num
        who.SetLabel(str(num))


app = wx.App(False)
ui = MainWindow(None, "刀!")
ui.Centre()
app.MainLoop()
