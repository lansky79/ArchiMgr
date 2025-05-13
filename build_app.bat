@echo off
echo === u6863u6848u68c0u7d22u7cfbu7edfu6253u5305u5de5u5177 ===
echo u6b63u5728u6784u5efau53efu6267u884cu6587u4ef6...

:: u6e05u7406u65e7u7684u6784u5efau6587u4ef6
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

:: u6784u5efau53efu6267u884cu6587u4ef6
pyinstaller --name="u6863u6848u68c0u7d22u7cfbu7edf" --icon="resources/app.ico" --noconsole --add-data="resources;resources" --add-data="config;config" --clean src/main.py

echo u6784u5efau5b8cu6210!
echo u8bf7u4f7fu7528Inno Setupu624bu52a8u7f16u8bd1installer.issu6587u4ef6u521bu5efau5b89u88c5u7a0bu5e8f

pause
