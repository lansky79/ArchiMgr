; u6863u6848u68c0u7d22u7cfbu7edfu7b80u5316u5b89u88c5u811au672c

[Setup]
AppName=u6863u6848u68c0u7d22u7cfbu7edf
AppVersion=1.0
DefaultDirName={autopf}\u6863u6848u68c0u7d22u7cfbu7edf
DefaultGroupName=u6863u6848u68c0u7d22u7cfbu7edf
OutputDir=.
OutputBaseFilename=u6863u6848u68c0u7d22u7cfbu7edf_u5b89u88c5u7a0bu5e8f
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\u6863u6848u68c0u7d22u7cfbu7edf\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\u6863u6848u68c0u7d22u7cfbu7edf"; Filename: "{app}\u6863u6848u68c0u7d22u7cfbu7edf.exe"
Name: "{group}\u5378u8f7d"; Filename: "{uninstallexe}"
Name: "{commondesktop}\u6863u6848u68c0u7d22u7cfbu7edf"; Filename: "{app}\u6863u6848u68c0u7d22u7cfbu7edf.exe"

[Run]
Filename: "{app}\u6863u6848u68c0u7d22u7cfbu7edf.exe"; Description: "u7acbu5373u542fu52a8u7a0bu5e8f"; Flags: nowait postinstall skipifsilent
