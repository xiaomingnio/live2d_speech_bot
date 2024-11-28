from funasr import AutoModel

hotword_asr_inference_pipeline = AutoModel(model="paraformer-zh",  vad_model="fsmn-vad",  punc_model="ct-punc", vad_kwargs={"speech_noise_thres": 0.9},
                  # spk_model="cam++", 
                  )
res = hotword_asr_inference_pipeline.generate(input='./engine/16k16bit.wav',
                     batch_size_s=300,
                     hotword="./engine/hotword.txt")
print(res)
print("加载offline asr 热词模型成功！")

def asr_infer(input_wav):
    res = hotword_asr_inference_pipeline.generate(input=input_wav,
                     batch_size_s=300,
                     hotword="./engine/hotword.txt")
    print(res)
    return res[0]['text']