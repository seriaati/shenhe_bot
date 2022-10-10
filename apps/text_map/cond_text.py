from typing import Literal
import yaml

from apps.text_map.convert_locale import to_paths

class CondText:
    def __init__(self):
        self.data = {}
        files = ['artifact', 'build', 'character','weapon']
        langs = ['en-US', 'zh-TW', 'ja-JP']
        for lang in langs:
            for file in files:
                with open(f"shenhe_external/{lang}/{file}.yaml") as f:
                    if lang not in self.data:
                        self.data[lang] = {}
                    self.data[lang][file] = yaml.safe_load(f)
    
    def get_text(self, lang: str, file: Literal['artifact', 'build', 'character',' weapon'], key: str) -> str:
        lang = to_paths(lang)
        if lang not in self.data:
            if lang == 'zh-CN':
                lang = 'zh-TW'
            else:
                lang = 'en-US'
        text = self.data[lang][file].get(key, '')
        if text == '':
            text = self.data['zh-TW'][file].get(key, '')
        return text
    
cond_text = CondText()