# live2d_speech_bot
基于live2d-py实现的语音对话机器人

无需gpu即可实现实时语音对话。

## 编译live2d-py
参考 https://arkueid.github.io/live2d-py-docs/

## 下载live2d模型
https://drive.google.com/file/d/12D1loj66UjBgUGZlsZVGBZ2usZWiZ6Yb/view?usp=sharing  

解压到当前目录，形式为 Resources，包含v2、v3、v3_

## 下载tts模型
https://drive.google.com/file/d/17GrNesqxqLcUlXmxlPaASRCL5dpxxTLV/view?usp=sharing  

解压到当前目录，形式为 tts_models，包含 sherpa-onnx-vits-zh-child 和 sherpa-onnx-vits-zh-ll 两个模型

## 下载asr模型
https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2

mkdir asr_models  
解压到 asr_models 里面

## 运行程序
`
python main_pyside6.py
`

## TODO
✅ 语音识别  
⬜ vad实现，全双工语音对话  
⬜ 大模型多轮对话  
