#!/usr/bin/env python3
"""Vercel 入口 — 直接复用 app.py 的 Flask app"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app  # noqa: F401  Vercel 需要名为 app 的 WSGI callable
