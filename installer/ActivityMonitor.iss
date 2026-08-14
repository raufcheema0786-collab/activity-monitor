; Inno Setup script for the Activity Monitor desktop app.
; Builds a real Windows installer around the PyInstaller-built exe at
; dist\ActivityMonitor.exe, and asks once, at install time, for the
; monitoring server's address -- the app itself only ever reads this from
; ACTIVITY_MONITOR_BACKEND_URL (see backend_config.py), it has no other way
; to find the server on a machine that isn't this dev box.

#define MyAppName "Activity Monitor"
#define MyAppVersion "1.0.0"
#define MyAppExeName "ActivityMonitor.exe"

[Setup]
AppId={{B3C1B9F0-6E1A-4C2C-9C7E-A1B2C3D4E5F6}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=output
OutputBaseFilename=ActivityMonitorSetup
Compression=lzma
SolidCompression=yes
; Writing a machine-wide environment variable (HKLM) needs admin rights --
; standard for software an IT admin is deploying to an employee's machine.
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; \
    ValueType: string; ValueName: "ACTIVITY_MONITOR_BACKEND_URL"; \
    ValueData: "{code:GetServerAddress}"; Flags: preservestringtype uninsdeletevalue

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName} now"; Flags: nowait postinstall skipifsilent

[Code]
var
  ServerPage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  ServerPage := CreateInputQueryPage(wpSelectDir,
    'Monitoring Server Address',
    'Where is the Activity Monitor server?',
    'Enter the server address your admin gave you (for example, https://monitor.yourcompany.com). ' +
    'This app will not be able to sync or activate without it. If you''re not sure, ask your admin ' +
    'before continuing.');
  ServerPage.Add('Server address:', False);
  // Lets a scripted/IT-pushed install pass the address non-interactively
  // via /ServerURL=..., instead of only ever supporting one admin
  // clicking through this page by hand on every single machine.
  ServerPage.Values[0] := ExpandConstant('{param:ServerURL|http://}');
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = ServerPage.ID then
  begin
    if (Trim(ServerPage.Values[0]) = '') or (Trim(ServerPage.Values[0]) = 'http://') then
    begin
      MsgBox('Please enter the monitoring server''s address before continuing.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

function GetServerAddress(Param: String): String;
begin
  Result := Trim(ServerPage.Values[0]);
end;

const
  EM_HWND_BROADCAST = $FFFF;
  EM_WM_SETTINGCHANGE = $001A;
  EM_SMTO_ABORTIFHUNG = $0002;

function SendMessageTimeout(hWnd: LongInt; Msg: LongInt; wParam: LongInt; lParam: String;
  fuFlags: LongInt; uTimeout: LongInt; var lpdwResult: LongInt): LongInt;
  external 'SendMessageTimeoutA@user32.dll stdcall';

procedure BroadcastEnvironmentChange;
var
  ResultCode: LongInt;
begin
  SendMessageTimeout(EM_HWND_BROADCAST, EM_WM_SETTINGCHANGE, 0, 'Environment', EM_SMTO_ABORTIFHUNG, 5000, ResultCode);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    BroadcastEnvironmentChange;
end;
