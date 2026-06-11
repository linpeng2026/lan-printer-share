@echo off
chcp 65001 >nul
echo ============================================
echo   打印机共享修复工具 - 打包脚本
echo ============================================
echo.
echo 正在安装 PyInstaller...
pip install pyinstaller -q

echo.
echo 正在打包...
pyinstaller PrinterShareFixer.spec --clean --noconfirm

echo.
echo ============================================
echo 打包完成！
echo EXE 文件位置: dist\打印机共享修复工具.exe
echo ============================================
pause
