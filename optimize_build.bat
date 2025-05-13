@echo off
echo === u6863u6848u68c0u7d22u7cfbu7edfu6253u5305u4f18u5316u5de5u5177 ===
echo u6b63u5728u51c6u5907u4f18u5316u6253u5305...

:: u521bu5efaUPXu76eeu5f55
if not exist tools\upx mkdir tools\upx

:: u68c0u67e5UPXu662fu5426u5df2u5b58u5728
if exist tools\upx\upx.exe (
    echo UPXu5df2u5b58u5728uff0cu8df3u8fc7u4e0bu8f7du6b65u9aa4
) else (
    echo u6b63u5728u4e0bu8f7dUPX...
    powershell -Command "(New-Object System.Net.WebClient).DownloadFile('https://github.com/upx/upx/releases/download/v4.2.1/upx-4.2.1-win64.zip', 'upx.zip')"
    
    echo u6b63u5728u89e3u538bUPX...
    powershell -Command "Expand-Archive -Path upx.zip -DestinationPath tools\upx_temp -Force"
    copy tools\upx_temp\upx-4.2.1-win64\upx.exe tools\upx\
    rmdir /s /q tools\upx_temp
    del upx.zip
    echo UPXu5df2u5b89u88c5u5b8cu6210
)

:: u6e05u7406u65e7u7684u6784u5efau6587u4ef6
echo u6e05u7406u65e7u7684u6784u5efau6587u4ef6...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

:: u4f7fu7528PyInstalleru6784u5efau53efu6267u884cu6587u4ef6uff0cu5e76u4f7fu7528UPXu538bu7f29
echo u6b63u5728u4f7fu7528PyInstalleru6784u5efau53efu6267u884cu6587u4ef6uff08u542fu7528UPXu538bu7f29uff09...
pyinstaller --name="u6863u6848u68c0u7d22u7cfbu7edf" --icon="resources/app.ico" --noconsole --add-data="resources;resources" --add-data="config;config" --clean --exclude-module=torch --exclude-module=huggingface_hub --exclude-module=matplotlib --exclude-module=scipy --exclude-module=PIL --exclude-module=pandas.tests --exclude-module=numpy.testing --exclude-module=numpy.distutils --exclude-module=sqlalchemy.testing --exclude-module=tkinter.test --exclude-module=unittest --exclude-module=pytest --upx-dir="tools/upx" --hidden-import=urllib3 --upx-exclude="*.dll" --upx-exclude="*.pyd" src/main.py

echo u6784u5efau5b8cu6210uff01
echo u8bf7u4f7fu7528Inno Setupu7f16u8bd1final_installer.issu6587u4ef6u521bu5efau5b89u88c5u7a0bu5e8f

pause
