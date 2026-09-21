#!/bin/bash
# StartTestFool Installer - Qusoor
set -e

echo "[*] Downloading Osint.py from GitHub..."
mkdir -p ~/.local/bin
curl -fsSL https://raw.githubusercontent.com/Qsor132/UbuntuOsint/main/Osint.py -o ~/.local/bin/Osint.py
chmod +x ~/.local/bin/Osint.py

echo "[*] Creating StartTestFool launcher..."
cat > ~/.local/bin/StartTestFool << 'EOF'
#!/bin/bash
exec python3 ~/.local/bin/Osint.py "$@"
EOF
chmod +x ~/.local/bin/StartTestFool

# ضمان أن ~/.local/bin داخل PATH
if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    export PATH="$HOME/.local/bin:$PATH"
fi

echo ""
echo "=========================================="
echo "[+] Done! Type: StartTestFool"
echo "=========================================="
