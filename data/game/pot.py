ACCUMULATION_RATE = {
    0: 4,
    2000: 8,
    3000: 12,
    4500: 16,
    6000: 20,
    8000: 22,
    10000: 24,
    12000: 26,
    15000: 28,
    20000: 30,
}


def get_pot_accumulation_rate(comfort: int) -> int:
    for index, value in enumerate(ACCUMULATION_RATE):
        if comfort < value:
            return ACCUMULATION_RATE[list(ACCUMULATION_RATE)[index - 1]]
    return 4
