; Script de Instalacao Inno Setup para UsbScreamer
; Documentacao: https://jrsoftware.org/ishelp/

#define MyAppName "UsbScreamer"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Breno Perez"
#define MyAppURL "https://usb-screamer.vercel.app"
#define MyAppExeName "UsbScreamer.exe"

[Setup]
AppId={{9F8E7D6C-5B4A-3210-FEDC-BA0976543210}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
; Pasta corrigida no padrao do Windows per-user
DefaultDirName={localappdata}\Programs\{#MyAppName}
DisableDirPage=no
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Impede a instalacao ou atualizacao com o executavel aberto
AppMutex=UsbScreamer_SingleInstance
; Instalacao nivel de usuario sem UAC forcado
PrivilegesRequired=lowest
; Icone do app em "Aplicativos instalados"
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=installer_output
OutputBaseFilename=UsbScreamer_Setup
SetupIconFile=app.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "autostart"; Description: "Iniciar o UsbScreamer com o Windows"; GroupDescription: "Opções adicionais:"

[Files]
; Copia tudo o que esta DENTRO da pasta dist\UsbScreamer diretamente para a raiz da instalacao
Source: "dist\UsbScreamer\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Mesmo formato do set_autostart() do main.py (caminho entre aspas)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\{#MyAppExeName}"""; Tasks: autostart; Flags: uninsdeletevalue

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
{ Remove a entrada de inicialização automática (HKCU\Run) ao desinstalar,
  inclusive quando o usuário a ativou depois pelo menu da bandeja }
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
    RegDeleteValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run', '{#MyAppName}');
end;
