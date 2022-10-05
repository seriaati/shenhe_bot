from typing import Literal
import yaml

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
        text = self.data[str(lang)][file].get(key, '')
        if text == '':
            text = self.data['zh-TW'][file].get(key, '')
        return text
    
cond_text = CondText()