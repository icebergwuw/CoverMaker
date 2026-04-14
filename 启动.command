#!/bin/bash
cd "$(dirname "$0")"
export TAVILY_API_KEY="TAVILY_KEY_REMOVED"

# 已经在跑了就直接开浏览器
if lsof -ti:5299 > /dev/null 2>&1; then
    open "http://127.0.0.1:5299"
    exit 0
fi

/usr/bin/python3 app.py &
sleep 2
open "http://127.0.0.1:5299"
wait
