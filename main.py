import sys
import os
import ctypes
from ctypes import wintypes
import logging
from logging.handlers import RotatingFileHandler
import winreg
import winsound
import time
import threading
import webbrowser
import subprocess
from PIL import Image, ImageDraw
import pystray

# --- CONFIGURAÇÃO DE DIRETÓRIOS E LOGGING ---
def get_base_path():
    """Retorna o diretório onde os assets (sons, ícone) estão.
    PyInstaller 6+ (--onedir) coloca os --add-data em _internal (sys._MEIPASS);
    versões anteriores usam a pasta do exe. O fallback cobre os dois casos."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

BASE_PATH = get_base_path()

# Dados do usuário em %LocalAppData%\UsbScreamer (log + sons personalizados)
LOCAL_APP_DATA = os.getenv("LOCALAPPDATA", os.path.expanduser("~"))
LOG_DIR = os.path.join(LOCAL_APP_DATA, "UsbScreamer")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")
USER_SOUNDS_DIR = os.path.join(LOG_DIR, "sounds")

# Log rotativo: no máximo ~1,5 MB no total (app.log + 2 backups)
_log_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=512 * 1024,
    backupCount=2,
    encoding="utf-8"
)
_log_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logging.basicConfig(level=logging.INFO, handlers=[_log_handler])

# --- BLINDAGEM: INSTÂNCIA ÚNICA (MUTEX WIN32) ---
MUTEX_NAME = "UsbScreamer_SingleInstance"
kernel32 = ctypes.windll.kernel32
ERROR_ALREADY_EXISTS = 183

kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
kernel32.CreateMutexW.restype = wintypes.HANDLE

mutex_handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
last_error = kernel32.GetLastError()

if last_error == ERROR_ALREADY_EXISTS:
    logging.warning("Instância duplicada detectada. Encerrando execução.")
    sys.exit(0)

# --- REPRODUÇÃO DE ÁUDIO ASSÍNCRONA ---
def resolve_sound(filename):
    """Ordem: som personalizado do usuário > som embutido (raiz do pacote) > pasta sounds/ (modo script)."""
    candidates = [
        os.path.join(USER_SOUNDS_DIR, filename),
        os.path.join(BASE_PATH, filename),
        os.path.join(BASE_PATH, "sounds", filename),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return candidates[1]

def play_sound(filename):
    sound_path = resolve_sound(filename)
    if not os.path.exists(sound_path):
        logging.error("Arquivo de som não encontrado: %s", sound_path)
        return
    try:
        winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception as e:
        logging.error("Falha ao reproduzir áudio %s: %s", filename, e)

# --- MONITORAMENTO DE DISCOS (DRIVE_REMOVABLE) ---
DRIVE_REMOVABLE = 2

def get_removable_drives():
    """Retorna conjunto de letras de unidade correspondentes a pendrives e unidades removíveis."""
    drives = set()
    bitmask = kernel32.GetLogicalDrives()
    for letter_code in range(26):
        if bitmask & (1 << letter_code):
            drive_letter = f"{chr(65 + letter_code)}:\\"
            drive_type = kernel32.GetDriveTypeW(drive_letter)
            if drive_type == DRIVE_REMOVABLE:
                drives.add(drive_letter)
    return drives

def drive_monitor_loop(stop_event):
    logging.info("Iniciando monitoramento de pendrives/unidades removíveis.")
    try:
        previous_drives = get_removable_drives()
    except Exception as e:
        logging.error("Erro ao obter estado inicial de unidades: %s", e)
        previous_drives = set()

    while not stop_event.is_set():
        try:
            current_drives = get_removable_drives()
            added = current_drives - previous_drives
            removed = previous_drives - current_drives

            # Priorização com elif para evitar sobreposição abrupta no buffer winsound
            if added:
                logging.info("Dispositivo conectado: %s", list(added))
                play_sound("plug.wav")
            elif removed:
                logging.info("Dispositivo desconectado: %s", list(removed))
                play_sound("unplug.wav")

            previous_drives = current_drives
        except Exception as e:
            logging.error("Erro no ciclo de monitoramento: %s", e)

        time.sleep(1.0)

# --- REGISTRO DO WINDOWS (INICIALIZAÇÃO AUTOMÁTICA) ---
RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "UsbScreamer"

def set_autostart(enable=True):
    """Grava ou remove a inicialização em HKCU apenas se for binário congelado."""
    if not getattr(sys, "frozen", False):
        logging.info("Ambiente de script detectado. Registro em HKCU ignorado.")
        return

    exe_path = f'"{sys.executable}"'
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE) as key:
            if enable:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
                logging.info("Inicialização configurada em HKCU: %s", exe_path)
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                    logging.info("Inicialização removida de HKCU.")
                except FileNotFoundError:
                    pass
    except Exception as e:
        logging.error("Erro ao alterar HKCU Run: %s", e)

def is_autostart_enabled():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except FileNotFoundError:
        return False
    except Exception as e:
        logging.error("Erro ao verificar autostart no registro: %s", e)
        return False

# --- CARREGAMENTO DE ÍCONE ---
def load_tray_icon_image():
    """Tenta carregar app.ico ou icon.ico. Se não achar, cria um ícone procedural visível."""
    possible_names = ["app.ico", "icon.ico"]
    for name in possible_names:
        icon_path = os.path.join(BASE_PATH, name)
        if os.path.exists(icon_path):
            try:
                img = Image.open(icon_path)
                return img
            except Exception as e:
                logging.error("Erro ao abrir ícone %s: %s", icon_path, e)

    # Fallback visível: quadrado azul com borda amarela (evita ícone invisível/transparente)
    logging.warning("Nenhum arquivo .ico encontrado em %s. Usando ícone de fallback.", BASE_PATH)
    fallback = Image.new("RGBA", (64, 64), (30, 41, 59, 255))
    draw = ImageDraw.Draw(fallback)
    draw.rectangle([8, 8, 56, 56], fill=(234, 179, 8, 255))
    return fallback

# --- BANDEJA DO SISTEMA (SYSTEM TRAY) ---
def create_tray_icon(stop_event):
    image = load_tray_icon_image()

    def on_toggle_autostart(icon, item):
        new_state = not item.checked
        set_autostart(new_state)

    def on_test_plug(icon, item):
        play_sound("plug.wav")

    def on_test_unplug(icon, item):
        play_sound("unplug.wav")

    def on_open_folder(icon, item):
        try:
            os.makedirs(USER_SOUNDS_DIR, exist_ok=True)
            os.startfile(USER_SOUNDS_DIR)
        except Exception as e:
            logging.error("Erro ao abrir pasta de sons: %s", e)

    def on_open_site(icon, item):
        try:
            webbrowser.open("https://usb-screamer.vercel.app")
        except Exception as e:
            logging.error("Erro ao abrir site: %s", e)

    def on_exit(icon, item):
        logging.info("Solicitado encerramento pelo menu da bandeja.")
        stop_event.set()
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("Testar Conectar (Plug)", on_test_plug),
        pystray.MenuItem("Testar Desconectar (Unplug)", on_test_unplug),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Iniciar com o Windows", on_toggle_autostart, checked=lambda item: is_autostart_enabled()),
        pystray.MenuItem("Meus Sons (personalizar)", on_open_folder),
        pystray.MenuItem("Site Oficial", on_open_site),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Sair", on_exit)
    )

    icon = pystray.Icon("UsbScreamer", image, "UsbScreamer", menu)
    return icon

def main():
    logging.info("UsbScreamer inicializado.")
    stop_event = threading.Event()

    monitor_thread = threading.Thread(target=drive_monitor_loop, args=(stop_event,), daemon=True)
    monitor_thread.start()

    tray_icon = create_tray_icon(stop_event)
    try:
        tray_icon.run()
    finally:
        stop_event.set()
        if mutex_handle:
            kernel32.CloseHandle(mutex_handle)
        logging.info("UsbScreamer finalizado com sucesso.")

if __name__ == "__main__":
    main()
