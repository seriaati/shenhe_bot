import yaml

from .convert_locale import CROWDIN_LANGS


class CondText:
    def __init__(self):
        self.data = {}
        files = ["artifact", "build", "character", "weapon"]
        langs = ["en-US", "zh-TW"]
        for lang in langs:
            for file in files:
                with open(f"shenhe_external/{lang}/{file}.yaml", encoding="utf-8") as f:
                    if lang not in self.data:
                        self.data[lang] = {}
                    try:
                        self.data[lang][file] = yaml.safe_load(f)
                    except Exception:  # skipcq: PYL-W0703
                        print(f"Error loading {lang}/{file}.yaml")

    def get_text(self, lang: str, file: str, key: str) -> str:
        lang = CROWDIN_LANGS.get(lang, "en-US")
        if lang not in self.data:
            if lang == "zh-CN":
                lang = "zh-TW"
            else:
                lang = "en-US"
        text = self.data[lang][file].get(key, "")
        if text == "":
            text = self.data["zh-TW"][file].get(key, "")
        return text


cond_text = CondText()
