import os
import sys
import subprocess

# --- AUTOMATIC DEPENDENCY CHECKER (Runs before anything else) ---
def check_dependencies():
    missing = []
    for mod in ["pygame", "numpy"]:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
            
    if missing:
        import tkinter as tk
        from tkinter import messagebox

        root_chk = tk.Tk()
        root_chk.withdraw()

        def auto_install():
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "pygame", "numpy"])
                messagebox.showinfo("Success", "Modules installed successfully! Restarting script...")
                top.destroy()
                root_chk.destroy()
                os.execv(sys.executable, [sys.executable] + sys.argv)
            except Exception as e:
                messagebox.showerror("Error", f"Automatic installation failed: {e}\nPlease use Manual Install.")

        def manual_install():
            if os.name == 'nt':
                subprocess.Popen('start cmd /k "pip install pygame numpy"', shell=True)
            else:
                messagebox.showinfo("Manual Install", "Please open your terminal and run:\npip install pygame numpy")
            top.destroy()
            root_chk.destroy()
            sys.exit()

        top = tk.Toplevel(root_chk)
        top.title("Missing Required Modules")
        top.geometry("400x180")
        top.resizable(False, False)
        top.lift()
        top.attributes("-topmost", True)

        lbl = tk.Label(top, text=f"Required modules missing: {', '.join(missing)}\nPlease choose an installation method:", font=("Segoe UI", 10), justify="left", padx=15, pady=15)
        lbl.pack()

        btn_frame = tk.Frame(top)
        btn_frame.pack(pady=10)

        btn_auto = tk.Button(btn_frame, text="Automatic Install", command=auto_install, bg="#00a2ff", fg="white", font=("Segoe UI", 10, "bold"), padx=10, pady=5)
        btn_auto.pack(side="left", padx=8)

        btn_manual = tk.Button(btn_frame, text="Manual Install (CMD)", command=manual_install, bg="#e0e0e0", fg="black", font=("Segoe UI", 10), padx=10, pady=5)
        btn_manual.pack(side="left", padx=8)

        root_chk.mainloop()
        sys.exit()

check_dependencies()

# --- MAIN APP IMPORTS ---
import json
import locale
import tempfile
import threading
import time
import tkinter as tk
from tkinter import filedialog, simpledialog
import numpy as np
import pygame

# Initialize Tkinter root (hidden) for file dialogs and prompts
root = tk.Tk()
root.withdraw()

# --- CONFIGURATION & TEMP STORAGE ---
TEMP_DIR = tempfile.gettempdir()
CONFIG_FILE = os.path.join(TEMP_DIR, "python_piano_config.json")

# --- TRANSLATIONS & LOCALIZATION ---
TRANSLATIONS = {
    "en": {
        "upload": "Upload Sound",
        "keys": "Set Keys",
        "record": "Record",
        "stop": "Stop",
        "play": "Play/Replay",
        "loop": "Toggle Loop",
        "export": "Export Code",
        "import": "Import Code",
        "fullscreen": "Fullscreen",
        "sound": "Sound: ",
        "language": "Language: ",
        "default_synth": "Default Synth",
    },
    "fr": {
        "upload": "Charger Son",
        "keys": "Touches",
        "record": "Enregistrer",
        "stop": "Arrêter",
        "play": "Jouer",
        "loop": "Boucle",
        "export": "Exporter",
        "import": "Importer",
        "fullscreen": "Plein écran",
        "sound": "Son: ",
        "language": "Langue: ",
        "default_synth": "Synth Défaut",
    },
    "es": {
        "upload": "Subir Sonido",
        "keys": "Teclas",
        "record": "Grabar",
        "stop": "Parar",
        "play": "Reproducir",
        "loop": "Bucle",
        "export": "Exportar",
        "import": "Importar",
        "fullscreen": "Pantalla Completa",
        "sound": "Sonido: ",
        "language": "Idioma: ",
        "default_synth": "Sintetizador Pred.",
    },
    "de": {
        "upload": "Sound Hochladen",
        "keys": "Tasten",
        "record": "Aufnehmen",
        "stop": "Stopp",
        "play": "Abspielen",
        "loop": "Schleife",
        "export": "Exportieren",
        "import": "Importieren",
        "fullscreen": "Vollbild",
        "sound": "Ton: ",
        "language": "Sprache: ",
        "default_synth": "Standard Synth",
    },
}

def get_system_lang():
    try:
        sys_lang = locale.getdefaultlocale()[0]
        if sys_lang:
            code = sys_lang[:2].lower()
            if code in TRANSLATIONS:
                return code
    except:
        pass
    return "en"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"language": get_system_lang(), "saved_sounds": []}

def save_config(config_data):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_data, f)
    except Exception as e:
        print(f"Error saving config: {e}")

app_config = load_config()
current_lang = app_config.get("language", get_system_lang())
if current_lang not in TRANSLATIONS:
    current_lang = "en"

def t(key):
    return TRANSLATIONS[current_lang].get(key, key)

# --- UI STYLING ---
INITIAL_WIDTH, INITIAL_HEIGHT = 1100, 500
BG_WHITE = (255, 255, 255)
TOOLBAR_BG = (245, 245, 245)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
KEY_BORDER = (180, 180, 180)
BLUE_HOVER = (100, 150, 255)
RED_RECORD = (230, 60, 60)
GREEN_PLAY = (40, 180, 90)
PURPLE_LOOP = (140, 80, 200)

pygame.mixer.pre_init(frequency=44100, size=-16, channels=64, buffer=512)
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=64)
pygame.mixer.set_num_channels(64) # Allow up to 64 simultaneous overlapping sounds

screen = pygame.display.set_mode((INITIAL_WIDTH, INITIAL_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Custom Piano - True Polyphony & Clean Playback")
font = pygame.font.SysFont("Segoe UI", 13)
font_bold = pygame.font.SysFont("Segoe UI", 14, bold=True)
font_key = pygame.font.SysFont("Segoe UI", 10, bold=True)

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

KEYBOARD_POOL = [
    (pygame.K_1, "1"), (pygame.K_2, "2"), (pygame.K_3, "3"), (pygame.K_4, "4"), (pygame.K_5, "5"),
    (pygame.K_6, "6"), (pygame.K_7, "7"), (pygame.K_8, "8"), (pygame.K_9, "9"), (pygame.K_0, "0"),
    (pygame.K_q, "Q"), (pygame.K_w, "W"), (pygame.K_e, "E"), (pygame.K_r, "R"), (pygame.K_t, "T"),
    (pygame.K_y, "Y"), (pygame.K_u, "U"), (pygame.K_i, "I"), (pygame.K_o, "O"), (pygame.K_p, "P"),
    (pygame.K_a, "A"), (pygame.K_s, "S"), (pygame.K_d, "D"), (pygame.K_f, "F"), (pygame.K_g, "G"),
    (pygame.K_h, "H"), (pygame.K_j, "J"), (pygame.K_k, "K"), (pygame.K_l, "L"), (pygame.K_SEMICOLON, ";"),
    (pygame.K_z, "Z"), (pygame.K_x, "X"), (pygame.K_c, "C"), (pygame.K_v, "V"), (pygame.K_b, "B"),
    (pygame.K_n, "N"), (pygame.K_m, "M"), (pygame.K_COMMA, ","), (pygame.K_PERIOD, "."), (pygame.K_SLASH, "/")
]

def midi_to_name(midi_num):
    name = NOTE_NAMES[midi_num % 12]
    octave = (midi_num // 12) - 1
    return f"{name}{octave}"

def is_black_key(midi_num):
    return NOTE_NAMES[midi_num % 12].endswith("#")

def generate_piano_keys(num_keys=88):
    start_midi = 21 if num_keys == 88 else 48
    keys = []
    for i in range(num_keys):
        midi = start_midi + i
        if midi > 108: break
        name = midi_to_name(midi)
        freq = 440.0 * (2.0 ** ((midi - 69) / 12.0))
        pool_item = KEYBOARD_POOL[i % len(KEYBOARD_POOL)]
        keys.append({
            "midi": midi, "name": name, "freq": freq,
            "is_black": is_black_key(midi),
            "shortcut_code": pool_item[0], "shortcut_name": pool_item[1]
        })
    return keys

PIANO_KEYS = generate_piano_keys(88)

def generate_default_tone(frequency=261.63, duration=1.5, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = (0.4 * np.sin(2 * np.pi * frequency * t) +
            0.25 * np.sin(2 * np.pi * (frequency * 2) * t) +
            0.15 * np.sin(2 * np.pi * (frequency * 3) * t) +
            0.1 * np.sin(2 * np.pi * (frequency * 4) * t))
    if frequency < 100: wave *= 1.8
    envelope = np.exp(-3.2 * t)
    audio = wave * envelope
    audio = np.int16(audio * 32767)
    return np.column_stack((audio, audio))

builtin_sounds = [("Default Synth", generate_default_tone())]
win_media_dir = "C:\\Windows\\Media"
if os.path.exists(win_media_dir):
    win_sound_files = [
        ("Win: Chord", "chord.wav"), ("Win: Ding", "ding.wav"),
        ("Win: Tada", "tada.wav"), ("Win: Notify", "Windows Notify.wav"),
        ("Win: Error", "Windows Critical Stop.wav")
    ]
    for label, fname in win_sound_files:
        fpath = os.path.join(win_media_dir, fname)
        if os.path.exists(fpath):
            try:
                snd_obj = pygame.mixer.Sound(fpath)
                builtin_sounds.append((label, pygame.sndarray.array(snd_obj)))
            except: pass

loaded_sound_arrays = [arr for _, arr in builtin_sounds]
sound_names = [name for name, _ in builtin_sounds]
num_builtin_sounds = len(builtin_sounds)

for s_item in app_config.get("saved_sounds", []):
    try:
        if os.path.exists(s_item["path"]):
            snd = pygame.mixer.Sound(s_item["path"])
            loaded_sound_arrays.append(pygame.sndarray.array(snd))
            sound_names.append(s_item["name"])
    except: pass

current_sound_index = 0
piano_sounds = {}
key_states = {}
mouse_pressed_midi = None

is_recording = False
is_playing = False
is_looping = False
recorded_events = []
recording_start_time = 0
playback_thread = None
scroll_offset_x = 0
active_dropdown = None

def ensure_stereo(sound_array):
    if sound_array.ndim == 1:
        sound_array = np.column_stack((sound_array, sound_array))
    elif sound_array.shape[1] == 1:
        sound_array = np.column_stack((sound_array[:, 0], sound_array[:, 0]))
    return np.ascontiguousarray(sound_array, dtype=np.int16)

def pitch_shift(sound_array, semitones):
    sound_array = ensure_stereo(sound_array)
    pitch_factor = 2.0 ** (semitones / 12.0)
    old_length = len(sound_array)
    new_length = int(old_length / pitch_factor)
    if new_length < 20: new_length = 20

    old_indices = np.arange(old_length)
    new_indices = np.linspace(0, old_length - 1, new_length)

    resampled = np.zeros((new_length, 2), dtype=np.int16)
    for i in range(2):
        resampled[:, i] = np.interp(new_indices, old_indices, sound_array[:, i])
    return np.ascontiguousarray(resampled, dtype=np.int16)

def load_and_prepare_sounds(sound_array):
    global piano_sounds, key_states
    sound_array = ensure_stereo(sound_array)
    piano_sounds.clear()
    for key in PIANO_KEYS:
        midi = key["midi"]
        semitones = midi - 60
        shifted_array = pitch_shift(sound_array, semitones)
        piano_sounds[midi] = pygame.sndarray.make_sound(shifted_array)
    key_states = {k["midi"]: False for k in PIANO_KEYS}

load_and_prepare_sounds(loaded_sound_arrays[current_sound_index])

def play_note(midi):
    # FIXED: Always play sound immediately without blocking rapid or simultaneous notes
    if midi in piano_sounds:
        piano_sounds[midi].play()
        key_states[midi] = True
        if is_recording:
            elapsed = time.time() - recording_start_time
            recorded_events.append({"time": round(elapsed, 3), "midi": midi, "type": "down"})

def stop_note(midi):
    if midi in key_states:
        key_states[midi] = False
        if is_recording:
            elapsed = time.time() - recording_start_time
            recorded_events.append({"time": round(elapsed, 3), "midi": midi, "type": "up"})

def handle_custom_sound_upload():
    global loaded_sound_arrays, sound_names, current_sound_index
    file_path = filedialog.askopenfilename(title="Select Custom Sound File", filetypes=[("Audio Files", "*.wav *.ogg *.mp3")])
    if file_path:
        try:
            snd = pygame.mixer.Sound(file_path)
            arr = pygame.sndarray.array(snd)
            filename = os.path.basename(file_path)
            loaded_sound_arrays.append(arr)
            sound_names.append(filename)
            current_sound_index = len(loaded_sound_arrays) - 1
            load_and_prepare_sounds(loaded_sound_arrays[current_sound_index])
            saved_list = app_config.get("saved_sounds", [])
            saved_list.append({"name": filename, "path": file_path})
            app_config["saved_sounds"] = saved_list
            save_config(app_config)
        except Exception as e: print(f"Failed to load audio: {e}")

def remove_sound(index):
    global loaded_sound_arrays, sound_names, current_sound_index
    if index < num_builtin_sounds or index >= len(sound_names): return
    removed_name = sound_names[index]
    saved_list = app_config.get("saved_sounds", [])
    app_config["saved_sounds"] = [s for s in saved_list if s["name"] != removed_name]
    save_config(app_config)
    del loaded_sound_arrays[index]
    del sound_names[index]
    if current_sound_index >= len(loaded_sound_arrays): current_sound_index = len(loaded_sound_arrays) - 1
    load_and_prepare_sounds(loaded_sound_arrays[current_sound_index])

def set_key_count_prompt():
    global PIANO_KEYS, scroll_offset_x
    root.deiconify()
    root.lift()
    count = simpledialog.askinteger("Custom Key Count", "Enter number of piano keys (12 to 88):", initialvalue=len(PIANO_KEYS), minvalue=12, maxvalue=88)
    root.withdraw()
    if count:
        PIANO_KEYS = generate_piano_keys(count)
        load_and_prepare_sounds(loaded_sound_arrays[current_sound_index])
        scroll_offset_x = 0

def export_recording():
    if not recorded_events: return
    code_str = json.dumps(recorded_events)
    root.deiconify()
    root.lift()
    simpledialog.askstring("Export Recording Code", "Copy your recording code below:", initialvalue=code_str)
    root.withdraw()

def import_recording():
    global recorded_events
    root.deiconify()
    root.lift()
    code_str = simpledialog.askstring("Import Recording Code", "Paste your custom recording code below:")
    root.withdraw()
    if code_str:
        try:
            parsed = json.loads(code_str)
            if isinstance(parsed, list): recorded_events = parsed
        except Exception as e: print(f"Invalid code: {e}")

def playback_loop_worker():
    global is_playing
    while is_playing and recorded_events:
        start_time = time.time()
        event_idx = 0
        total_events = len(recorded_events)
        while is_playing and event_idx < total_events:
            current_time = time.time() - start_time
            ev = recorded_events[event_idx]
            if current_time >= ev["time"]:
                if ev["type"] == "down": play_note(ev["midi"])
                else: stop_note(ev["midi"])
                event_idx += 1
            else: time.sleep(0.0005) # Higher precision for fast songs
        if not is_looping: break
        time.sleep(0.3)
    is_playing = False

def toggle_playback():
    global is_playing, playback_thread
    if is_playing: is_playing = False
    else:
        if recorded_events:
            is_playing = True
            playback_thread = threading.Thread(target=playback_loop_worker, daemon=True)
            playback_thread.start()

def start_recording():
    global is_recording, recording_start_time, recorded_events
    recorded_events = []
    recording_start_time = time.time()
    is_recording = True

def stop_all_actions():
    global is_recording, is_playing
    is_recording = False
    is_playing = False

def toggle_loop_mode():
    global is_looping
    is_looping = not is_looping

is_fullscreen = False
def toggle_fullscreen():
    global is_fullscreen, screen
    is_fullscreen = not is_fullscreen
    if is_fullscreen: screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else: screen = pygame.display.set_mode((INITIAL_WIDTH, INITIAL_HEIGHT), pygame.RESIZABLE)

# Main Game Loop
running = True
clock = pygame.time.Clock()

while running:
    current_width, current_height = screen.get_size()
    mouse_pos = pygame.mouse.get_pos()
    mouse_pressed = pygame.mouse.get_pressed()[0]

    screen.fill(BG_WHITE)

    # --- 1. DRAW TOOLBAR ---
    pygame.draw.rect(screen, TOOLBAR_BG, (0, 0, current_width, 65))
    pygame.draw.line(screen, (210, 210, 210), (0, 65), (current_width, 65), 1)

    btn_w, btn_h, btn_y = 100, 34, 15
    start_x = 15

    buttons = [
        {"label": t("keys"), "action": set_key_count_prompt},
        {"label": t("record"), "action": start_recording},
        {"label": t("stop"), "action": stop_all_actions},
        {"label": t("play"), "action": toggle_playback},
        {"label": t("loop"), "action": toggle_loop_mode},
        {"label": t("export"), "action": export_recording},
        {"label": t("import"), "action": import_recording},
        {"label": t("fullscreen"), "action": toggle_fullscreen},
    ]

    ui_rects = []
    for i, btn in enumerate(buttons):
        bx = start_x + (i * (btn_w + 6))
        if bx + btn_w > current_width - 240: break
        rect = pygame.Rect(bx, btn_y, btn_w, btn_h)
        ui_rects.append((rect, btn["action"]))

        is_hovered = rect.collidepoint(mouse_pos)
        is_clicked = is_hovered and mouse_pressed

        if is_hovered or is_clicked:
            fill_color, text_color = BLUE_HOVER, WHITE
        else:
            fill_color, text_color = WHITE, BLACK

        if btn["label"] == t("record") and is_recording: fill_color, text_color = RED_RECORD, WHITE
        elif btn["label"] == t("play") and is_playing: fill_color, text_color = GREEN_PLAY, WHITE
        elif btn["label"] == t("loop") and is_looping: fill_color, text_color = PURPLE_LOOP, WHITE

        pygame.draw.rect(screen, fill_color, rect, border_radius=0)
        pygame.draw.rect(screen, BLACK, rect, 1, border_radius=0)
        txt = font_bold.render(btn["label"], True, text_color)
        screen.blit(txt, (bx + (btn_w - txt.get_width()) // 2, btn_y + (btn_h - txt.get_height()) // 2))

    # --- SOUND & LANGUAGE DROPDOWN BUTTONS ---
    dropdown_w = 135
    sound_btn_rect = pygame.Rect(current_width - 250, btn_y, dropdown_w, btn_h)
    lang_btn_rect = pygame.Rect(current_width - 105, btn_y, 90, btn_h)

    s_hover = sound_btn_rect.collidepoint(mouse_pos)
    pygame.draw.rect(screen, BLUE_HOVER if s_hover else WHITE, sound_btn_rect, border_radius=0)
    pygame.draw.rect(screen, BLACK, sound_btn_rect, 1, border_radius=0)
    s_txt = font.render(f"Sound ▼", True, WHITE if s_hover else BLACK)
    screen.blit(s_txt, (sound_btn_rect.x + 10, sound_btn_rect.y + (btn_h - s_txt.get_height()) // 2))

    l_hover = lang_btn_rect.collidepoint(mouse_pos)
    pygame.draw.rect(screen, BLUE_HOVER if l_hover else WHITE, lang_btn_rect, border_radius=0)
    pygame.draw.rect(screen, BLACK, lang_btn_rect, 1, border_radius=0)
    l_txt = font.render(f"Lang: {current_lang.upper()} ▼", True, WHITE if l_hover else BLACK)
    screen.blit(l_txt, (lang_btn_rect.x + 10, lang_btn_rect.y + (btn_h - l_txt.get_height()) // 2))

    status_y = 72
    status_str = f"{t('sound')}{sound_names[current_sound_index]} | Keys: {len(PIANO_KEYS)} | Rec: {'ON' if is_recording else 'OFF'} | Play: {'ON' if is_playing else 'OFF'} | Loop: {'ON' if is_looping else 'OFF'}"
    status_surf = font.render(status_str, True, (80, 80, 80))
    screen.blit(status_surf, (15, status_y))

    # --- 2. DRAW PIANO KEYS ---
    keyboard_top = 100
    keyboard_height = current_height - 120

    white_keys = [k for k in PIANO_KEYS if not k["is_black"]]
    white_key_width = max(16, (current_width - 30) // max(1, len(white_keys)))
    total_keyboard_width = len(white_keys) * white_key_width

    keys_pressed = pygame.key.get_pressed()
    if keys_pressed[pygame.K_LEFT]: scroll_offset_x = max(0, scroll_offset_x - 12)
    if keys_pressed[pygame.K_RIGHT]: scroll_offset_x = min(max(0, total_keyboard_width - current_width + 30), scroll_offset_x + 12)

    white_key_rects = {}
    current_white_idx = 0
    for key in PIANO_KEYS:
        if not key["is_black"]:
            x = 15 + (current_white_idx * white_key_width) - scroll_offset_x
            rect = pygame.Rect(x, keyboard_top, white_key_width, keyboard_height)
            white_key_rects[key["midi"]] = rect

            is_pressed = key_states.get(key["midi"], False)
            col = (180, 215, 255) if is_pressed else WHITE
            pygame.draw.rect(screen, col, rect)
            pygame.draw.rect(screen, KEY_BORDER, rect, 1)

            if key.get("shortcut_name") and white_key_width > 16:
                s_lbl = font_key.render(key["shortcut_name"], True, (40, 40, 40))
                screen.blit(s_lbl, (x + (white_key_width - s_lbl.get_width()) // 2, keyboard_top + keyboard_height - 60))

            if key["name"].startswith("C") and white_key_width > 18:
                lbl = font.render(key["name"], True, (120, 120, 120))
                screen.blit(lbl, (x + (white_key_width - lbl.get_width()) // 2, keyboard_top + keyboard_height - 25))

            current_white_idx += 1

    black_key_width = int(white_key_width * 0.62)
    black_key_height = int(keyboard_height * 0.58)
    black_key_rects = {}

    current_white_idx = 0
    for key in PIANO_KEYS:
        if not key["is_black"]: current_white_idx += 1
        else:
            prev_white_x = 15 + ((current_white_idx - 1) * white_key_width) - scroll_offset_x
            x = prev_white_x + white_key_width - (black_key_width // 2)
            rect = pygame.Rect(x, keyboard_top, black_key_width, black_key_height)
            black_key_rects[key["midi"]] = rect

            is_pressed = key_states.get(key["midi"], False)
            col = (50, 130, 220) if is_pressed else BLACK
            pygame.draw.rect(screen, col, rect)
            pygame.draw.rect(screen, (70, 70, 70), rect, 1)

            if key.get("shortcut_name") and black_key_width > 10:
                s_lbl = font_key.render(key["shortcut_name"], True, WHITE)
                screen.blit(s_lbl, (x + (black_key_width - s_lbl.get_width()) // 2, keyboard_top + black_key_height - 25))

    # --- 3. DRAW DROPDOWN MENUS ---
    sound_item_rects = []
    delete_btn_rects = []
    lang_item_rects = []
    sound_upload_rect = None

    if active_dropdown == "sound":
        box_h = (len(sound_names) + 2) * 28
        sound_box = pygame.Rect(sound_btn_rect.x, sound_btn_rect.bottom, dropdown_w + 30, box_h)
        pygame.draw.rect(screen, WHITE, sound_box)
        pygame.draw.rect(screen, BLACK, sound_box, 1)

        for idx, sname in enumerate(sound_names):
            item_rect = pygame.Rect(sound_box.x, sound_box.y + (idx * 28), dropdown_w, 28)
            sound_item_rects.append((item_rect, idx))
            if item_rect.collidepoint(mouse_pos): pygame.draw.rect(screen, (220, 230, 255), item_rect)
            it_txt = font.render(sname[:18], True, BLACK)
            screen.blit(it_txt, (item_rect.x + 8, item_rect.y + 6))

            if idx >= num_builtin_sounds:
                del_rect = pygame.Rect(item_rect.right + 2, item_rect.y + 4, 20, 20)
                delete_btn_rects.append((del_rect, idx))
                pygame.draw.rect(screen, (230, 60, 60), del_rect)
                x_txt = font.render("X", True, WHITE)
                screen.blit(x_txt, (del_rect.x + 5, del_rect.y + 2))

        up_rect = pygame.Rect(sound_box.x, sound_box.y + (len(sound_names) * 28), sound_box.width, 28)
        if up_rect.collidepoint(mouse_pos): pygame.draw.rect(screen, (220, 230, 255), up_rect)
        up_txt = font.render("+ " + t("upload"), True, BLUE_HOVER)
        screen.blit(up_txt, (up_rect.x + 8, up_rect.y + 6))
        sound_upload_rect = up_rect

    elif active_dropdown == "lang":
        langs = [("en", "English"), ("fr", "Français"), ("es", "Español"), ("de", "Deutsch")]
        box_h = len(langs) * 28
        lang_box = pygame.Rect(lang_btn_rect.x, lang_btn_rect.bottom, lang_btn_rect.width, box_h)
        pygame.draw.rect(screen, WHITE, lang_box)
        pygame.draw.rect(screen, BLACK, lang_box, 1)

        for idx, (code, lname) in enumerate(langs):
            item_rect = pygame.Rect(lang_box.x, lang_box.y + (idx * 28), lang_box.width, 28)
            lang_item_rects.append((item_rect, code))
            if item_rect.collidepoint(mouse_pos): pygame.draw.rect(screen, (220, 230, 255), item_rect)
            l_item_txt = font.render(lname, True, BLACK)
            screen.blit(l_item_txt, (item_rect.x + 10, item_rect.y + 6))

    pygame.display.flip()

    # --- 4. EVENT HANDLING ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        elif event.type == pygame.VIDEORESIZE: screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11: toggle_fullscreen()
            else:
                for key in PIANO_KEYS:
                    if key.get("shortcut_code") == event.key:
                        play_note(key["midi"])

        elif event.type == pygame.KEYUP:
            for key in PIANO_KEYS:
                if key.get("shortcut_code") == event.key:
                    stop_note(key["midi"])

        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            action_triggered = False

            if active_dropdown == "sound":
                clicked_sound = False
                for del_r, idx in delete_btn_rects:
                    if del_r.collidepoint(pos):
                        remove_sound(idx)
                        clicked_sound = True
                        break
                if not clicked_sound:
                    for item_r, idx in sound_item_rects:
                        if item_r.collidepoint(pos):
                            current_sound_index = idx
                            load_and_prepare_sounds(loaded_sound_arrays[current_sound_index])
                            active_dropdown = None
                            clicked_sound = True
                            break
                if not clicked_sound and sound_upload_rect and sound_upload_rect.collidepoint(pos):
                    handle_custom_sound_upload()
                    active_dropdown = None
                    clicked_sound = True
                if not clicked_sound: active_dropdown = None
                continue

            elif active_dropdown == "lang":
                clicked_lang = False
                for item_r, code in lang_item_rects:
                    if item_r.collidepoint(pos):
                        current_lang = code
                        app_config["language"] = current_lang
                        save_config(app_config)
                        active_dropdown = None
                        clicked_lang = True
                        break
                if not clicked_lang: active_dropdown = None
                continue

            if sound_btn_rect.collidepoint(pos):
                active_dropdown = "sound" if active_dropdown != "sound" else None
                continue
            elif lang_btn_rect.collidepoint(pos):
                active_dropdown = "lang" if active_dropdown != "lang" else None
                continue

            for rect, action in ui_rects:
                if rect.collidepoint(pos):
                    action()
                    action_triggered = True
                    break

            if not action_triggered and pos[1] >= keyboard_top:
                clicked_midi = None
                for midi, rect in black_key_rects.items():
                    if rect.collidepoint(pos):
                        clicked_midi = midi; break
                if not clicked_midi:
                    for midi, rect in white_key_rects.items():
                        if rect.collidepoint(pos):
                            clicked_midi = midi; break
                if clicked_midi:
                    mouse_pressed_midi = clicked_midi
                    play_note(clicked_midi)

        elif event.type == pygame.MOUSEBUTTONUP:
            if mouse_pressed_midi is not None:
                stop_note(mouse_pressed_midi)
                mouse_pressed_midi = None

    clock.tick(60)

pygame.quit()
