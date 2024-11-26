import sys
from threading import Thread
from offlinetts import TTS
import pygame
from PySide6.QtCore import Signal, Slot, QThread
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
import time
import re
import uuid
import os
import queue
import time

tts = TTS()
os.makedirs("./tts_wav", exist_ok=True)

# 初始化pygame用于播放音频
pygame.mixer.init()

# 定义队列
text_queue = queue.Queue()
audio_queue = queue.Queue()

class TextToSpeechThread(Thread):
    def __init__(self):
        super().__init__()

    def run(self):
        while True:
            if not text_queue.empty():
                text = text_queue.get()
                # 生成一个随机 UUID
                random_uuid = uuid.uuid4()

                # 将 UUID 转换为字符串
                uuid_str = str(random_uuid)

                audio_file = f"./tts_wav/tmp_tts_{uuid_str}.wav"
                
                audio_file_output = tts.infer(text, 0, 1, audio_file)
                
                audio_queue.put(audio_file_output)
            time.sleep(0.01)  # 稍作延时，避免过度占用 CPU


class AudioPlayThread(Thread):
    def __init__(self, ):
        super().__init__()

    def run(self):
        # 不断检查是否播放完毕
        while True:
            if not audio_queue.empty():
                if not pygame.mixer.get_busy():
                    wav_file = audio_queue.get()  # 从队列中取出音乐文件
                    print("wav_file: ", wav_file)
                    sound = pygame.mixer.Sound(wav_file)
                    sound.play()
            time.sleep(0.1)  # 稍作延时，避免过度占用 CPU

        print("Speech finished.")
        

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Streaming Text to Speech")

        self.layout = QVBoxLayout()

        self.label = QLabel("等待流式回复...")
        self.layout.addWidget(self.label)

        self.button = QPushButton("开始流式回复")
        self.button.clicked.connect(self.on_button_clicked)
        self.layout.addWidget(self.button)

        self.setLayout(self.layout)
        

    def on_button_clicked(self):
        # 模拟大模型的流式返回的文本
        response_text = "你好，今天的天气很好。你想去散步吗？我们可以一起去。"
        self.process_and_speak(response_text)

    def process_and_speak(self, text):
        # 按标点符号分割文本（这里简单分割，可以根据需求优化正则表达式）
        sentences = re.split(r'([。！？])', text)
        sentences = [s + punctuation for s, punctuation in zip(sentences[::2], sentences[1::2])]
        
        # 创建线程处理每一句话的TTS生成和播放
        for sentence in sentences:
            text_queue.put(sentence)
            
            


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    audio_play_thread = AudioPlayThread()
    audio_play_thread.start()
    
    tts_thread = TextToSpeechThread()
    tts_thread.start()  # 启动线程

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
