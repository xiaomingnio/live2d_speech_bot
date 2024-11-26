#!/usr/bin/env python3
#
# Copyright (c)  2023  Xiaomi Corporation
import time

import sherpa_onnx
import soundfile as sf


class TTS():
    def __init__(self, base_path):

        tts_config = sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(
                vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                    model=f"{base_path}/model.onnx",
                    lexicon=f"{base_path}/lexicon.txt",
                    data_dir="",
                    dict_dir=f"{base_path}/dict",
                    tokens=f"{base_path}/tokens.txt",
                ),
                provider="cpu",
                debug=False,
                num_threads=4,
            ),
            rule_fsts=f"{base_path}/phone.fst,{base_path}/date.fst,{base_path}/number.fst",
            max_num_sentences=2,
        )
        if not tts_config.validate():
            raise ValueError("Please check your config")

        self.tts = sherpa_onnx.OfflineTts(tts_config)
        self.output_filename = "tmp_tts.wav"
    
    def infer(self, text, sid, speed, audio_file):

        start = time.time()
        audio = self.tts.generate(text, sid=sid, speed=speed)
        end = time.time()

        if len(audio.samples) == 0:
            print("Error in generating audios. Please read previous error messages.")
            return

        elapsed_seconds = end - start
        audio_duration = len(audio.samples) / audio.sample_rate
        real_time_factor = elapsed_seconds / audio_duration

        sf.write(
            audio_file,
            audio.samples,
            samplerate=audio.sample_rate,
            subtype="PCM_16",
        )
        print(f"Saved to {audio_file}")
        print(f"The text is '{text}'")
        print(f"Elapsed seconds: {elapsed_seconds:.3f}")
        print(f"Audio duration in seconds: {audio_duration:.3f}")
        print(f"RTF: {elapsed_seconds:.3f}/{audio_duration:.3f} = {real_time_factor:.3f}")

        return audio_file



