@echo off
echo 正在测试当前环境...
python test_imports.py

echo.
echo 准备卸载不需要的包...
pause

:: 卸载大型包
pip uninstall -y torch torchvision torchaudio transformers datasets scikit-learn scipy pyarrow accelerate

:: 重新测试导入
echo.
echo 重新测试导入...
python test_imports.py

echo.
echo 测试完成！
pause
