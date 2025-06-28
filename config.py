# config.py
"""
Configuration constants for the Driver Monitoring Application.
"""
# "tracking" sau "normal" 
MODE = "tracking" # mod de vizionare 

FPS = 30
VIDEO_W, VIDEO_H = 1280, 960  # dimensiunea pentru inferenta
PREVIEW_W, PREVIEW_H = 800, 480  # dimensiunea ferestrei OpenCV pentru afisaj
PREVIEW_WINDOW_NAME = "Driver Monitor"
QT_PLATFORM = "xcb"

BUTTON_STATES_INITIAL = { # Starea initiala a fiecarei functii
    "water": True, "dark": True, "monitor": True, "phone": True, "timer": False,
    "close": False  
}

BUTTON_TEXTS_MAP = { # Textul adisat pe buton
    "water": {"on": "Water ON", "off": "Water OFF", "display": "Water"},
    "dark": {"on": "Dark ON", "off": "Dark OFF", "display": "Dark"},
    "monitor": {"on": "Monitor ON", "off": "Monitor OFF", "display": "Face"},
    "phone": {"on": "Phone ON", "off": "Phone OFF", "display": "Phone"},
    "timer": {"on": "Timer ON", "off": "Timer OFF", "display": "Timer"},
    "close": {"on": "X", "off": "X", "display": "X"},
}

TIMER_POPUP_OPTIONS = [ 
    ("5 Min", 5 * 60), ("10 Min", 10 * 60), ("15 Min", 15 * 60),
    ("20 Min", 20 * 60), ("30 Min", 30 * 60)
]

BUTTON_ORDER_MAIN_ROW = ["water", "dark", "face", "phone", "timer"]

# Bara butoane
BTN_ITEM_W, BTN_ITEM_H = 110, 40
BTN_ITEM_SPACING = 10
BTN_MAIN_ROW_Y = 15

# Buton inchidere
CLOSE_BTN_W, CLOSE_BTN_H = 40, 40
CLOSE_BTN_MARGIN = 10

# Hidratare
DRINK_INTERVAL = 30  # Secunde inainte de a afisa alerta de hidratare
PROMPT_DURATION = 5  # Secunde cat este afisat un mesaj de alerta

# Intuneric
DARK_CHECK_INTERVAL = 30    # Secunde intre verificarile de luminozitate
DARK_PROMPT_DURATION = 5    # Secunde cat este afisat un mesaj de alerta
DARK_THRESHOLD = 50         # Pragul de luminozitate (0-255) sub care se considera intuneric

# Inchidere ochi
NO_FACE_TIMEOUT = 23  # Secunde fara detectia fetei inainte ca avatarul sa inchida ochii

# Ascundere bara cutoane
BUTTON_VISIBILITY_TIMEOUT = 10  # Secunde inainte de a inchide ochii


# Fereastra cronometru
POPUP_WIDTH_PREVIEW = 300
POPUP_TITLE_HEIGHT_PREVIEW = 40
POPUP_OPTION_BTN_H_PREVIEW = 30
POPUP_OPTION_SPACING_Y_PREVIEW = 10
POPUP_PADDING_PREVIEW = 20
