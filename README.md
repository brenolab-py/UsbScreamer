# UsbScreamer

Utilitário de bandeja para Windows que toca um som quando você **conecta** ou **remove** um pendrive. Leve, sem janela, feito em Python.

🌐 Site oficial: <https://usb-screamer.vercel.app>

## Recursos

- Som ao conectar (`plug.wav`) e ao desconectar (`unplug.wav`) unidades removíveis
- Ícone na bandeja do sistema com menu:
  - Testar os dois sons
  - Iniciar com o Windows (liga/desliga)
  - Meus Sons (personalizar)
  - Site Oficial
  - Sair
- Instância única (não abre duas vezes)
- Log rotativo em `%LOCALAPPDATA%\UsbScreamer\app.log` (até ~1,5 MB)
- Instalação por usuário, sem precisar de administrador

## Instalação

Baixe o instalador (`UsbScreamer_Setup.exe`) pelo [site oficial](https://usb-screamer.vercel.app) e execute. Durante a instalação você pode marcar **Iniciar o UsbScreamer com o Windows**.

> O Windows SmartScreen pode exibir um aviso em executáveis novos. O SHA-256 do instalador está publicado no site para você conferir a integridade do arquivo.

## Sons personalizados

1. Clique com o botão direito no ícone da bandeja e escolha **Meus Sons (personalizar)**.
2. Coloque na pasta que abrir os arquivos `plug.wav` e/ou `unplug.wav`.
3. Pronto: o app usa seus arquivos no lugar dos padrões. Apague-os para voltar ao som original.

Observações:

- Somente formato **WAV** (PCM) é suportado.
- A pasta fica em `%LOCALAPPDATA%\UsbScreamer\sounds`, então atualizações e reinstalações **não apagam** seus sons.

## Limitações conhecidas

- Detecta apenas unidades do tipo **removível** (pendrives e cartões de memória). SSDs e HDs externos USB são reportados pelo Windows como discos fixos e **não** disparam o som.
- A detecção é feita por verificação a cada 1 segundo. Conectar e remover no mesmo segundo pode passar despercebido.

## Rodando pelo código-fonte

Requer Windows e Python 3.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Em modo script, o app procura os sons na pasta `sounds\` ao lado do `main.py`.

## Gerando o executável e o instalador

Requer [Inno Setup](https://jrsoftware.org/isinfo.php).

```powershell
pip install -r requirements-dev.txt
python build_aut.py          # gera dist\UsbScreamer (PyInstaller --onedir)
```

Depois abra `installer.iss` no Inno Setup e compile com **Ctrl + F9** (gera `installer_output\UsbScreamer_Setup.exe`). Para obter o SHA-256 do instalador:

```powershell
python build_aut.py hash
```

Para lançar uma nova versão, atualize `MyAppVersion` em `installer.iss` e os campos de versão em `version_info.txt`.

## Estrutura do projeto

| Arquivo | Função |
|---|---|
| `main.py` | Aplicativo (monitoramento, bandeja, áudio, autostart) |
| `build_aut.py` | Build com PyInstaller e cálculo do hash do instalador |
| `installer.iss` | Script do instalador (Inno Setup) |
| `version_info.txt` | Metadados de versão embutidos no `.exe` |
| `sounds/` | Sons padrão (`plug.wav`, `unplug.wav`) |
| `landingpage/` | Site estático publicado na Vercel |

## Licença

Distribuído sob a licença MIT. Veja o arquivo [LICENSE](LICENSE).

## Autor

Feito por **Breno Perez** ([@brenolab-py](https://github.com/brenolab-py)).