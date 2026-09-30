import hashlib
import os
import shutil
import subprocess
import sys

SETUP_PATH = os.path.join("installer_output", "UsbScreamer_Setup.exe")

def build():
    print("[1/3] Limpando diretórios de build anteriores...")
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f" - Removido: {folder}")

    sep = ";"

    # Localização do ícone (no seu diretório o arquivo chama-se app.ico)
    icon_file = "app.ico" if os.path.exists("app.ico") else "icon.ico"
    if not os.path.exists(icon_file):
        print(f"[AVISO] Arquivo de ícone '{icon_file}' não encontrado. O executável usará o ícone padrão.")

    # Assets empacotados junto ao app (o PyInstaller 6+ os coloca em _internal;
    # o main.py resolve isso via sys._MEIPASS). O ícone dos atalhos vem do próprio exe.
    datas = []

    plug_path = os.path.join("sounds", "plug.wav") if os.path.exists(os.path.join("sounds", "plug.wav")) else "plug.wav"
    unplug_path = os.path.join("sounds", "unplug.wav") if os.path.exists(os.path.join("sounds", "unplug.wav")) else "unplug.wav"

    if os.path.exists(plug_path):
        datas.append(f"{plug_path}{sep}.")
    else:
        print(f"[ERRO] plug.wav não encontrado em {plug_path}!")
        sys.exit(1)

    if os.path.exists(unplug_path):
        datas.append(f"{unplug_path}{sep}.")
    else:
        print(f"[ERRO] unplug.wav não encontrado em {unplug_path}!")
        sys.exit(1)

    if os.path.exists(icon_file):
        # Ícone da bandeja (main.py procura app.ico ou icon.ico)
        datas.append(f"{icon_file}{sep}.")

    pyinstaller_cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=UsbScreamer"
    ]

    if os.path.exists(icon_file):
        pyinstaller_cmd.append(f"--icon={icon_file}")

    # Metadados do exe (publisher, versão, copyright) exibidos em Propriedades > Detalhes
    version_file = "version_info.txt"
    if os.path.exists(version_file):
        pyinstaller_cmd.append(f"--version-file={version_file}")
    else:
        print(f"[AVISO] '{version_file}' não encontrado. O exe será gerado sem metadados de versão.")

    for data in datas:
        pyinstaller_cmd.extend(["--add-data", data])

    pyinstaller_cmd.append("main.py")

    print("\n[2/3] Executando PyInstaller (--onedir)...")
    print(f"Comando: {' '.join(pyinstaller_cmd)}\n")
    result = subprocess.run(pyinstaller_cmd)
    if result.returncode != 0:
        print("\n[ERRO] Falha no processo do PyInstaller.")
        sys.exit(1)

    print("\n[3/3] Build finalizado com sucesso!")
    print(r"Arquivos gerados em: dist\UsbScreamer")
    print("Próximo passo: abra o 'installer.iss' no Inno Setup e aperte Ctrl + F9 para compilar o setup.")
    print("Depois rode: python build_aut.py hash")

def print_setup_hash():
    if not os.path.exists(SETUP_PATH):
        print(f"[ERRO] Instalador não encontrado em {SETUP_PATH}. Compile o installer.iss primeiro.")
        sys.exit(1)

    sha256 = hashlib.sha256()
    with open(SETUP_PATH, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha256.update(chunk)

    print(f"Arquivo: {SETUP_PATH}")
    print(f"SHA-256: {sha256.hexdigest().upper()}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "hash":
        print_setup_hash()
    else:
        build()
