CITIES = {
    0: {
        "cht": "未知城市",
        "en": "Unknown models.City",
        "jp": "未知の都市",
        "chs": "未知城市",
        "fr": "Ville inconnue",
        "de": "Unbekannte Stadt",
        "es": "Ciudad desconocida",
        "pt": "Cidade desconhecida",
        "ru": "Неизвестный город",
        "kr": "알 수없는 도시",
        "vi": "Thành phố không xác định",
        "id": "Kota tidak diketahui",
        "th": "เมืองที่ไม่รู้จัก",
    },
    1: {
        "cht": "蒙德",
        "en": "Mondstat",
        "jp": "蒙德",
        "chs": "蒙德",
        "fr": "Mondstat",
        "de": "Mondstat",
        "es": "Mondstat",
        "pt": "Mondstat",
        "ru": "Мондштадта",
        "kr": "몬드",
        "vi": "Mondstat",
        "id": "Mondstat",
        "th": "Mondstat",
    },
    2: {
        "cht": "璃月",
        "en": "Liyue",
        "jp": "璃月",
        "chs": "璃月",
        "fr": "Liyue",
        "de": "Liyue",
        "es": "Liyue",
        "pt": "Liyue",
        "ru": "Ли Юэ",
        "kr": "리월",
        "vi": "Liyue",
        "id": "Liyue",
        "th": "Liyue",
    },
    3: {
        "cht": "稻妻",
        "en": "Inazuma",
        "jp": "稻妻",
        "chs": "稻妻",
        "fr": "Inazuma",
        "de": "Inazuma",
        "es": "Inazuma",
        "pt": "Inazuma",
        "ru": "Инадзумы",
        "kr": "이나즈마",
        "vi": "Inazuma",
        "id": "Inazuma",
        "th": "Inazuma",
    },
    4: {
        "cht": "須彌",
        "en": "Sumeru",
        "jp": "須彌",
        "chs": "須彌",
        "fr": "Sumeru",
        "de": "Sumeru",
        "es": "Sumeru",
        "pt": "Sumeru",
        "ru": "Сумеру",
        "kr": "수메르",
        "vi": "Sumeru",
        "id": "Sumeru",
        "th": "Sumeru",
    },
}


def get_city_name(city_id: int, lang: str) -> str:
    try:
        return CITIES[city_id][lang]
    except KeyError:
        return CITIES[0][lang]


LANGS = {
    "chs": "zh-CN",
    "cht": "zh-TW",
    "en": "en-US",
    "fr": "fr",
    "de": "de",
    "es": "es-ES",
    "pt": "pr-BR",
    "ru": "ru",
    "jp": "ja",
    "kr": "ko",
    "vi": "vi",
    "id": "id",
    "th": "th",
    "it": "it",
    "tr": "tr",
}

WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

EVENTS_URL = "https://api.ambr.top/assets/data/event.json"
