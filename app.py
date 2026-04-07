#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NMADDER Web API - Render Compatible
"""

import os
import sys
import json
from datetime import datetime

# إصلاح Event Loop أولاً
import asyncio
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# Flask
from flask import Flask, jsonify, request

app = Flask(__name__)

# التحقق من المتغيرات
API_ID = os.environ.get('API_ID')
API_HASH = os.environ.get('API_HASH')

if not API_ID or not API_HASH:
    print("❌ Error: API_ID and API_HASH required!")
    sys.exit(1)

@app.route('/')
def home():
    return jsonify({
        "name": "NMADDER API",
        "version": "12.0.3-web",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/api/info')
def info():
    return jsonify({
        "api_id": str(API_ID)[:4] + "****",
        "api_hash": API_HASH[:8] + "****",
        "features": ["messaging", "scraping", "adding"]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Starting NMADDER API on port {port}")
    app.run(host='0.0.0.0', port=port)
