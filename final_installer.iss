; 档案检索系统安装脚本 - 中文版

[Setup]
AppName=档案检索系统
AppVersion=1.0
DefaultDirName={autopf}\档案检索系统
DefaultGroupName=档案检索系统
OutputDir=.
OutputBaseFilename=档案检索系统安装程序
Compression=lzma
SolidCompression=yes

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Files]
Source: "dist\u6863u6848u68c0u7d22u7cfbu7edf\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\档案检索系统"; Filename: "{app}\u6863u6848u68c0u7d22u7cfbu7edf.exe"
Name: "{group}\卸载"; Filename: "{uninstallexe}"
Name: "{commondesktop}\档案检索系统"; Filename: "{app}\u6863u6848u68c0u7d22u7cfbu7edf.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\u6863u6848u68c0u7d22u7cfbu7edf.exe"; Description: "立即启动程序"; Flags: nowait postinstall skipifsilent

[Messages]
WelcomeLabel1=欢迎使用档案检索系统安装向导
WelcomeLabel2=该向导将在您的计算机上安装 [name/ver]。%n%n建议您在继续之前关闭所有其他应用程序。
FinishedHeadingLabel=完成 [name] 安装向导
FinishedLabel=安装向导已成功地安装了 [name]。%n%n单击
