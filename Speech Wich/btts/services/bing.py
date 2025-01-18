import re
import os
import json
import tempfile
import time
import shutil
import requests

from btts.utils.tokeniz_text import split_text_into_chunks
from btts.utils.generate_user_agent import generate_user_agent

class Bing:
    BING_TRANSLATOR_URL = "https://www.bing.com/translator"
    BING_TTS_API = "https://www.bing.com/tfettts?IG={}&IID=translator.5024.4"
    SSML_TEMPLATE = "<speak version='1.0' xml:lang='{}'><voice name='{}'><prosody rate='{}'>{}</prosody></voice></speak>"
    VOICES_DATA_PATH = "data/voices.json"

    def __init__(self):
        self.user_agent = None
        self.token = None
        self.key = None
        self.IG = None
        self.voices = self.load_voices()

    def initialize_environment(self):
        user_agent = generate_user_agent()
        html = requests.get(self.BING_TRANSLATOR_URL, headers={"User-Agent": user_agent}).text
        self.key, self.token, self.IG = extract_token_and_key(html)
        self.user_agent = user_agent

    def ctts(self, ssml_chunks, filename):
        temp_dir = tempfile.mkdtemp()
        
        reinitialized_environment = False
        for i, ssml in enumerate(ssml_chunks):
            error = self.download_audio(ssml, f"{temp_dir}/{i}.temp")
            if error:
                if "invalid_chunk" in error:
                    shutil.rmtree(temp_dir)
                    return error
                if not reinitialized_environment:
                    self.initialize_environment()
                    reinitialized_environment = True
                error = self.download_audio(ssml, f"{temp_dir}/{i}.temp")
                if error:
                    shutil.rmtree(temp_dir)
                    return error


        output = self.combine_audio_files(temp_dir, filename)
        shutil.rmtree(temp_dir)
        return output

    def combine_audio_files(self, temp_dir, filename):
            
        with open(filename, 'wb') as main_file:
            files = sorted(os.listdir(temp_dir), key=natural_sort_key)
            for file in files:
                with open(f"{temp_dir}/{file}", 'rb') as f:
                    main_file.write(f.read())

    def download_audio(self, ssml, filename):
        data = {
            "ssml": ssml,
            "token": self.token,
            "key": self.key
        }

        params = {
            "url": self.BING_TTS_API.format(self.IG),
            "headers": {"User-Agent": self.user_agent},
            "data": data
        }

        tries = 2
        last_exception = None
        
        while tries > 0:
            try:
                response = requests.post(**params, timeout=400)
                if response.status_code == 500 or response.status_code == 504:
                    tries -= 1
                    response.raise_for_status()
                if response.headers.get('Content-Type') == 'audio/mpeg':
                    with open(filename, "wb") as f:
                        f.write(response.content)
                    response.close()
                    return
                else:
                    response.close()
                    return response.text
            
            except requests.exceptions.Timeout as timeout_exception:
                last_exception = timeout_exception
                tries -= 1
                time.sleep(0.5)
            except Exception as e:
                last_exception = e
                time.sleep(0.5)

        response.close()
        return {"invalid_chunk": ssml, "exception": last_exception}


    def split_text_and_build_ssml(self, text, locale="en-US", voice="en-US-AnaNeural", speed_rate="0.00%"):
        def filter_text(text):
            return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        text_chunks = split_text_into_chunks(filter_text(text), max_chunk_length=3087)
        ssml_chunks = []
        for chunk in text_chunks:
            ssml_chunks.append(self.SSML_TEMPLATE.format(locale, voice, speed_rate, chunk))

        return ssml_chunks


    def load_voices(self):
        with open(self.VOICES_DATA_PATH, "r") as f:
            voices_data = json.loads(f.read())

        return voices_data

    def get_locale(self):
        return list(self.voices)

def extract_token_and_key(html):
    key_token_match = r'var params_AbusePreventionHelper = \[([\s\S]*?)\]'
    IG_pattern = r'",IG:"([A-F\d]+)"'

    key_token_match = re.search(key_token_match, html)
    IG_match = re.search(IG_pattern, html)

    key = token = IG = None
    if key_token_match:
        key, token, _ = key_token_match.group(1).split(",")
        token = token.replace('"', '')

    if IG_match:
        IG = IG_match.group(1)

    return key, token, IG

def natural_sort_key(filename):
    parts = filename.split('.')
    if parts and parts[0].isdigit():
        return int(parts[0])
    return filename
