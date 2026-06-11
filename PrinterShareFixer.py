# -*- coding: utf-8 -*-
"""
Windows 10/11 打印机共享修复工具 - GUI版
原作者: WqlSoft  |  GUI改写: Python tkinter
描述: 一键修复 Windows 打印机共享问题，涵盖注册表、防火墙、服务、SMB、LPD等
"""

import os
import sys

# ============================================================
# PyInstaller 单文件 DLL 搜索路径修复（必须在其他 import 之前）
# 解决部分电脑因临时目录 DLL 找不到而无法启动的问题
# ============================================================
def _fix_dll_search_path():
    """将 PyInstaller 解压目录加入 DLL 搜索路径，确保 Windows 能找到所有依赖"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 解压目录
        base_dir = sys._MEIPASS  # noqa

        # 方法1: os.add_dll_directory (Python 3.8+, Win8+)
        try:
            os.add_dll_directory(base_dir)
            os.add_dll_directory(os.path.join(base_dir, 'DLLs'))
        except Exception:
            pass

        # 方法2: SetDllDirectoryW (Win7兼容)
        try:
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel32.SetDllDirectoryW(base_dir)
        except Exception:
            pass

        # 方法3: 追加 PATH 环境变量
        try:
            current_path = os.environ.get('PATH', '')
            if base_dir not in current_path:
                os.environ['PATH'] = base_dir + os.pathsep + current_path
        except Exception:
            pass

_fix_dll_search_path()

import ctypes
import subprocess
import threading
import time
import socket
import winreg
from datetime import datetime


# ============================================================
# 管理员权限提升
# ============================================================
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def run_as_admin():
    """重新以管理员权限启动自身"""
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join([f'"{arg}"' for arg in sys.argv]), None, 1
        )
        sys.exit(0)


# ============================================================
# 日志回调
# ============================================================
log_callback = None


def log(msg):
    """输出日志到GUI"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    text = f"[{timestamp}] {msg}"
    if log_callback:
        log_callback(text + "\n")
    print(text)


# ============================================================
# 核心修复功能
# ============================================================

def reg_set_dword(key_path, value_name, data):
    """设置注册表 DWORD 值"""
    try:
        # 解析根键
        root_map = {
            "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
            "HKLM": winreg.HKEY_LOCAL_MACHINE,
            "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
            "HKCU": winreg.HKEY_CURRENT_USER,
            "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
            "HKCR": winreg.HKEY_CLASSES_ROOT,
        }
        parts = key_path.split("\\", 1)
        root = root_map.get(parts[0].upper(), winreg.HKEY_LOCAL_MACHINE)
        sub_key = parts[1] if len(parts) > 1 else ""

        key = winreg.CreateKey(root, sub_key)
        winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, data)
        winreg.CloseKey(key)
        return True
    except Exception as e:
        log(f"  注册表设置失败 [{key_path}\\{value_name}]: {e}")
        return False


def reg_set_sz(key_path, value_name, data):
    """设置注册表 SZ 值"""
    try:
        root_map = {
            "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
            "HKLM": winreg.HKEY_LOCAL_MACHINE,
            "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
            "HKCU": winreg.HKEY_CURRENT_USER,
            "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
            "HKCR": winreg.HKEY_CLASSES_ROOT,
        }
        parts = key_path.split("\\", 1)
        root = root_map.get(parts[0].upper(), winreg.HKEY_LOCAL_MACHINE)
        sub_key = parts[1] if len(parts) > 1 else ""

        key = winreg.CreateKey(root, sub_key)
        winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, data)
        winreg.CloseKey(key)
        return True
    except Exception as e:
        log(f"  注册表设置失败 [{key_path}\\{value_name}]: {e}")
        return False


def reg_delete(key_path, value_name):
    """删除注册表值"""
    try:
        root_map = {
            "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
            "HKLM": winreg.HKEY_LOCAL_MACHINE,
            "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
            "HKCU": winreg.HKEY_CURRENT_USER,
            "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
            "HKCR": winreg.HKEY_CLASSES_ROOT,
        }
        parts = key_path.split("\\", 1)
        root = root_map.get(parts[0].upper(), winreg.HKEY_LOCAL_MACHINE)
        sub_key = parts[1] if len(parts) > 1 else ""

        key = winreg.OpenKey(root, sub_key, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, value_name)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return True  # already deleted
    except Exception as e:
        return False


def run_cmd(cmd, suppress_error=False):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            encoding="gbk", errors="replace"
        )
        if result.returncode != 0 and not suppress_error:
            log(f"  命令执行出错: {cmd[:60]}...")
        return result
    except Exception as e:
        log(f"  命令执行异常: {e}")
        return None


# ============================================================
# 各项修复功能
# ============================================================

def fix_guest_account():
    """启用 Guest 账户"""
    log("▶ 启用 Guest 账户...")
    run_cmd("net user guest /active:yes", suppress_error=True)
    run_cmd('net user guest ""', suppress_error=True)
    reg_set_dword("HKLM\\SYSTEM\\CurrentControlSet\\Control\\Lsa", "ForceGuest", 1)
    reg_set_dword("HKLM\\SYSTEM\\ControlSet001\\Control\\Lsa", "ForceGuest", 1)
    log("  Guest 账户已启用")


def fix_firewall_rules():
    """配置防火墙规则"""
    log("▶ 配置防火墙规则 (允许文件和打印机共享、网络发现)...")
    run_cmd('netsh advfirewall firewall set rule group="文件和打印机共享" new enable=yes', suppress_error=True)
    run_cmd('netsh advfirewall firewall set rule group="网络发现" new enable=yes', suppress_error=True)
    log("  防火墙规则已配置")


def fix_firewall_ports():
    """开放 LPR/LPD 端口"""
    log("▶ 开放 LPR/LPD 防火墙端口...")
    run_cmd('netsh advfirewall firewall add rule name="LPR Port" dir=in action=allow protocol=TCP localport=515', suppress_error=True)
    run_cmd('netsh advfirewall firewall add rule name="LPD Port" dir=in action=allow protocol=TCP localport=721-731', suppress_error=True)
    log("  LPR/LPD 端口已开放")


def fix_registry_security():
    """修复注册表安全相关设置"""
    log("▶ 配置注册表安全设置...")

    regs = [
        ("HKLM\\SYSTEM\\ControlSet001\\Control\\Lsa", "LimitBlankPasswordUse", 0),
        ("HKLM\\SYSTEM\\CurrentControlSet\\Control\\Lsa", "LimitBlankPasswordUse", 0),
        ("HKLM\\SYSTEM\\CurrentControlSet\\Control\\Lsa", "ForceGuest", 1),
        # 解决 Win10 以上共享提示 0X80004005 错误
        ("HKLM\\SYSTEM\\CurrentControlSet\\Services\\LanmanWorkstation\\Parameters", "AllowInsecureGuestAuth", 1),
        ("HKLM\\SYSTEM\\CurrentControlSet\\Services\\LanmanWorkstation\\Parameters", "AllowInsecureGuestAuth", 1),
        ("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\LanmanWorkstation", "AllowInsecureGuestAuth", 1),
        ("HKLM\\SYSTEM\\CurrentControlSet\\Control\\Lsa", "restrictanonymoussam", 0),
        ("HKLM\\SYSTEM\\CurrentControlSet\\Control\\Lsa\\MSV1_0", "LmCompatibilityLevel", 1),
        ("HKLM\\SYSTEM\\CurrentControlSet\\Control\\Lsa", "everyoneincludesanonymous", 1),
        ("HKLM\\SYSTEM\\CurrentControlSet\\Control\\Lsa", "NoLmHash", 0),
        # 解决部分环境下访问提示 0x80070043
        ("HKLM\\SYSTEM\\CurrentControlSet\\Services\\WebClient\\Parameters", "BasicAuthLevel", 2),
        ("HKLM\\SYSTEM\\CurrentControlSet\\Services\\LanmanServer\\Parameters", "restrictnullsessaccess", 0),
        # SMB 安全签名
        ("HKLM\\System\\CurrentControlSet\\Services\\LanmanWorkstation\\Parameters", "RequireSecuritySignature", 0),
        ("HKLM\\System\\CurrentControlSet\\Services\\LanmanWorkstation\\Parameters", "EnableForcedLogoff", 0),
        # Everyone 匿名访问
        ("HKLM\\SYSTEM\\ControlSet001\\Control\\Lsa", "EveryoneIncludesAnonymous", 1),
        ("HKLM\\SYSTEM\\ControlSet001\\Control\\Lsa", "RestrictAnonymousSAM", 0),
        ("HKLM\\SYSTEM\\ControlSet001\\Control\\Lsa", "RestrictAnonymous", 0),
        # NTLM
        ("HKLM\\SYSTEM\\ControlSet001\\Control\\Lsa\\MSV1_0", "NtlmMinClientSec", 0),
        ("HKLM\\SYSTEM\\ControlSet001\\Control\\Lsa\\MSV1_0", "NtlmMinServerSec", 0),
        ("HKLM\\SYSTEM\\ControlSet001\\Control\\Lsa\\MSV1_0", "RestrictReceivingNTLMTraffic", 1),
        # NetBT
        ("HKLM\\SYSTEM\\ControlSet001\\Services\\NetBT\\Parameters", "UseNewSmb", 1),
        # 共享向导
        ("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "SharingWizardOn", 0),
        # LMHOSTS
        ("HKLM\\SYSTEM\\CurrentControlSet\\Services\\NetBT\\Parameters", "EnableLMHOSTS", 1),
    ]

    for path, name, val in regs:
        reg_set_dword(path, name, val)

    # SZ 类型
    reg_set_sz("HKLM\\SYSTEM\\ControlSet001\\Services\\NetBT\\Parameters", "TransportBindName", "\\Device\\")

    log("  注册表安全设置完成")


def fix_print_registry():
    """修复打印机相关注册表"""
    log("▶ 配置打印机注册表（RPC / Point and Print / 驱动搜索）...")

    regs = [
        # 解决 0x0000011b 错误
        ("HKLM\\System\\CurrentControlSet\\Control\\Print", "RpcAuthnLevelPrivacyEnabled", 0),
        ("HKLM\\System\\CurrentControlSet\\Control\\Print", "RpcAuthnLevelPrivacyEnabled", 0),
        # Point and Print - 允许非管理员安装驱动
        ("HKLM\\Software\\Policies\\Microsoft\\Windows NT\\Printers\\PointAndPrint", "RestrictDriverInstallationToAdministrators", 0),
        ("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\Printers\\PointAndPrint", "NoWarningNoElevationOnInstall", 0),
        ("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\Printers\\PointAndPrint", "UpdatePromptSettings", 0),
        # RPC 打印机协议
        ("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\Printers\\RPC", "RpcUseNamedPipeProtocol", 1),
        ("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\Printers\\RPC", "RpcProtocols", 0x7),
        ("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\Printers\\RPC", "ForceKerberosForRpc", 1),
        # 驱动安装时不搜索 Windows Update
        ("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DriverSearching", "DriverUpdateWizardWuSearchEnabled", 0),
        ("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DriverSearching", "SearchOrderConfig", 0),
        ("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DriverSearching", "DontSearchWindowsUpdate", 1),
        ("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DriverSearching", "DontPromptForWindowsUpdate", 1),
        ("HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\DriverSearching", "DriverUpdateWizardWuSearchEnabled", 0),
        ("HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\DriverSearching", "SearchOrderConfig", 0),
        ("HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\DriverSearching", "DontSearchWindowsUpdate", 1),
        ("HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\DriverSearching", "DontPromptForWindowsUpdate", 1),
    ]

    for path, name, val in regs:
        reg_set_dword(path, name, val)

    log("  打印机注册表配置完成")


def fix_disable_defender_firewall():
    """关闭 Windows Defender 防火墙（可选，有些环境需要）"""
    log("▶ 关闭 Windows Defender 防火墙...")

    regs = [
        ("HKLM\\SYSTEM\\ControlSet001\\Services\\SharedAccess\\Parameters\\FirewallPolicy\\StandardProfile", "EnableFirewall", 0),
        ("HKLM\\SYSTEM\\ControlSet001\\Services\\SharedAccess\\Parameters\\FirewallPolicy\\StandardProfile", "DoNotAllowExceptions", 0),
        ("HKLM\\SYSTEM\\ControlSet001\\Services\\SharedAccess\\Parameters\\FirewallPolicy\\StandardProfile", "DisableNotifications", 0),
        ("HKLM\\SYSTEM\\ControlSet001\\Services\\SharedAccess\\Parameters\\FirewallPolicy\\PublicProfile", "EnableFirewall", 0),
        ("HKLM\\SYSTEM\\ControlSet001\\Services\\SharedAccess\\Parameters\\FirewallPolicy\\PublicProfile", "DoNotAllowExceptions", 0),
        ("HKLM\\SYSTEM\\ControlSet001\\Services\\SharedAccess\\Parameters\\FirewallPolicy\\PublicProfile", "DisableNotifications", 0),
        ("HKLM\\SYSTEM\\ControlSet001\\Services\\SharedAccess\\Parameters\\FirewallPolicy\\DomainProfile", "EnableFirewall", 0),
        ("HKLM\\SYSTEM\\ControlSet001\\Services\\SharedAccess\\Parameters\\FirewallPolicy\\DomainProfile", "DoNotAllowExceptions", 0),
        ("HKLM\\SYSTEM\\ControlSet001\\Services\\SharedAccess\\Parameters\\FirewallPolicy\\DomainProfile", "DisableNotifications", 0),
    ]

    for path, name, val in regs:
        reg_set_dword(path, name, val)

    log("  Windows Defender 防火墙已关闭")


def fix_network_to_private():
    """将网络设置为专用网络"""
    log("▶ 设置网络为专用网络...")

    profile_key = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\NetworkList\Profiles"
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, profile_key)
        i = 0
        while True:
            try:
                sub_key_name = winreg.EnumKey(key, i)
                reg_set_dword(f"HKLM\\{profile_key}\\{sub_key_name}", "Category", 1)
                i += 1
            except OSError:
                break
        winreg.CloseKey(key)
        log("  所有网络已设置为专用网络")
    except Exception as e:
        log(f"  设置专用网络失败: {e}")

    # 隐藏网络位置向导
    reg_set_dword("HKLM\\SYSTEM\\CurrentControlSet\\Control\\Network\\NetworkLocationWizard", "HideWizard", 1)


def fix_smb1():
    """启用 SMB1 协议支持"""
    log("▶ 启用 SMB1 协议支持...")
    run_cmd("DISM /Online /Enable-Feature /FeatureName:SMB1Protocol /all /norestart", suppress_error=True)
    log("  SMB1 协议已启用（可能需要重启）")


def fix_lpd_service():
    """安装 LPD 打印服务"""
    log("▶ 安装 LPD 打印服务...")

    # 检测系统版本
    result = subprocess.run("ver", shell=True, capture_output=True, text=True, encoding="gbk", errors="replace")
    ver_output = result.stdout.lower()

    if "6." in ver_output:
        log("  检测到 Windows 7，安装 LPD 组件...")
        cmds = [
            'dism /online /enable-feature /featurename:"Printing-Foundation-Features" /norestart',
            'dism /online /enable-feature /featurename:"Printing-Foundation-LPDPrintService" /norestart',
            'dism /online /enable-feature /featurename:"Printing-Foundation-LPRPortMonitor" /norestart',
            'dism /online /enable-feature /featurename:"Printing-Foundation-InternetPrinting-Client" /norestart',
        ]
    else:
        log("  检测到 Windows 10/11，安装 LPD 组件...")
        cmds = [
            'dism /online /enable-feature /featurename:"Printing-Foundation-Features" /norestart',
            'dism /online /enable-feature /featurename:"Printing-Foundation-LPDPrintService" /norestart',
            'dism /online /enable-feature /featurename:"Printing-Foundation-LPRPortMonitor" /norestart',
            'dism /online /enable-feature /featurename:"Printing-Foundation-InternetPrinting-Client" /norestart',
        ]

    for cmd in cmds:
        run_cmd(cmd, suppress_error=True)

    log("  LPD 打印服务安装完成")


def fix_services():
    """配置服务"""
    log("▶ 配置相关服务...")

    # 启动 Computer Browser 服务
    run_cmd("sc config Browser start= auto", suppress_error=True)
    run_cmd("sc start Browser", suppress_error=True)

    # 启动 FDResPub (Function Discovery Resource Publication)
    run_cmd("sc config FDResPub start= auto", suppress_error=True)
    run_cmd("sc start FDResPub", suppress_error=True)

    # 启动 SSDPSRV (SSDP Discovery)
    run_cmd("sc config SSDPSRV start= auto", suppress_error=True)
    run_cmd("sc start SSDPSRV", suppress_error=True)

    # 启动 upnphost (UPnP Device Host)
    run_cmd("sc config upnphost start= auto", suppress_error=True)
    run_cmd("sc start upnphost", suppress_error=True)

    # Netlogon
    run_cmd("sc config Netlogon start= demand", suppress_error=True)

    # 配置 LanmanServer Browser 参数
    reg_set_sz("HKLM\\SYSTEM\\CurrentControlSet\\Services\\Browser\\Parameters", "MaintainServerList", "Auto")
    reg_set_sz("HKLM\\SYSTEM\\CurrentControlSet\\Services\\Browser\\Parameters", "IsDomainMaster", "FALSE")

    # NetBIOS over TCP/IP - 设置所有网络接口
    try:
        key_path = r"SYSTEM\CurrentControlSet\Services\NetBT\Parameters\Interfaces"
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
        i = 0
        while True:
            try:
                sub_name = winreg.EnumKey(key, i)
                reg_set_dword(f"HKLM\\{key_path}\\{sub_name}", "NetbiosOptions", 0)
                i += 1
            except OSError:
                break
        winreg.CloseKey(key)
    except Exception:
        pass

    log("  服务配置完成")


def fix_network_rights():
    """修复网络访问权限"""
    log("▶ 修复网络访问权限...")

    # 创建安全模板文件
    temp_dir = os.environ.get("TEMP", "C:\\Windows\\Temp")
    inf_path = os.path.join(temp_dir, "psf_zcl.inf")
    sdb_path = os.path.join(temp_dir, "psf_zcl.sdb")
    log_path = os.path.join(temp_dir, "psf_zcl.log")

    inf_content = """[Unicode]
Unicode=yes
[Version]
signature="$CHICAGO$"
Revision=1
[Privilege Rights]
sedenynetworklogonright =
senetworklogonright = Everyone,Administrators,Users,Power Users,Backup Operators,guest
"""

    try:
        with open(inf_path, "w", encoding="utf-16") as f:
            f.write(inf_content)

        run_cmd(f'secedit /configure /db "{sdb_path}" /cfg "{inf_path}" /log "{log_path}" /quiet', suppress_error=True)

        # 清理临时文件
        for f in [inf_path, sdb_path, log_path]:
            try:
                os.remove(f)
            except Exception:
                pass
    except Exception as e:
        log(f"  网络权限修复失败: {e}")

    log("  网络访问权限已修复")


def fix_hidden_shares():
    """禁用隐藏管理共享"""
    log("▶ 禁用隐藏管理共享...")

    regs = [
        ("HKLM\\SYSTEM\\ControlSet001\\Services\\LanmanServer\\Parameters", "AutoShareServer", 0),
        ("HKLM\\SYSTEM\\ControlSet001\\Services\\LanmanServer\\Parameters", "AutoShareWks", 0),
        ("HKLM\\SYSTEM\\CurrentControlSet\\Services\\LanmanServer\\Parameters", "AutoShareServer", 0),
        ("HKLM\\SYSTEM\\CurrentControlSet\\Services\\LanmanServer\\Parameters", "AutoShareWks", 0),
    ]

    for path, name, val in regs:
        reg_set_dword(path, name, val)

    # 删除受限管道
    deletes = [
        ("HKLM\\SYSTEM\\ControlSet001\\Services\\LanmanServer\\Parameters", "NullSessionPipes"),
        ("HKLM\\SYSTEM\\ControlSet001\\Services\\LanmanServer\\Parameters", "SMB1"),
        ("HKLM\\SYSTEM\\ControlSet001\\Services\\LanmanServer\\Parameters", "SMB2"),
        ("HKLM\\SYSTEM\\ControlSet001\\Services\\NetBT\\Parameters", "SMBDeviceEnabled"),
        # 删除计划任务命名空间（提升网络访问速度）
        ("HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\RemoteComputer\\NameSpace", "{D6277990-4C6A-11CF-8D87-00AA0060F5BF}"),
    ]

    for path, name in deletes:
        reg_delete(path, name)

    # 断开所有网络连接
    run_cmd("net use * /del /y", suppress_error=True)
    # 在局域网中可见
    run_cmd("net config server /hidden:no", suppress_error=True)

    log("  隐藏管理共享已禁用")


def fix_gpupdate():
    """刷新组策略"""
    log("▶ 刷新组策略...")
    run_cmd("gpupdate /force", suppress_error=True)
    log("  组策略已刷新")


def fix_restart_spooler():
    """重启打印后台服务"""
    log("▶ 重启打印后台服务...")
    run_cmd("net stop spooler /y", suppress_error=True)
    time.sleep(2)
    run_cmd("net start spooler", suppress_error=True)
    log("  打印后台服务已重启")


# ============================================================
# 所有修复项定义
# ============================================================

ALL_FIXES = [
    ("启用 Guest 账户", fix_guest_account, "解决匿名访问和来宾共享问题"),
    ("配置防火墙规则", fix_firewall_rules, "允许文件和打印机共享、网络发现"),
    ("开放 LPR/LPD 端口", fix_firewall_ports, "开放 TCP 515 / 721-731 端口"),
    ("注册表安全设置", fix_registry_security, "SMB签名、NTLM、匿名访问等核心注册表"),
    ("打印机注册表配置", fix_print_registry, "RPC协议、Point and Print、驱动搜索"),
    ("关闭 Defender 防火墙", fix_disable_defender_firewall, "关闭所有配置文件的 Windows 防火墙"),
    ("设置网络为专用", fix_network_to_private, "所有网络接口改为专用网络"),
    ("启用 SMB1 协议", fix_smb1, "通过 DISM 启用 SMB 1.0 协议"),
    ("安装 LPD 打印服务", fix_lpd_service, "安装 LPD/LPR 打印服务组件"),
    ("配置系统服务", fix_services, "启动 Browser/SSDP/UPnP 等服务"),
    ("修复网络访问权限", fix_network_rights, "secedit 配置安全策略"),
    ("禁用隐藏共享", fix_hidden_shares, "禁用 C$/D$/Admin$ 等隐藏共享"),
    ("刷新组策略", fix_gpupdate, "gpupdate /force 更新组策略"),
    ("重启打印后台服务", fix_restart_spooler, "重启 Print Spooler 服务"),
]


# ============================================================
# GUI 界面 (tkinter)
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import tkinter.font as tkfont


class PrinterShareFixerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Windows 打印机共享修复工具 - v2.0 GUI")
        self.root.geometry("860x720")
        self.root.minsize(780, 640)

        # 设置图标（如果有的话）
        try:
            self.root.iconbitmap(default="printer.ico")
        except Exception:
            pass

        # 颜色方案 - 现代扁平风格
        self.colors = {
            "bg": "#f0f2f5",
            "card": "#ffffff",
            "primary": "#1677ff",
            "primary_hover": "#4096ff",
            "success": "#52c41a",
            "warning": "#fa8c16",
            "danger": "#ff4d4f",
            "text": "#1a1a1a",
            "text_secondary": "#666666",
            "border": "#e8e8e8",
            "log_bg": "#1e1e2e",
            "log_text": "#cdd6f4",
            "log_info": "#89b4fa",
        }

        self.root.configure(bg=self.colors["bg"])
        self.check_vars = {}
        self.is_running = False

        self.setup_ui()

        # 全局日志回调
        global log_callback
        log_callback = self.append_log

        # 启动后打印系统信息
        self.log_system_info()

    def log_system_info(self):
        hostname = socket.gethostname()
        log(f"计算机名: {hostname}")
        log(f"操作系统: {self.get_os_version()}")
        log("工具已就绪，请选择要修复的项目，然后点击「开始修复」")

    def get_os_version(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
            name = winreg.QueryValueEx(key, "ProductName")[0]
            winreg.CloseKey(key)
            return name
        except Exception:
            return "Unknown"

    def setup_ui(self):
        # ========== 顶部标题栏 ==========
        header = tk.Frame(self.root, bg=self.colors["primary"], height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_frame = tk.Frame(header, bg=self.colors["primary"])
        title_frame.pack(expand=True)

        title_label = tk.Label(
            title_frame,
            text="🖨  Windows 打印机共享修复工具",
            font=("Microsoft YaHei UI", 22, "bold"),
            fg="white",
            bg=self.colors["primary"],
        )
        title_label.pack(pady=(10, 0))

        hostname_label = tk.Label(
            title_frame,
            text=f"计算机: {socket.gethostname()}  |  by WqlSoft (GUI版)",
            font=("Microsoft YaHei UI", 12),
            fg="#d4d4d4",
            bg=self.colors["primary"],
        )
        hostname_label.pack(pady=(0, 10))

        # ========== 主内容区域 ==========
        main_container = tk.Frame(self.root, bg=self.colors["bg"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # --- 左侧：修复选项卡片 ---
        left_frame = tk.Frame(main_container, bg=self.colors["bg"])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        card = tk.Frame(left_frame, bg=self.colors["card"], highlightbackground=self.colors["border"],
                        highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True)

        # 卡片标题
        card_header = tk.Frame(card, bg=self.colors["card"])
        card_header.pack(fill=tk.X, padx=16, pady=(14, 6))

        tk.Label(
            card_header, text="修复项目", font=("Microsoft YaHei UI", 16, "bold"),
            fg=self.colors["text"], bg=self.colors["card"]
        ).pack(side=tk.LEFT)

        # 全选 / 取消
        btn_frame = tk.Frame(card_header, bg=self.colors["card"])
        btn_frame.pack(side=tk.RIGHT)

        select_all_btn = tk.Label(
            btn_frame, text="全选", font=("Microsoft YaHei UI", 12),
            fg=self.colors["primary"], bg=self.colors["card"], cursor="hand2"
        )
        select_all_btn.pack(side=tk.LEFT, padx=(0, 8))
        select_all_btn.bind("<Button-1>", lambda e: self.select_all())

        deselect_btn = tk.Label(
            btn_frame, text="取消", font=("Microsoft YaHei UI", 12),
            fg=self.colors["text_secondary"], bg=self.colors["card"], cursor="hand2"
        )
        deselect_btn.pack(side=tk.LEFT)
        deselect_btn.bind("<Button-1>", lambda e: self.deselect_all())

        # 滚动区域
        canvas = tk.Canvas(card, bg=self.colors["card"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(card, orient=tk.VERTICAL, command=canvas.yview)
        self.check_frame = tk.Frame(canvas, bg=self.colors["card"])

        self.check_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.check_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=(0, 8))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 4), pady=(0, 8))

        # 鼠标滚轮绑定
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", on_mousewheel)

        # 创建复选框
        for i, (name, func, desc) in enumerate(ALL_FIXES):
            var = tk.BooleanVar(value=True)
            self.check_vars[name] = var

            item_frame = tk.Frame(self.check_frame, bg=self.colors["card"])
            item_frame.pack(fill=tk.X, padx=12, pady=2)

            cb = tk.Checkbutton(
                item_frame, text="", variable=var,
                bg=self.colors["card"], activebackground=self.colors["card"],
                highlightthickness=0,
            )
            cb.pack(side=tk.LEFT)

            label_frame = tk.Frame(item_frame, bg=self.colors["card"])
            label_frame.pack(side=tk.LEFT, fill=tk.X)

            tk.Label(
                label_frame, text=name,
                font=("Microsoft YaHei UI", 12, "bold"),
                fg=self.colors["text"], bg=self.colors["card"],
                anchor=tk.W,
            ).pack(anchor=tk.W)

            tk.Label(
                label_frame, text=desc,
                font=("Microsoft YaHei UI", 13),
                fg=self.colors["text_secondary"], bg=self.colors["card"],
                anchor=tk.W,
            ).pack(anchor=tk.W)

        # --- 右侧：操作按钮和日志 ---
        right_frame = tk.Frame(main_container, bg=self.colors["bg"])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(12, 0))

        # 按钮卡片
        btn_card = tk.Frame(right_frame, bg=self.colors["card"], highlightbackground=self.colors["border"],
                            highlightthickness=1)
        btn_card.pack(fill=tk.X, pady=(0, 12))

        btn_inner = tk.Frame(btn_card, bg=self.colors["card"])
        btn_inner.pack(padx=16, pady=14)

        # 一键修复按钮
        self.fix_all_btn = tk.Button(
            btn_inner, text="一键修复全部",
            font=("Microsoft YaHei UI", 15, "bold"),
            bg=self.colors["primary"], fg="white",
            activebackground=self.colors["primary_hover"],
            activeforeground="white",
            relief=tk.FLAT, cursor="hand2",
            height=2,
            command=self.start_fix_all,
        )
        self.fix_all_btn.pack(fill=tk.X, pady=(0, 8))

        # 修复选中按钮
        self.fix_selected_btn = tk.Button(
            btn_inner, text="修复选中项目",
            font=("Microsoft YaHei UI", 11),
            bg=self.colors["success"], fg="white",
            activebackground="#73d13d",
            activeforeground="white",
            relief=tk.FLAT, cursor="hand2",
            height=2,
            command=self.start_fix_selected,
        )
        self.fix_selected_btn.pack(fill=tk.X, pady=(0, 8))

        # 仅重启后台服务
        self.restart_btn = tk.Button(
            btn_inner, text="仅重启打印后台服务",
            font=("Microsoft YaHei UI", 12),
            bg=self.colors["warning"], fg="white",
            activebackground="#ffc069",
            activeforeground="white",
            relief=tk.FLAT, cursor="hand2",
            height=1,
            command=self.restart_spooler_only,
        )
        self.restart_btn.pack(fill=tk.X, pady=(0, 4))

        # 进度条
        self.progress = ttk.Progressbar(
            right_frame, mode="determinate", style="TProgressbar"
        )
        self.progress.pack(fill=tk.X, pady=(0, 8))

        # 状态标签
        self.status_label = tk.Label(
            right_frame,
            text="就绪 - 等待操作",
            font=("Microsoft YaHei UI", 11),
            fg=self.colors["text_secondary"], bg=self.colors["bg"],
            anchor=tk.W,
        )
        self.status_label.pack(fill=tk.X, pady=(0, 8))

        # 日志区域
        log_label_frame = tk.Frame(right_frame, bg=self.colors["bg"])
        log_label_frame.pack(fill=tk.X)
        tk.Label(
            log_label_frame, text="执行日志",
            font=("Microsoft YaHei UI", 12, "bold"),
            fg=self.colors["text"], bg=self.colors["bg"],
        ).pack(side=tk.LEFT)
        self.clear_log_btn = tk.Label(
            log_label_frame, text="清空", font=("Microsoft YaHei UI", 11),
            fg=self.colors["primary"], bg=self.colors["bg"], cursor="hand2"
        )
        self.clear_log_btn.pack(side=tk.RIGHT)
        self.clear_log_btn.bind("<Button-1>", lambda e: self.clear_log())

        self.log_text = scrolledtext.ScrolledText(
            right_frame,
            font=("Consolas", 12),
            bg=self.colors["log_bg"],
            fg=self.colors["log_text"],
            insertbackground="white",
            relief=tk.FLAT,
            wrap=tk.WORD,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        # 底部版权
        footer = tk.Label(
            self.root,
            text="WqlSoft © 2024  |  GUI版 - Python tkinter  |  请以管理员身份运行",
            font=("Microsoft YaHei UI", 10),
            fg=self.colors["text_secondary"], bg=self.colors["bg"],
        )
        footer.pack(side=tk.BOTTOM, pady=(4, 8))

    def append_log(self, text):
        """添加日志（线程安全）"""
        self.root.after(0, self._append_log_impl, text)

    def _append_log_impl(self, text):
        self.log_text.insert(tk.END, text)
        self.log_text.see(tk.END)

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)

    def select_all(self):
        for var in self.check_vars.values():
            var.set(True)

    def deselect_all(self):
        for var in self.check_vars.values():
            var.set(False)

    def set_ui_state(self, running):
        self.is_running = running
        state = tk.DISABLED if running else tk.NORMAL

        # 动态改变按钮状态
        if running:
            self.fix_all_btn.config(state=state, text="修复中...", bg="#8c8c8c")
            self.fix_selected_btn.config(state=state, text="修复中...", bg="#8c8c8c")
            self.restart_btn.config(state=state)
        else:
            self.fix_all_btn.config(state=state, text="一键修复全部", bg=self.colors["primary"])
            self.fix_selected_btn.config(state=state, text="修复选中项目", bg=self.colors["success"])
            self.restart_btn.config(state=state)

    def update_progress(self, value):
        self.root.after(0, self._update_progress_impl, value)

    def _update_progress_impl(self, value):
        self.progress["value"] = value

    def update_status(self, text):
        self.root.after(0, self._update_status_impl, text)

    def _update_status_impl(self, text):
        self.status_label.config(text=text)

    def restart_spooler_only(self):
        if self.is_running:
            return
        self.set_ui_state(True)
        self.update_status("正在重启打印后台服务...")
        thread = threading.Thread(target=self._run_restart_spooler, daemon=True)
        thread.start()

    def _run_restart_spooler(self):
        try:
            fix_restart_spooler()
            self.update_status("打印后台服务已重启 - 完成")
            messagebox.showinfo("完成", "打印后台服务已重启！")
        except Exception as e:
            log(f"错误: {e}")
            self.update_status("操作失败")
            messagebox.showerror("错误", str(e))
        finally:
            self.set_ui_state(False)

    def start_fix_all(self):
        if self.is_running:
            return
        self.set_ui_state(True)
        self.update_status("正在执行一键修复...")
        self.progress["value"] = 0

        thread = threading.Thread(target=self._run_fixes, args=(list(range(len(ALL_FIXES))), "一键修复"))
        thread.daemon = True
        thread.start()

    def start_fix_selected(self):
        if self.is_running:
            return

        selected = []
        for i, (name, func, desc) in enumerate(ALL_FIXES):
            if self.check_vars[name].get():
                selected.append(i)

        if not selected:
            messagebox.showwarning("提示", "请至少选择一个修复项目！")
            return

        self.set_ui_state(True)
        self.update_status("正在修复选中项目...")
        self.progress["value"] = 0

        thread = threading.Thread(target=self._run_fixes, args=(selected, "选中修复"))
        thread.daemon = True
        thread.start()

    def _run_fixes(self, indices, mode_name):
        """在后台线程中运行修复"""
        total = len(indices)
        try:
            log("=" * 50)
            log(f"开始执行【{mode_name}】- 共 {total} 项")
            log("=" * 50)

            for idx, i in enumerate(indices):
                name, func, desc = ALL_FIXES[i]
                log("")
                try:
                    func()
                    self.update_status(f"[{idx + 1}/{total}] {name} - 已完成")
                except Exception as e:
                    log(f"  !! {name} 执行失败: {e}")
                    self.update_status(f"[{idx + 1}/{total}] {name} - 失败")

                self.update_progress(int((idx + 1) / total * 100))

            log("")
            log("=" * 50)
            log(f"【{mode_name}】全部完成！")
            self.update_status("所有修复已完成")
            self.update_progress(100)

            self.root.after(0, lambda: messagebox.showinfo(
                "完成",
                f"修复完成！共执行 {total} 项。\n"
                "部分更改可能需要重启计算机才能生效。\n\n"
                "建议重启计算机后测试打印机共享。"
            ))

        except Exception as e:
            log(f"严重错误: {e}")
            self.update_status("修复过程中发生严重错误")
            self.root.after(0, lambda: messagebox.showerror("错误", f"修复失败: {e}"))
        finally:
            self.set_ui_state(False)


# ============================================================
# 主入口
# ============================================================

def main():
    # 检查管理员权限
    if not is_admin():
        ret = messagebox.askyesno(
            "需要管理员权限",
            "此工具需要以管理员身份运行才能修改系统设置。\n\n"
            "是否以管理员权限重新启动？\n"
            "(选择「否」将退出程序)",
        )
        if ret:
            run_as_admin()
        else:
            sys.exit(0)
        return

    root = tk.Tk()

    # 设置 DPI 感知
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = PrinterShareFixerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
