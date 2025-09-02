#define MyAppName "档案检索系统"
#define MyAppVersion "1.0.0518"
#define MyAppPublisher "新都区自然资源规划局"
#define MyAppURL ""
#define MyAppExeName "ArchiveManager.exe"

[Setup]
; 注意: AppId的值为单独标识本应用程序。
; 不要在其他应用程序中使用相同的AppId值。
; (若要生成新的GUID，可在菜单中点击 工具|生成GUID。)
AppId={{A0C9E4F5-D6B9-4E3B-B1C7-F8D3A8D5E7B2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; 需要管理员权限以便写入 Program Files
PrivilegesRequired=admin
OutputDir=installer
OutputBaseFilename=ArchiveManager_Setup
SetupIconFile=resources\app.ico
; 使用LZMA压缩，平衡压缩率和安装速度
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; 主程序文件
Source: "dist\ArchiveManager\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; 确保包含所有子目录和文件
; 注意: 不要在任何共享系统文件上使用"Flags: ignoreversion"
; 注意: 不要在任何共享系统文件上使用"Flags: ignoreversion"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// 自定义安装过程代码
procedure InitializeWizard;
begin
  // 添加自定义欢迎页面文本
  WizardForm.WelcomeLabel1.Caption := '欢迎安装 ' + '{#MyAppName}';
  WizardForm.WelcomeLabel2.Caption := '本向导将指引您完成 {#MyAppName} {#MyAppVersion} 的安装。' + #13#10 + #13#10 +
    '建议在继续安装之前关闭所有其他应用程序。' + #13#10 + #13#10 +
    '点击"下一步"继续。';
end;

// 安装完成后的操作
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // 安装完成后的操作
  end;
end;
