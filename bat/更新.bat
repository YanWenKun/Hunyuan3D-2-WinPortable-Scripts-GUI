@echo off
setlocal enabledelayedexpansion
chcp 65001

:: --- 1. 环境设置与检查 ---
:: 将内嵌的 Git 和 Python 添加到临时 PATH
set "PATH=%PATH%;%~dp0\MinGit\cmd;%~dp0\python_standalone\Scripts"

:: 检查 Git 是否可用
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo Error: 未找到 'git' 命令。请确保已安装 Git 并将其添加到 PATH 环境变量中。
    echo 下载地址: https://git-scm.com/downloads/win
    goto :error
)

:: --- 2. 批量更新 Git 仓库 ---
:: 定义所有需要更新的目录列表
set "repo_list=Hunyuan3D-2 Hunyuan3D-2-vanilla Hunyuan3D-2.1 WinScripts-GUI"

echo ===============================================
echo            开始更新所有 Git 仓库
echo ===============================================
echo.

:: 循环处理列表中的每一个目录
for %%G in (%repo_list%) do (
    echo --- 正在处理: %%G ---
    if not exist "%%G" (
        echo [警告] 目录 "%%G" 不存在，已跳过。
    ) else (
        pushd "%%G" && (
            echo 正在执行 git reset --hard...
            git reset --hard >nul && (
                echo 正在执行 git pull...
                git pull
            ) || (
                echo [错误] 'git reset --hard' 失败。
            )
            popd
        ) || (
            echo [错误] 无法进入目录 "%%G"。
        )
    )
    echo.
)

:: --- 3. 执行特定仓库的后续操作 ---
set "gui_dir=WinScripts-GUI"
if exist "%gui_dir%\bat\init.bat" (
    echo --- 正在启动 %gui_dir% 的初始化脚本... ---
    start "GUI Initializer" /d "%gui_dir%\bat" init.bat
    echo.
    echo 脚本已在新窗口中启动，你可以安全地关闭此窗口。
) else (
    echo [警告] 未找到 "%gui_dir%\bat\init.bat"，无法启动。
)

goto :end

:error
echo.
echo !!! 脚本执行过程中发生错误，已中止。 !!!

:end
echo.
endlocal
pause
