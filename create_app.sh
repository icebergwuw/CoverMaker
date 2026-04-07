#!/bin/bash
# 创建 Auto Publish.app 放到桌面

APP_PATH="$HOME/Desktop/Auto Publish.app"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$APP_PATH/Contents/MacOS"
mkdir -p "$APP_PATH/Contents/Resources"

# 主执行文件
cat > "$APP_PATH/Contents/MacOS/run" << EOF
#!/bin/bash
export TAVILY_API_KEY="TAVILY_KEY_REMOVED"
export PATH="/usr/local/bin:/usr/bin:/bin:/Users/iceberg/.nvm/versions/node/v24.13.1/bin:\$PATH"

cd "$SCRIPT_DIR"

# 检查端口是否已占用（已经在跑了）
if lsof -ti:5299 > /dev/null 2>&1; then
    open "http://127.0.0.1:5299/auto-publish"
    exit 0
fi

# 启动服务
python3 app.py &
PID=\$!

# 等服务起来再开浏览器
sleep 2
open "http://127.0.0.1:5299/auto-publish"

wait \$PID
EOF

chmod +x "$APP_PATH/Contents/MacOS/run"

# Info.plist
cat > "$APP_PATH/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>run</string>
    <key>CFBundleIdentifier</key>
    <string>com.pdfagile.autopublish</string>
    <key>CFBundleName</key>
    <string>Auto Publish</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>LSUIElement</key>
    <false/>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

echo "✅ 已创建：$APP_PATH"
echo "   直接双击桌面上的 Auto Publish 图标即可启动"
