import subprocess
import time
import os
import sys

zapret_process = None
proxy_process = None


# ================= PATH FIX (для exe) =================
def get_path(rel_path):
    if hasattr(sys, '_MEIPASS'):
        base = sys._MEIPASS
    else:
        base = os.path.abspath(".")
    return os.path.join(base, rel_path)


# ================= ZAPRET =================
def start_zapret():
    global zapret_process

    if zapret_process is None:
        try:
            zapret_path = get_path("zapret/start.bat")

            print("Запускаю:", zapret_path)

            zapret_process = subprocess.Popen(
                ["cmd", "/c", zapret_path],
                cwd=get_path("zapret")  # 👈 КРИТИЧЕСКИ ВАЖНО
            )

            time.sleep(3)

        except Exception as e:
            print("Zapret error:", e)


def stop_zapret():
    global zapret_process

    if zapret_process:
        zapret_process.terminate()
        zapret_process = None

    # убиваем процессы zapret
    os.system("taskkill /f /im winws.exe >nul 2>&1")
    os.system("taskkill /f /im goodbyedpi.exe >nul 2>&1")
    os.system("taskkill /f /im zapret.exe >nul 2>&1")


# ================= PROXY =================
def start_proxy():
    global proxy_process

    if proxy_process is None:
        try:
            proxy_process = subprocess.Popen(
                [get_path("proxy.exe")],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except Exception as e:
            print("Proxy error:", e)


def stop_proxy():
    global proxy_process

    if proxy_process:
        proxy_process.terminate()
        proxy_process = None

    os.system("taskkill /f /im proxy.exe >nul 2>&1")


# ================= WARP =================
def start_warp():
    try:
        # 🔧 фикс зависаний демона
        subprocess.run("net stop CloudflareWARP", shell=True)
        time.sleep(2)
        subprocess.run("net start CloudflareWARP", shell=True)
        time.sleep(3)

        # статус
        try:
            status = subprocess.check_output(
                "warp-cli status", shell=True
            ).decode().lower()
        except:
            status = ""

        # если уже подключен
        if "connected" in status and "disconnected" not in status:
            return

        # если нет регистрации
        if "registration missing" in status or "unable" in status:
            print("🔧 Creating registration...")
            subprocess.run("warp-cli registration delete", shell=True)
            time.sleep(1)
            subprocess.run("warp-cli registration new", shell=True)
            time.sleep(2)

        subprocess.run("warp-cli connect", shell=True)

    except Exception as e:
        print("WARP error:", e)


def stop_warp():
    try:
        subprocess.run("warp-cli disconnect", shell=True)
    except Exception as e:
        print("Stop WARP error:", e)


# ================= CHECK =================
def warp_installed():
    try:
        subprocess.check_output("warp-cli --version", shell=True)
        return True
    except:
        return False