@echo off
rem 20240412 重写所有代码，针对Win11家庭版系统更新到202404补丁打印共享出错。By WqlSoft
rem 20240412 测试Win11家庭版系统作为主机时，Win7 Win10子机可以直接共享到打印机，LPR共享也正常，反之也可以。
rem 20240412 测试Win10系统作为主机时，Win10子机可以直接共享到打印机，LPR共享也正常，反之也可以。
rem 20240412 测试Win7系统作为主机时，Win10 Win11子机可以直接共享到打印机，LPR共享也正常，反之也可以。
rem 20240412 只作文件夹共享不需要重启系统，LPR共享时要双方重启。
rem 20240412 测试未关闭Defender的情况下不被杀，可以正常运行。 
rem 20240412 几个系统反复还原测试，正常。
rem 20241120 修改不自动安装LPR打印共享功能，给出5秒安装提示。
rem 20241214 增加域判断，本工具未在{已加入域}的系统中测试过
rem 20241214 解决报错找不到网络名0x80070043-未测试是否有效

rem =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

title =_=Windows10.11家庭版打印机共享-WqlSoft=_=计算机名:%computername%=_=当前时间：%time%_=_=_=_=_=

echo 非常感谢WqlSoft大佬制作了这个工具！
echo.
echo 我是二虎电脑，曾经使用过很多打印机共享修复工具，发现这个工具是最好用的，基本解决了碰到的Windows10.11无法共享的问题。
echo 所以把这个好工具分享给你，在运行过程中可能安全软件会提示，需要选择允许!
echo.

echo.
pause
cls

echo =_=_=_=_=_=获取管理员身份权限=_=开始_=_=_=_=_=_=_=_=_==_=_=_=
rem 自动请求以管理员权限运行
reg query HKU\S-1-5-20>nul 2>nul || echo CreateObject^("Shell.Application"^).ShellExecute "%~f0", "%*", "", "runas", 1 > "%temp%\getadmin.vbs" && cscript //b "%temp%\getadmin.vbs" && exit /b & del "%temp%\getadmin.vbs" /f /q>nul 2>nul
@echo.

@echo.      -----**当前系统是管理员身份**-----
rem *****************************域判断*********************************************************
setlocal EnableDelayedExpansion
rem 获取计算机名及其所属的域/工作组名称
for /F "tokens=2 delims==" %%i in ('wmic computersystem get domain /value ^| findstr /i "Domain"') do (
    set "domain=%%i"
)
rem 移除可能存在的尾随空格或换行符
set "domain=!domain:~0,-1!"
rem 使用PowerShell检查是否加入域
for /f "delims=" %%a in ('powershell -NoProfile -Command "(Get-WmiObject Win32_ComputerSystem).PartOfDomain"') do (
    set "isDomainMember=%%a"
)
if /i "%isDomainMember%"=="True" (
    echo ==================================================
    echo 此计算机已加入域：%domain%
    echo ==================================================
    echo 本工具未在{已加入域}的系统中测试过，请关闭本窗口.
        choice /c yn /t 4 /d n /M "本工具未在{已加入域}的系统中测试过，请关闭本窗口.默认5秒后退出 (Y/N)"
if errorlevel 2 (
   rem echo 这里是按N键后执行内容
   exit
) else (
   rem echo 这里是按Y键后执行内容
    )

) else (
    echo 此计算机未加入域，工作组为：%domain%
)
endlocal
rem ******************************域判断****结束**************************************************

rem 启用Guest账户
net user guest /active:yes >nul 2>&1
net user guest "" >nul 2>&1

rem 先开启系统的网络发现和局域网文件共享防火墙权限
netsh advfirewall firewall set rule group="文件和打印机共享" new enable=yes >nul
netsh advfirewall firewall set rule group="网络发现" new enable=yes >nul
netsh firewall set service type = fileandprint mode = enable scope = subnet >nul
reg add "HKEY_LOCAL_MACHINE\SYSTEM\ControlSet001\Control\Lsa" /v "LimitBlankPasswordUse" /t REG_DWORD /d "00000000" /f >nul
reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Lsa" /v "LimitBlankPasswordUse" /t REG_DWORD /d "00000000" /f >nul
reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Lsa" /v forceguest /t REG_DWORD /d 0x1 /f
rem 解决Win10以上共享提示0X80004005错误  SMB 客户端允许不安全的来宾登录。
reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" /v AllowInsecureGuestAuth /t REG_DWORD /d 0x1 /f
reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" /f /v "AllowInsecureGuestAuth" /t REG_DWORD /d 1 >NUL 2>nul
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\LanmanWorkstation" /f /v "AllowInsecureGuestAuth" /t REG_DWORD /d 1 >NUL 2>nul
reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Lsa" /v restrictanonymoussam /t REG_DWORD /d 0x0 /f >nul 2>nul
reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Lsa\MSV1_0" /v LmCompatibilityLevel /t REG_DWORD /d 0x1 /f >nul 2>nul
reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Lsa" /v everyoneincludesanonymous /t REG_DWORD /d 0x1 /f >nul 2>nul
reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Lsa" /v NoLmHash /t REG_DWORD /d 0x0 /f >nul 2>nul

rem 解决报错找不到网络名0x80070043-未测试是否有效241214
reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\WebClient\Parameters" /v BasicAuthLevel /t REG_DWORD /d 2 /f >nul 2>nul

rem 网络访问 限制匿名访问命名管道和共享
reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\services\LanmanServer\Parameters" /v restrictnullsessaccess /t REG_DWORD /d 0x0 /f >nul 2>nul
rem 控制是否成为"浏览服务器"
reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\Browser\Parameters" /v MaintainServerList /t REG_SZ /d Auto /f
reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\Browser\Parameters" /v IsDomainMaster /t REG_SZ /d FALSE /f
rem 解决 windows 连接共享打印机 0x0000011b 错误
Reg add "HKLM\System\CurrentControlSet\Control\Print" /v "RpcAuthnLevelPrivacyEnabled" /t REG_DWORD /d "0" /f >nul 2>&1
rem 709修复
rem 禁用 RPC (Remote Procedure Call) 身份验证级别中的隐私保护
Reg add "HKLM\System\CurrentControlSet\Control\Print" /v "RpcAuthnLevelPrivacyEnabled" /t REG_DWORD /d "0" /f >nul 2>&1
rem 解决客户端弹出以管理员身份安装新的打印机驱动程序，值 0 允许非管理员在使用 Point and Print 时安装驱动程序
Reg add "HKLM\Software\Policies\Microsoft\Windows NT\Printers\PointAndPrint" /v "RestrictDriverInstallationToAdministrators" /t REG_DWORD /d "0" /f >nul 2>&1
rem “安装用于新连接的驱动程序时”：“显示警告和提升提示”。
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Printers\PointAndPrint" /v NoWarningNoElevationOnInstall /t REG_DWORD /d 0 /f > nul 2>&1
rem “更新现有连接的驱动程序时”：“显示警告和提升提示”。
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Printers\PointAndPrint" /v UpdatePromptSettings /t REG_DWORD /d 0 /f > nul 2>&1

rem 要通过注册表切换网络打印设置 启用 RPC 通信使用命名管道协议
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows NT\Printers\RPC" /v RpcUseNamedPipeProtocol /t REG_DWORD /d 1 /f
rem 要启用侦听传入连接
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows NT\Printers\RPC" /v RpcProtocols /t REG_DWORD /d 0x7 /f
rem 要强制执行 Kerberos 身份验证，
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows NT\Printers\RPC" /v ForceKerberosForRpc /t REG_DWORD /d 1 /f
rem 安装驱动时不搜索Windows Update更新
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\DriverSearching" /v DriverUpdateWizardWuSearchEnabled /t REG_DWORD /d 0 /f > nul 2>&1
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\DriverSearching" /v SearchOrderConfig /t REG_DWORD /d 0 /f > nul 2>&1
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\DriverSearching" /v DontSearchWindowsUpdate /t REG_DWORD /d 1 /f > nul 2>&1
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\DriverSearching" /v DontPromptForWindowsUpdate /t REG_DWORD /d 1 /f > nul 2>&1
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\DriverSearching" /v DriverUpdateWizardWuSearchEnabled /t REG_DWORD /d 0 /f > nul 2>&1
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\DriverSearching" /v SearchOrderConfig /t REG_DWORD /d 0 /f > nul 2>&1
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\DriverSearching" /v DontSearchWindowsUpdate /t REG_DWORD /d 1 /f > nul 2>&1
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\DriverSearching" /v DontPromptForWindowsUpdate /t REG_DWORD /d 1 /f > nul 2>&1
rem Microsoft 网络客户端：对通信进行数字签名 (始终)
reg add "HKLM\System\CurrentControlSet\Services\LanmanWorkstation\Parameters" /v RequireSecuritySignature /t REG_DWORD /d 0 /f 
reg add "HKLM\System\CurrentControlSet\Services\LanmanWorkstation\Parameters" /v EnableForcedLogoff /t REG_DWORD /d 0 /f


echo 正在配置防火墙...
netsh advfirewall firewall add rule name="LPR Port" dir=in action=allow protocol=TCP localport=515
netsh advfirewall firewall add rule name="LPD Port" dir=in action=allow protocol=TCP localport=721-731

rem 启用或关闭 Windows Defender 防火墙 (重启生效)
rem 专用网络设置
rem 关闭-启用 Windows Defender 防火墙
reg add "HKLM\SYSTEM\ControlSet001\Services\SharedAccess\Parameters\FirewallPolicy\StandardProfile" /v "EnableFirewall" /t REG_DWORD /d 0 /f
rem 关闭-阻止所有传入连接, 包括位于允许应用列表中的应用
reg add "HKLM\SYSTEM\ControlSet001\Services\SharedAccess\Parameters\FirewallPolicy\StandardProfile" /v "DoNotAllowExceptions" /t REG_DWORD /d 0 /f
rem 开启-Windows Defender 防火墙阻止新应用时通知我
reg add "HKLM\SYSTEM\ControlSet001\Services\SharedAccess\Parameters\FirewallPolicy\StandardProfile" /v "DisableNotifications" /t REG_DWORD /d 0 /f
rem 公用网络设置
reg add "HKLM\SYSTEM\ControlSet001\Services\SharedAccess\Parameters\FirewallPolicy\PublicProfile" /v "EnableFirewall" /t REG_DWORD /d 0 /f
reg add "HKLM\SYSTEM\ControlSet001\Services\SharedAccess\Parameters\FirewallPolicy\PublicProfile" /v "DoNotAllowExceptions" /t REG_DWORD /d 0 /f
reg add "HKLM\SYSTEM\ControlSet001\Services\SharedAccess\Parameters\FirewallPolicy\PublicProfile" /v "DisableNotifications" /t REG_DWORD /d 0 /f
rem 域网络设置
reg add "HKLM\SYSTEM\ControlSet001\Services\SharedAccess\Parameters\FirewallPolicy\DomainProfile" /v "EnableFirewall" /t REG_DWORD /d 0 /f
reg add "HKLM\SYSTEM\ControlSet001\Services\SharedAccess\Parameters\FirewallPolicy\DomainProfile" /v "DoNotAllowExceptions" /t REG_DWORD /d 0 /f
reg add "HKLM\SYSTEM\ControlSet001\Services\SharedAccess\Parameters\FirewallPolicy\DomainProfile" /v "DisableNotifications" /t REG_DWORD /d 0 /f

rem 设置为专用网络(0|公用网络,1|专用网络)Win10 以上为1，Win7为1
rem 启用延迟环境变量扩展功能
setlocal EnableDelayedExpansion
rem 定义要遍历的注册表键路径
set "keyPath=HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\NetworkList\Profiles"

rem 获取操作系统版本信息
for /f "tokens=4-5 delims=. " %%i in ('ver') do (
    set "osVersion=%%i.%%j"
)

for /f "delims=" %%A in ('reg query "%keyPath%" /s ^| findstr /i "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\NetworkList\\Profiles\\"') do (
    rem 提取当前子键名
    set "subKey=%%A"
    set "subKey=!subKey:HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\NetworkList\Profiles\=!"

    rem 根据操作系统版本设置相应键值
    if %osVersion% LEQ 6.1 (
        rem 系统为Windows 7或更低版本，设置键值为1
        reg add "!keyPath!\!subKey!" /v Category /t REG_DWORD /d 1 /f > nul 2>&1 && (
            rem echo 已将子键:!keyPath!\!subKey! 的 "Category" 值改为 1
            echo 已将所有网卡都修改成工作网络。
        ) || (
            echo 子键:!keyPath!\!subKey! 不存在 "Category" 值。
        )
    ) else (
        rem 系统为Windows 10或更高版本，设置键值为1
        reg add "!keyPath!\!subKey!" /v Category /t REG_DWORD /d 1 /f > nul 2>&1 && (
            rem echo 已将子键:!keyPath!\!subKey! 的 "Category" 值改为 1
            echo 已将所有网卡都修改成专用网络。
        ) || (
            echo 子键:!keyPath!\!subKey! 不存在 "Category" 值。
        )
    )
)
rem 设置开机不再提示设置网络
reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Network\NetworkLocationWizard" /v HideWizard /t REG_DWORD /d 1 /f > nul 2>&1

rem **********设置为专用网络结束*****************


@echo off
SetLocal EnableDelayedExpansion
rem net accounts /maxpwage:unlimited
rem net share "Video"="D:\Video" /grant:%UserName%,read /users:3 >nul 2>nul
reg add "HKLM\SYSTEM\ControlSet001\Control\Lsa" /f /v "ForceGuest" /t REG_DWORD /d 1 >nul
reg add "HKLM\SYSTEM\ControlSet001\Control\Lsa" /f /v "ForceGuest" /t REG_DWORD /d 1 >nul
reg add "HKLM\SYSTEM\ControlSet001\Control\Lsa" /f /v "LimitBlankPasswordUse" /t REG_DWORD /d 0x0 /f >nul 2>nul
rem 禁止IPC$空连接 1为禁用
reg add "HKLM\SYSTEM\ControlSet001\Control\Lsa" /f /v "RestrictAnonymousSAM" /t REG_DWORD /d 0x0 /f >nul 2>nul
reg add "HKLM\SYSTEM\ControlSet001\Control\Lsa" /f /v "RestrictAnonymous" /t REG_DWORD /d 0 >nul 2>nul
rem 将Everyone权限应用于匿名用户
reg add "HKLM\SYSTEM\ControlSet001\Control\Lsa" /f /v "EveryoneIncludesAnonymous" /t REG_DWORD /d 1
reg add "HKLM\SYSTEM\ControlSet001\Control\Lsa\MSV1_0" /f /v "NtlmMinClientSec" /t REG_DWORD /d 0 >nul
reg add "HKLM\SYSTEM\ControlSet001\Control\Lsa\MSV1_0" /f /v "NtlmMinServerSec" /t REG_DWORD /d 0 >nul
reg add "HKLM\SYSTEM\ControlSet001\Control\Lsa\MSV1_0" /f /v "RestrictReceivingNTLMTraffic" /t REG_DWORD /d 1
reg add "HKLM\SYSTEM\ControlSet001\Services\NetBT\Parameters" /f /v "TransportBindName" /t REG_SZ /d \Device\
reg add "HKLM\SYSTEM\ControlSet001\Services\NetBT\Parameters" /f /v "UseNewSmb" /t REG_DWORD /d 1 >nul
reg add "HKLM\SYSTEM\ControlSet001\Services\LanmanServer\Parameters" /f /v "RestrictNullSessAccess" /t REG_DWORD /d 1 >nul
reg query "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\services\Netlogon" /v Start|findstr "0x4" && sc config Netlogon start= demand
rem 取消 简单共享向导
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v "SharingWizardOn" /t REG_DWORD /d 0 /f

rem 限制IPC$的远程默认共享 禁止 $C $D
reg add "HKLM\SYSTEM\ControlSet001\Services\LanmanServer\Parameters" /f /v "AutoShareServer" /t REG_DWORD /d 0 >nul
rem 禁止默认的管理共享及磁盘分区共享 禁止 $Admin
reg add "HKLM\SYSTEM\ControlSet001\Services\LanmanServer\Parameters" /f /v "AutoShareWks" /t REG_DWORD /d 0 >nul
reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\services\LanmanServer\Parameters" /v AutoShareServer /t REG_DWORD /d 0 /f >nul
reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\services\LanmanServer\Parameters" /v AutoShareWks /t REG_DWORD /d 0 /f >nul
rem 网络访问: 限制对命名管道和共享的匿名访问
reg delete "HKLM\SYSTEM\ControlSet001\Services\LanmanServer\Parameters" /f /v "NullSessionPipes" >nul 2>nul
reg delete "HKLM\SYSTEM\ControlSet001\Services\LanmanServer\Parameters" /f /v "SMB1" >nul 2>nul
reg delete "HKLM\SYSTEM\ControlSet001\Services\LanmanServer\Parameters" /f /v "SMB2" >nul 2>nul
reg delete "HKLM\SYSTEM\ControlSet001\Services\NetBT\Parameters" /f /v "SMBDeviceEnabled" >nul 2>nul
rem 启动服务
for /f "delims=" %%a in ('reg query "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\services\NetBT\Parameters\Interfaces" /s /e /f "0x2"^|findstr "\Tcpip_"') do reg add "%%a" /v NetbiosOptions /t REG_DWORD /d 0x0 /f
reg query "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\services\NetBT\Parameters" /v EnableLMHOSTS|findstr "0x0" && reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\services\NetBT\Parameters" /v EnableLMHOSTS /t REG_DWORD /d 0x1 /f
rem 删除计划任务（Scheduled Tasks）加快网络访问速度
reg delete "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\RemoteComputer\NameSpace\{D6277990-4C6A-11CF-8D87-00AA0060F5BF}" /f >nul 2>nul

rem 清空“拒绝从网络访问此计算机”
(echo [Unicode]
echo Unicode=yes
echo [Version]
echo signature="$CHICAGO$"
echo Revision=1
echo [Privilege Rights]
echo sedenynetworklogonright =
echo senetworklogonright = Everyone,Administrators,Users,Power Users,Backup Operators,guest) >> "%TEMP%\zcl.inf"

secedit /configure /db "%TEMP%\zcl.sdb" /cfg "%TEMP%\zcl.inf" /log "%TEMP%\zcl.log" /quiet

del /q "%TEMP%\zcl.*"

rem 断开所有连接
net use * /del /y
rem 在局域网内不隐藏自己的计算机名
net config server /hidden:no
rem net share ipc$
gpupdate /force

echo 开启SMB1 支持
DISM /Online /Enable-Feature /FeatureName:SMB1Protocol /all /norestart

rem===============请在10秒内按Y键执行以下命令=============================
@echo off
ver | findstr "6." > nul && set os=win7
ver | findstr "10." > nul && set os=win10_or_win11

choice /c yn /t 4 /d n /M "是否启用LPD打印共享功能，默认5秒后放弃 (Y/N)"

if errorlevel 2 (
   rem echo 这里是按N键后执行内容
) else (
  
echo 开启LPD打印相关功能……


if "%os%"=="win7" (
    echo Windows 7 开启LPD打印相关功能……
    dism /online /enable-feature /featurename:"Printing-Foundation-Features" /norestart
    dism /online /enable-feature /featurename:"Printing-Foundation-LPDPrintService" /norestart
    dism /online /enable-feature /featurename:"Printing-Foundation-LPRPortMonitor" /norestart
    dism /online /enable-feature /featurename:"Printing-Foundation-InternetPrinting-Client" /norestart
    echo Windows 7 开启LPD打印相关功能……结束
) else if "%os%"=="win10_or_win11" (
    echo Windows 10 或 Windows 11 开启LPD打印相关功能……
    echo 开启SMB1 支持
    DISM /Online /Enable-Feature /FeatureName:SMB1Protocol /all /norestart
    dism /online /enable-feature /featurename:"Printing-Foundation-InternetPrinting-Client" /all /norestart
    dism /online /enable-feature /featurename:"Printing-Foundation-LPDPrintService" /all /norestart
    dism /online /enable-feature /featurename:"Printing-Foundation-LPRPortMonitor" /all /norestart
    echo Windows 11 开启LPD打印相关功能……结束
) else (
    echo 出错：未知系统！！
    sleep 5
)
)
    echo.
    echo.

echo ****************************正在启动相关系统服务*****稍等*******************************************
echo.

for %%a in (server Browser DHCP fdPHost lmhosts LanmanServer LanmanWorkstation NetBT SharedAccess SSDPSRV FDResPub WebClient) do (
        sc config "%%~a" start=auto >nul
        net start "%%~a" >nul 2>nul
        )
net stop spooler /yes > NUL
rem 删除打印任务
DEL C:\WINDOWS\SYSTEM32\SPOOL\PRINTERS\*.* /F /Q
net start spooler > NUL
net start LPDSVC >nul 2>nul
echo.
echo 当前计算机名: 【%computername%】

    ipconfig
    echo.
echo **************************************************************************************
@echo 【现在可直接共享目录了】【如要LPR方式共享打印机则先重启】，，拜拜，，
REM 打开设备和打印机
set "osVersion="
for /f "delims=" %%a in ('wmic os get Caption ^| findstr /i "Windows 11"') do set "osVersion=%%a"
if defined osVersion (
    start "" control /name Microsoft.DevicesAndPrinters
) else (
    start "" shell:::{A8A91A66-3A7D-4424-8D24-04E180695C7A}
)
echo.

choice /T 8 /D Y /M "完成!  重启后生效。By WqlSoft 2024.11.20 (Y/N)"
if errorlevel 2 (
    echo 你已放弃删除本脚本。
) else (
    del "%~f0"
    echo 删除自身.
)

exit /b
