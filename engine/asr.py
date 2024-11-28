import sherpa_onnx
import soundfile as sf
import time

class ASR():
    def __init__(self, type):
        self.type = type
        if type == "funasr_parafomer":
            from funasr import AutoModel

            self.hotword_asr_inference_pipeline = AutoModel(model="paraformer-zh",  vad_model="fsmn-vad",  punc_model="ct-punc", vad_kwargs={"speech_noise_thres": 0.9},
                            # spk_model="cam++", 
                            )
            res = self.hotword_asr_inference_pipeline.generate(input='./engine/16k16bit.wav',
                                batch_size_s=300,
                                hotword="./engine/hotword.txt")
            print(res)
            print("加载offline asr 热词模型成功！")
        elif type == "sherpa_onnx_sense_voice":
            model = "./asr_models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/model.onnx"
            tokens = "./asr_models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/tokens.txt"
            self.sherpa_onnx_sense_voice = sherpa_onnx.OfflineRecognizer.from_sense_voice(
                model=model,
                tokens=tokens,
                use_itn=True,
                debug=True,
            )
            

    def asr_infer(self, input_wav):
        if self.type == "funasr_parafomer":
            t0 = time.time()
            res = self.hotword_asr_inference_pipeline.generate(input=input_wav,
                            batch_size_s=300,
                            hotword="./engine/hotword.txt")
            print(res)
            t1 = time.time()
            print("ASR infer time: ", t1-t0)
            return res[0]['text']
        elif self.type == "sherpa_onnx_sense_voice":
            t0 = time.time()
            audio, sample_rate = sf.read(input_wav, dtype="float32", always_2d=True)
            audio = audio[:, 0]  # only use the first channel

            # audio is a 1-D float32 numpy array normalized to the range [-1, 1]
            # sample_rate does not need to be 16000 Hz

            stream = self.sherpa_onnx_sense_voice.create_stream()
            stream.accept_waveform(sample_rate, audio)
            self.sherpa_onnx_sense_voice.decode_stream(stream)
            # print(input_wav)
            print(stream.result)
            t1 = time.time()
            print("ASR infer time: ", t1-t0)
            return stream.result.text
        
if __name__ == "__main__":
    asr = ASR(type='sherpa_onnx_sense_voice')
    print(asr.asr_infer("recorded_audio.wav"))