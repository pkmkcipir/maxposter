; Skrip Inno Setup untuk Maxposter (client).
; File ini dijalankan otomatis oleh GitHub Actions setelah PyInstaller selesai
; membuild folder client/dist/Maxposter, dan menghasilkan installer
; MaxposterSetup.exe di installer/Output/.
;
; Untuk build manual di komputer sendiri: install Inno Setup 6
; (https://jrsoftware.org/isinfo.php), lalu buka file ini dengan Inno Setup
; Compiler dan klik Compile (pastikan client/dist/Maxposter sudah ada dari
; hasil PyInstaller terlebih dahulu).

#define MyAppName "Maxposter"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Maxposter"
#define MyAppExeName "Maxposter.exe"

[Setup]
AppId={{8F2C1A4E-9B3D-4F5A-8E1C-2D3B4A5C6D7E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=MaxposterSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\client\dist\Maxposter\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
