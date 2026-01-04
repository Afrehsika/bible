import os
import torch
from transformers import VitsModel, AutoTokenizer
import scipy.io.wavfile as wav
import numpy as np
from pathlib import Path

class TTSEngine:
    def __init__(self):
        self.models = {}
        self.tokenizers = {}
        # Map simple codes to HF model IDs
        self.model_map = {
            "eng": "facebook/mms-tts-eng",
            "aka": "facebook/mms-tts-aka"  # Twi
        }
    
    def _load_model(self, lang):
        if lang not in self.model_map:
            raise ValueError(f"Language {lang} not supported.")
        
        if lang in self.models:
            return self.models[lang], self.tokenizers[lang]
            
        model_id = self.model_map[lang]
        print(f"Loading TTS model: {model_id}...")
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            model = VitsModel.from_pretrained(model_id)
            # Force CPU to avoid 'meta' device errors if accelerate is installed
            model.to("cpu")
            self.models[lang] = model
            self.tokenizers[lang] = tokenizer
            return model, tokenizer
        except Exception as e:
            print(f"Failed to load model {model_id}: {e}")
            return None, None

    def preload(self, lang):
        """Preloads the model for the given language."""
        self._load_model(lang)


    def generate_audio(self, text, lang, output_path):
        """
        Generates audio for `text` in `lang` and saves to `output_path`.
        Returns True if successful.
        """
        if lang not in self.model_map:
            print(f"Language {lang} not supported for TTS.")
            return False

        model, tokenizer = self._load_model(lang)
        if not model or not tokenizer:
            return False

        try:
            inputs = tokenizer(text, return_tensors="pt")
            with torch.no_grad():
                output = model(**inputs).waveform

            # Convert to numpy and save
            audio_data = output.cpu().numpy().squeeze()
            
            # Normalize and convert to 16-bit PCM (essential for mobile compatibility)
            # Clip between -1 and 1 just in case
            audio_data = np.clip(audio_data, -1.0, 1.0)
            # Scale to int16
            audio_data_int16 = (audio_data * 32767).astype(np.int16)
            
            # Save as WAV (MMS usually 16kHz depends on config, VitsModel usually stores sample_rate)
            rate = model.config.sampling_rate
            
            wav.write(output_path, rate, audio_data_int16)
            return True
        except Exception as e:
            print(f"Error generating audio: {e}")
            return False
