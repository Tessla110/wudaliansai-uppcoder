#!/bin/sh
# Start wudaliansai on Uppcoder (Spark free plan).
# Uppcoder serves the app at <public-host>/app/ -> 127.0.0.1:8000.
# The app itself runs on 0.0.0.0:18765; rewrite_proxy.py listens on
# 8000, forwards to the app and rewrites the /live.m3u play links to
# https://<public-host>/app/play/<key>.
# Usage: ./run.sh   (run inside ~/app in the container Terminal)
set -e
cd "$(dirname "$0")"
if [ ! -x ./wudaliansai ]; then
  python3 fetch_wudaliansai.py
fi
if ! curl -fsS -o /dev/null --max-time 2 http://127.0.0.1:18765/health 2>/dev/null; then
  BIND=0.0.0.0:18765 setsid nohup ./wudaliansai >/home/uppcoder/log/wudaliansai.log 2>&1 < /dev/null &
  for i in $(seq 1 30); do
    curl -fsS -o /dev/null --max-time 2 http://127.0.0.1:18765/health 2>/dev/null && break
    sleep 2
  done
fi
if ! curl -fsS -o /dev/null --max-time 2 http://127.0.0.1:8000/health 2>/dev/null; then
  setsid nohup python3 rewrite_proxy.py >/home/uppcoder/log/rewrite_proxy.log 2>&1 < /dev/null &
  sleep 1
fi
curl -fsS -o /dev/null --max-time 10 http://127.0.0.1:8000/health
echo "wudaliansai is up: <public-host>/app/ and <public-host>/app/live.m3u"
