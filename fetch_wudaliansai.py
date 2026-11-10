"""Fetch the wudaliansai binary from Docker Hub and install it here.

Uppcoder does not build Dockerfiles, so on Uppcoder we run the binary
directly: this script pulls the amd64 image iptvtop/wudaliansai from
the public Docker Hub registry (no login needed), extracts
/wudaliansai from its layers and installs it next to this script.
Only the Python standard library is used.
"""
import json
import os
import shutil
import stat
import tarfile
import tempfile
import urllib.request

REPO = "iptvtop/wudaliansai"
HERE = os.path.dirname(os.path.abspath(__file__))


def get(url, token=None, accept=None):
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", "Bearer " + token)
    if accept:
        req.add_header("Accept", accept)
    return urllib.request.urlopen(req, timeout=120)


def main():
    token = json.load(get(
        "https://auth.docker.io/token?service=registry.docker.io"
        "&scope=repository:%s:pull" % REPO))["token"]
    index = json.load(get(
        "https://registry-1.docker.io/v2/%s/manifests/latest" % REPO,
        token, "application/vnd.oci.image.index.v1+json"))
    amd64 = [m for m in index["manifests"]
             if m["platform"]["architecture"] == "amd64"][0]
    manifest = json.load(get(
        "https://registry-1.docker.io/v2/%s/manifests/%s"
        % (REPO, amd64["digest"]),
        token, "application/vnd.oci.image.manifest.v1+json"))
    tmp = tempfile.mkdtemp(prefix="wudaliansai-")
    try:
        for i, layer in enumerate(manifest["layers"]):
            path = os.path.join(tmp, "layer%d.tar.gz" % i)
            with get("https://registry-1.docker.io/v2/%s/blobs/%s"
                     % (REPO, layer["digest"]), token) as resp, \
                    open(path, "wb") as f:
                f.write(resp.read())
            with tarfile.open(path) as tf:
                tf.extractall(os.path.join(tmp, "rootfs"))
        src = os.path.join(tmp, "rootfs", "wudaliansai")
        dst = os.path.join(HERE, "wudaliansai")
        shutil.copyfile(src, dst)
        os.chmod(dst, os.stat(dst).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print("installed %s (%d bytes)" % (dst, os.path.getsize(dst)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
