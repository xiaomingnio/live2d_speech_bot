import json
from PySide6.QtGui import QMouseEvent
# import live2d.v2 as live2d
import live2d.v3 as live2d
import os

from functools import partial

from PySide6.QtCore import QTimerEvent
from PySide6.QtWidgets import QWidget, QSplitter, QApplication, QPushButton, QVBoxLayout, QLineEdit, QLabel, QTextEdit, QScrollArea, QHBoxLayout
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl, Signal, Slot
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor, QIcon
from live2d.utils.lipsync import WavHandler
from live2d.v3.params import StandardParams, Parameter
from offlinetts import TTS
import llm
from text_split import split_sentences, contains_punctuation
import uuid
import queue
import time
from threading import Thread, Event
import pygame
import wave

def validate_wav(file_path):
    """验证 WAV 文件的完整性"""
    if not os.path.isfile(file_path):
        print(f"文件 {file_path} 不存在.")
        return False

    try:
        # 尝试打开 WAV 文件
        with wave.open(file_path, 'rb') as wav_file:
            # 获取 WAV 文件的参数
            num_channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            frame_rate = wav_file.getframerate()
            num_frames = wav_file.getnframes()

            # 打印 WAV 文件的基本信息
            print(f"通道数: {num_channels}")
            print(f"采样宽度 (字节): {sample_width}")
            print(f"采样率: {frame_rate}")
            print(f"总帧数: {num_frames}")

            # 确保文件包含有效的音频数据（即帧数大于0）
            if num_frames == 0:
                print("警告：WAV 文件包含0帧数据！")
                return False

            print("文件有效，格式完整。")
            return True

    except wave.Error as e:
        # 如果打开文件或读取时出现问题，打印错误信息
        print(f"错误：{e}")
        return False

os.makedirs("./tts_wav", exist_ok=True)

tts = TTS(base_path=r"tts_models/sherpa-onnx-vits-zh-ll")
RESOURCES_DIRECTORY = "Resources"


def callback():
    print("motion end")
    
# 定义队列
text_queue = queue.Queue()
audio_queue = queue.Queue()

# 初始化pygame用于播放音频
pygame.mixer.init()

class TextToSpeechThread(Thread):
    def __init__(self):
        super().__init__()
        self.stop_event = Event()  # 初始化stop_event
        self.finish = False


    def run(self):
        while not self.finish:
            if not text_queue.empty():
                text, audio_file = text_queue.get()
                
                audio_file_output = tts.infer(text, 0, 1, audio_file)
                
                audio_queue.put(audio_file_output)
            time.sleep(0.01)  # 稍作延时，避免过度占用 CPU
            
    def stop(self):
        self.stop_event.set()


class AudioPlayThread(Thread):
    def __init__(self):
        super().__init__()
        self.stop_event = Event()  # 初始化stop_event
        self.finish = False

    def run(self):
        # 不断检查是否播放完毕
        while not self.finish:
            if not audio_queue.empty():
                if not pygame.mixer.get_busy():
                    wav_file = audio_queue.get()  # 从队列中取出音乐文件
                    # print("wav_file: ", wav_file)
                    sound = pygame.mixer.Sound(wav_file)
                    sound.play()
            time.sleep(0.1)  # 稍作延时，避免过度占用 CPU

        print("Speech finished.")
    
    def stop(self):
        self.stop_event.set()


class DigitalHuman(QOpenGLWidget):
    model: live2d.LAppModel

    def __init__(self) -> None:
        super().__init__()
        # 去掉了窗口的边框
        # self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        # 设置窗口的透明度
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # 布局
        layout = QVBoxLayout()

        self.setLayout(layout)

        self.setWindowTitle("数字人")
        self.setGeometry(500, 500, 400, 400)  # 固定位置 (100, 100) 和大小 (400, 300)
        # self.setGeometry(300, 300, 300, 100)

        self.a = 0
        self.resize(700, 500)

        self.wavHandler = WavHandler()
        self.lipSyncN = 2.5

    @Slot(str)
    def send_text_to_digitalhuman(self, audio_file):
        print("=============== run here =================", audio_file)
        def thread_target(audio_file1: str):
            while True:
                # if self.wavHandler.is_finish():
                if self.wavHandler.pcmData is None or self.wavHandler.lastOffset >= self.wavHandler.numFrames:  # 数据未加载或者数据已经读取完毕
                    print(f"驱动口型：{audio_file1} ")
                    self.wavHandler.Start(audio_file1)
                    break
                time.sleep(0.1)
        
        path = audio_file
        thread = Thread(target=thread_target, args=(path,))
        thread.start()

    def initializeGL(self) -> None:
        # 将当前窗口作为 OpenGL 的上下文
        # 图形会被绘制到当前窗口
        self.makeCurrent()

        if live2d.LIVE2D_VERSION == 3:
            live2d.glewInit()
            # live2d.setGLProperties()

        # 创建模型
        self.model = live2d.LAppModel()

        model_path = "D:\workspace\live2d_gen\Textoon\outputs\\20250527-210403\\20250527-210403_model"

        # 加载模型参数
        if live2d.LIVE2D_VERSION == 2:
            # 适用于 2 的模型
            self.model.LoadModelJson(os.path.join(RESOURCES_DIRECTORY, "v2/kasumi2/kasumi2.model.json"))
        elif live2d.LIVE2D_VERSION == 3:
            name = "Haru-2"
            # 适用于 3 的模型
            # self.model.LoadModelJson(os.path.join(RESOURCES_DIRECTORY, f"v3_/{name}/{name}.model3.json"))
            # self.model.LoadModelJson(r"Resources/runtime/mark_free_t04.model3.json")
            self.model.LoadModelJson(os.path.join(model_path, "female_01Arkit_6.model3.json"))

        # 以 fps = 30 的频率进行绘图
        self.startTimer(int(1000 / 30))

        # 关闭自动眨眼
        self.model.SetAutoBlinkEnable(True)
        # 关闭自动呼吸
        self.model.SetAutoBreathEnable(True)

        # 参数设置
        config_path = os.path.join(model_path, "config.json")
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
            setparameter = cfg.get("setparameter", {})

            if setparameter['Param']:
                self.model.SetParameterValue(StandardParams.Param, setparameter['Param'])
            if setparameter['Param47']:
                self.model.SetParameterValue(StandardParams.Param47, setparameter['Param47'])
            if setparameter['Param48']:
                self.model.SetParameterValue(StandardParams.Param48, setparameter['Param48'])
            if setparameter['Param54']:
                self.model.SetParameterValue(StandardParams.Param54, setparameter['Param54'])
            if setparameter['Param57']:
                self.model.SetParameterValue(StandardParams.Param57, setparameter['Param57'])
            if setparameter['Param59']:
                self.model.SetParameterValue(StandardParams.Param59, setparameter['Param59'])
            if setparameter['Param60']:
                self.model.SetParameterValue(StandardParams.Param60, setparameter['Param60'])

    def resizeGL(self, w: int, h: int) -> None:
        if self.model:
            # 使模型的参数按窗口大小进行更新
            self.model.Resize(w, h)
    
    def paintGL(self) -> None:
        
        live2d.clearBuffer()

        self.model.Update()

        if self.wavHandler.Update():
            # 利用 wav 响度更新 嘴部张合
            self.model.SetParameterValue(
                StandardParams.ParamJawOpen, self.wavHandler.GetRms() * self.lipSyncN
            )

        self.model.Draw()
    
    def timerEvent(self, a0: QTimerEvent | None) -> None:

        if self.a == 0: # 测试一次播放动作和回调函数
            self.model.StartMotion("TapBody", 0, live2d.MotionPriority.FORCE, onFinishMotionHandler=callback)
            self.a += 1
        
        self.update() 

    def mousePressEvent(self, event: QMouseEvent) -> None:
        # 传入鼠标点击位置的窗口坐标
        self.model.Touch(event.pos().x(), event.pos().y());

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        self.model.Drag(event.pos().x(), event.pos().y())


class Chat(QWidget):
    model: live2d.LAppModel
    
    data_signal = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        # 去掉了窗口的边框
        # self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        # 设置窗口的透明度
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        self.chat_layout = QHBoxLayout()
        # 创建聊天显示区域，包含一个滚动区域
        self.chat_display_area = QTextEdit(self)
        self.chat_display_area.setReadOnly(True)  # 禁止编辑聊天区域
        self.chat_display_area.setAlignment(Qt.AlignTop)  # 文本对齐到顶部
        self.chat_layout.addWidget(self.chat_display_area)

        # 创建输入框和按钮
        self.input_layout = QHBoxLayout()
        self.text_input = QLineEdit(self)
        self.text_input.setPlaceholderText("请输入文本...")
        self.input_layout.addWidget(self.text_input)
        
        # 语音识别按钮 (麦克风图标)
        self.mic_button = QPushButton()
        self.mic_button.setIcon(QIcon("icon/mic.png"))  # 确保有一个麦克风图标的文件
        self.mic_button.clicked.connect(self.start_voice_recognition)
        self.input_layout.addWidget(self.mic_button)
        
        # 创建发送按钮
        self.send_button = QPushButton("发送", self)
        self.send_button.clicked.connect(self.send_message)
        self.input_layout.addWidget(self.send_button)
        
        self.chat_layout.addLayout(self.input_layout)

    
        self.setLayout(self.chat_layout)

        self.setWindowTitle("chat")
        self.setGeometry(100, 100, 400, 400)  # 固定位置 (100, 100) 和大小 (400, 300)

        self.a = 0
        # self.resize(700, 1000)
        
    def start_voice_recognition(self):
        text = "yuyinshibie"
        self.text_input.setText(text)  # 设置文本输入框为识别的文本

    def update_text(self,char_to_add):
        # 获取当前 QTextEdit 的文本
        current_text = self.chat_display_area.toPlainText()

        # 将新字符追加到现有文本中
        new_text = current_text + char_to_add

        # 更新 QTextEdit 控件
        self.chat_display_area.setPlainText(new_text)

        # 保持 QTextEdit 始终滚动到最后
        cursor = self.chat_display_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chat_display_area.setTextCursor(cursor)
    
    def send_message(self):
        # 获取输入框中的文本
        input_text = self.text_input.text()
        self.chat_display_area.append(f"你: {input_text}")
        self.text_input.clear()


        # 大模型上下文回答 TODO
        self.chat_display_area.append(f"机器人: ")
        messages = [{'role': 'user','content': input_text},]
        responds = llm.gpt_35_api_stream(messages)
        text = ''
        split_text = ''
        for res in responds:
            # print(res)
            text += res
            self.update_text(res)
            
            split_text += res
            # print(text)
            if contains_punctuation(split_text, ['.', '!', '?', '。', '！', '？']):
                sentences = split_sentences(split_text)
                if len(sentences) != 2:
                    raise Exception("大模型回复出错。")
                llm_out_text = sentences[0]
                split_text = sentences[1]

                # 生成一个随机 UUID
                random_uuid = uuid.uuid4()

                # 将 UUID 转换为字符串
                uuid_str = str(random_uuid)

                audio_file = f"./tts_wav/tmp_tts_{uuid_str}.wav"
                text_queue.put((llm_out_text, audio_file))
                
                def thread_target(audio_file: str):
                    while True:
                        if os.path.exists(audio_file) and validate_wav(audio_file):
                            self.data_signal.emit(audio_file)
                            break
                        time.sleep(0.1)
                        
                thread = Thread(target=thread_target, args=(audio_file,))
                thread.start()
        

        # 清空文本输入框
        self.text_input.clear()
        

if __name__ == "__main__":
    import sys
    live2d.init()

    app = QApplication(sys.argv)
    # win = MainWindow()
    
    audio_play_thread = AudioPlayThread()
    audio_play_thread.start()
    
    tts_thread = TextToSpeechThread()
    tts_thread.start()  # 启动线程
    
    chat = Chat()
    digital_human = DigitalHuman()
        
    # 信号连接
    chat.data_signal.connect(digital_human.send_text_to_digitalhuman)
    
    chat.show()
    digital_human.show()
    app.exec()

    live2d.dispose()
    audio_play_thread.finish = True
    tts_thread.finish = True
    
    sys.exit(0)  # 退出程序