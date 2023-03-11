UPGRADE_EXP = {
    1: {"next_level": 1000, "total_exp": 0},
    2: {"next_level": 1325, "total_exp": 1000},
    3: {"next_level": 1700, "total_exp": 2325},
    4: {"next_level": 2150, "total_exp": 4025},
    5: {"next_level": 2625, "total_exp": 6175},
    6: {"next_level": 3150, "total_exp": 8800},
    7: {"next_level": 3725, "total_exp": 11950},
    8: {"next_level": 4350, "total_exp": 15675},
    9: {"next_level": 5000, "total_exp": 20025},
    10: {"next_level": 5700, "total_exp": 25025},
    11: {"next_level": 6450, "total_exp": 30725},
    12: {"next_level": 7225, "total_exp": 37175},
    13: {"next_level": 8050, "total_exp": 44400},
    14: {"next_level": 8925, "total_exp": 52450},
    15: {"next_level": 9825, "total_exp": 61375},
    16: {"next_level": 10750, "total_exp": 71200},
    17: {"next_level": 11725, "total_exp": 81950},
    18: {"next_level": 12725, "total_exp": 93675},
    19: {"next_level": 13775, "total_exp": 106400},
    20: {"next_level": 14875, "total_exp": 120175},
    21: {"next_level": 16800, "total_exp": 135050},
    22: {"next_level": 18000, "total_exp": 151850},
    23: {"next_level": 19250, "total_exp": 169850},
    24: {"next_level": 20550, "total_exp": 189100},
    25: {"next_level": 21875, "total_exp": 209650},
    26: {"next_level": 23250, "total_exp": 231525},
    27: {"next_level": 24650, "total_exp": 254775},
    28: {"next_level": 26100, "total_exp": 279425},
    29: {"next_level": 27575, "total_exp": 305525},
    30: {"next_level": 29100, "total_exp": 333100},
    31: {"next_level": 30650, "total_exp": 362200},
    32: {"next_level": 32250, "total_exp": 392850},
    33: {"next_level": 33875, "total_exp": 425100},
    34: {"next_level": 35550, "total_exp": 458975},
    35: {"next_level": 37250, "total_exp": 494525},
    36: {"next_level": 38975, "total_exp": 531775},
    37: {"next_level": 40750, "total_exp": 570750},
    38: {"next_level": 42575, "total_exp": 611500},
    39: {"next_level": 44425, "total_exp": 654075},
    40: {"next_level": 46300, "total_exp": 698500},
    41: {"next_level": 50625, "total_exp": 744800},
    42: {"next_level": 52700, "total_exp": 795425},
    43: {"next_level": 54775, "total_exp": 848125},
    44: {"next_level": 56900, "total_exp": 902900},
    45: {"next_level": 59075, "total_exp": 959800},
    46: {"next_level": 61275, "total_exp": 1018875},
    47: {"next_level": 63525, "total_exp": 1080150},
    48: {"next_level": 65800, "total_exp": 1143675},
    49: {"next_level": 68125, "total_exp": 1209475},
    50: {"next_level": 70475, "total_exp": 1277600},
    51: {"next_level": 76500, "total_exp": 1348075},
    52: {"next_level": 79050, "total_exp": 1424575},
    53: {"next_level": 81650, "total_exp": 1503625},
    54: {"next_level": 84275, "total_exp": 1585275},
    55: {"next_level": 86950, "total_exp": 1669550},
    56: {"next_level": 89650, "total_exp": 1756500},
    57: {"next_level": 92400, "total_exp": 1846150},
    58: {"next_level": 95175, "total_exp": 1938550},
    59: {"next_level": 98000, "total_exp": 2033725},
    60: {"next_level": 100875, "total_exp": 2131725},
    61: {"next_level": 108950, "total_exp": 2232600},
    62: {"next_level": 112050, "total_exp": 2341550},
    63: {"next_level": 115175, "total_exp": 2453600},
    64: {"next_level": 118325, "total_exp": 2568775},
    65: {"next_level": 121525, "total_exp": 2687100},
    66: {"next_level": 124775, "total_exp": 2808625},
    67: {"next_level": 128075, "total_exp": 2933400},
    68: {"next_level": 131400, "total_exp": 3061475},
    69: {"next_level": 134775, "total_exp": 3192875},
    70: {"next_level": 138175, "total_exp": 3327650},
    71: {"next_level": 148700, "total_exp": 3465825},
    72: {"next_level": 152375, "total_exp": 3614525},
    73: {"next_level": 156075, "total_exp": 3766900},
    74: {"next_level": 159825, "total_exp": 3922975},
    75: {"next_level": 163600, "total_exp": 4082800},
    76: {"next_level": 167425, "total_exp": 4246400},
    77: {"next_level": 171300, "total_exp": 4413825},
    78: {"next_level": 175225, "total_exp": 4585125},
    79: {"next_level": 179175, "total_exp": 4760350},
    80: {"next_level": 183175, "total_exp": 4939525},
    81: {"next_level": 216225, "total_exp": 5122700},
    82: {"next_level": 243025, "total_exp": 5338925},
    83: {"next_level": 273100, "total_exp": 5581950},
    84: {"next_level": 306800, "total_exp": 5855050},
    85: {"next_level": 344600, "total_exp": 6161850},
    86: {"next_level": 386950, "total_exp": 6506450},
    87: {"next_level": 434425, "total_exp": 6893400},
    88: {"next_level": 487625, "total_exp": 7327825},
    89: {"next_level": 547200, "total_exp": 7815450},
    90: {"next_level": None, "total_exp": 8362650},
}


def get_exp_table():
    return UPGRADE_EXP
