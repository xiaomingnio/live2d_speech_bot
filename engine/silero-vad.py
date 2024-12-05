import time
import torch
from silero_vad import (load_silero_vad,
                          read_audio,
                          get_speech_timestamps,
                          save_audio,
                          VADIterator,
                          collect_chunks)

class VAD():
    def __init__(self):
        self.model = load_silero_vad(onnx=True)
        self.SAMPLING_RATE = 16000

    ## just probabilities
    def get_speech_prob(self, chunk):
        speech_prob = self.model(chunk, self.SAMPLING_RATE).item()
        return speech_prob

if __name__ == "__main__":
    vad = VAD()

    import pyaudio
    import wave
    import numpy as np

    # 配置音频参数
    FORMAT = pyaudio.paInt16  # 16位深度
    CHANNELS = 1              # 单声道
    RATE = 16000              # 采样率
    CHUNK = 1024              # 每次读取的帧数

    # 打开 pyaudio 流
    p = pyaudio.PyAudio()

    # 开启音频流
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("开始录音...")

    # 录音并按每512字节切分数据
    recording = True
    buffer = b''  # 用于暂存音频数据

    while recording:
        # 读取音频流的数据块
        data = stream.read(CHUNK)
        
        # 将读取的数据加入到 buffer
        buffer += data
        
        # 如果 buffer 中的数据大于等于 1024 字节，则进行处理
        # 读取 1024 帧，每帧 2 字节（16 位音频格式）
        while len(buffer) >= 1024:
            # 提取出前 512 字节的数据
            chunk_data = buffer[:1024]
            buffer = buffer[1024:]  # 剩余部分保留在 buffer 中
            
            chunk_data = torch.from_numpy(np.frombuffer(chunk_data, np.int16))
            
            # print(chunk_data.shape)
            
            speech_prob = vad.get_speech_prob(chunk_data)

            print("speech_prob: ", speech_prob)
            

    # 停止录音流
    stream.stop_stream()
    stream.close()
    p.terminate()

    print("录音结束")