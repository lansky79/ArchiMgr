; u6863u6848u68c0u7d22u7cfbu7edfu5b89u88c5u811au672c - u4e2du6587u7248

[Setup]
AppName=u6863u6848u68c0u7d22u7cfbu7edf
AppVersion=1.0
DefaultDirName={autopf}\u6863u6848u68c0u7d22u7cfbu7edf
DefaultGroupName=u6863u6848u68c0u7d22u7cfbu7edf
OutputDir=.
OutputBaseFilename=u6863u6848u68c0u7d22u7cfbu7edfu5b89u88c5u7a0bu5e8f
Compression=lzma
SolidCompression=yes

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Files]
Source: "dist\u6863u6848u68c0u7d22u7cfbu7edf\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\u6863u6848u68c0u7d22u7cfbu7edf"; Filename: "{app}\u6863u6848u68c0u7d22u7cfbu7edf.exe"
Name: "{group}\u5378u8f7d"; Filename: "{uninstallexe}"
Name: "{commondesktop}\u6863u6848u68c0u7d22u7cfbu7edf"; Filename: "{app}\u6863u6848u68c0u7d22u7cfbu7edf.exe"

[Run]
Filename: "{app}\u6863u6848u68c0u7d22u7cfbu7edf.exe"; Description: "u7acbu5373u542fu52a8u7a0bu5e8f"; Flags: nowait postinstall skipifsilent

[Messages]
WelcomeLabel1=u6b22u8fceu4f7fu7528u6863u6848u68c0u7d22u7cfbu7edfu5b89u88c5u5411u5bfc
WelcomeLabel2=u8be5u5411u5bfcu5c06u5728u60a8u7684u8ba1u7b97u673au4e0au5b89u88c5 [name/ver]u3002%n%nu5efau8baeu60a8u5728u7ee7u7eedu4e4bu524du5173u95edu6240u6709u5176u4ed6u5e94u7528u7a0bu5e8fu3002
FinishedHeadingLabel=u5b8cu6210 [name] u5b89u88c5u5411u5bfc
FinishedLabel=u5b89u88c5u5411u5bfcu5df2u6210u529fu5730u5b89u88c5u4e86 [name]u3002%n%nu5355u51fbu201cu5b8cu6210u201du9000u51fau5b89u88c5u5411u5bfcu3002
