# wudaliansai-uppcoder

Deploy `iptvtop/wudaliansai` (a tiny Rust live-match playlist proxy) on
[Uppcoder](https://portal.uppcoder.com) on the free Spark plan.

## What actually runs on Uppcoder

Uppcoder has no "deploy a Docker image" option: a Stack is a dev
container per framework component, and you connect a Git repository to
it. It does not build the Dockerfile, and it does not start your app
for you. So this repo carries everything needed to run the binary
inside the container:

| file | purpose |
| --- | --- |
| `Dockerfile` | Run the image as a container anywhere else (Docker, Fly.io, ...). `BIND` defaults to `0.0.0.0:18765`, or set `$PORT`. |
| `fetch_wudaliansai.py` | Pulls the amd64 image from Docker Hub and installs `/wudaliansai` here. No Docker needed. |
| `rewrite_proxy.py` | Listens on 8000, forwards to the app on 18765 and rewrites the `/live.m3u` play links to `https://<public-host>/app/play/<key>`. |
| `run.sh` | Starts the app + proxy (used after a container restart). |

Uppcoder serves the app at `<public-host>/app/`, proxied to
`127.0.0.1:8000` inside the container. The binary builds absolute
play URLs from the request Host header with its built-in default
port 18765 and no `/app/` prefix, so without `rewrite_proxy.py` the
links in the playlist would be dead. The proxy fixes them.

## URLs (live deployment)

- App: https://dhqhpz8i-rust-wudaliansai.apps-2.websson.cloud/app/
- Playlist: https://dhqhpz8i-rust-wudaliansai.apps-2.websson.cloud/app/live.m3u

The playlist is an M3U file (today's football/basketball/esports
matches with stream links). Play keys rotate when the app refreshes
its list (about once a minute), so fetch the playlist and play
promptly. `/play/<key>` redirects (302) to the stream's CDN m3u8.

## Restarting after a container restart

In the container Terminal:

```sh
cd ~/app
./run.sh
```

The processes run detached (`setsid` + `nohup`); logs are in
`~/log/wudaliansai.log` and `~/log/rewrite_proxy.log`. The Stack is
on the free Spark plan: 1 Stack, 2 GB RAM, 500 CPU-seconds/day; the
app idles at ~0.2 GB RAM and a few CPU-seconds per day.
