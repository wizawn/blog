#!/usr/bin/env python3
"""Google AI iOS 双通道 SKU 改写本地网关 (适配 Clash Mi / FlClash / Clash Verge / Karing)

用法示例 (电脑与手机连接同一 Wi-Fi，将 192.168.1.100 换成电脑局域网 IP):
  pip install mitmproxy
  # 若电脑本机已开 Clash Verge (如端口 7897) 作为上游美国出口:
  mitmdump --listen-host 192.168.1.100 -p 18910 --proxyauth gtool:change-me \
    --mode upstream:http://127.0.0.1:7897 -s gai_mitm_gateway.py

模式切换:
  默认环境变量 GAI_MODE=tri_eft_smart (优先 5x/20x 首月 $0 免费试用 + Pro $1.99)
  老号开付费一折可设: GAI_MODE=tri_smart
"""

import json
import os
import re
import struct
import time
from mitmproxy import http

MODE = os.environ.get("GAI_MODE", "tri_eft_smart").strip()
STATS = {"started_at": int(time.time()), "mode": MODE, "web_hits": 0, "pb_hits": 0}

PAIRS_BY_MODE = {
    "tri_eft_smart": [
        (b"g1.ios.20tb.m.v2", b"g1.20tb.1month_eft.acq"),
        (b"g1.ios.30tb.ai.pro.m", b"g1.ai.ultra.1month_eft.acq"),
    ],
    "eft_20x_direct": [
        (b"g1.ios.20tb.m.v2", b"g1.ai.ultra.1month_eft.acq"),
        (b"g1.ios.30tb.ai.pro.m", b"g1.ai.ultra.1month_eft.acq"),
    ],
    "tri_smart": [
        (b"g1.ios.20tb.m.v2", b"g1.20tb.3months_ip_90p.acq"),
        (b"g1.ios.30tb.ai.pro.m", b"g1.ai.ultra.3months_ip_90p.acq"),
    ],
}


def _enc_varint(v: int) -> bytes:
    out = bytearray()
    while True:
        b = v & 0x7F
        v >>= 7
        if v:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def _read_varint(buf: bytes, pos: int, end: int):
    val = 0
    shift = 0
    while pos < end:
        b = buf[pos]
        pos += 1
        val |= (b & 0x7F) << shift
        if not (b & 0x80):
            return val, pos
        shift += 7
        if shift > 35:
            return None, -1
    return None, -1


def _skip_group(buf: bytes, pos: int, end: int, expected_fn: int, depth: int) -> int:
    if depth <= 0:
        return -1
    while pos < end:
        tag, pos = _read_varint(buf, pos, end)
        if tag is None:
            return -1
        fn, wt = tag >> 3, tag & 7
        if fn <= 0:
            return -1
        if wt == 4:
            return pos if fn == expected_fn else -1
        if wt == 0:
            _, pos = _read_varint(buf, pos, end)
            if pos < 0:
                return -1
        elif wt == 1:
            pos += 8
        elif wt == 5:
            pos += 4
        elif wt == 2:
            ln, pos = _read_varint(buf, pos, end)
            if ln is None or pos + ln > end:
                return -1
            pos += ln
        elif wt == 3:
            pos = _skip_group(buf, pos, end, fn, depth - 1)
            if pos < 0:
                return -1
        else:
            return -1
    return -1


def transform_raw_pb(buf: bytes, start: int, end: int, src_b: bytes, dst_b: bytes, depth: int = 20):
    if depth <= 0 or src_b not in buf[start:end]:
        return None, 0
    out = bytearray()
    pos = start
    hits = 0
    while pos < end:
        tag_start = pos
        tag, pos = _read_varint(buf, pos, end)
        if tag is None:
            return None, 0
        fn, wt = tag >> 3, tag & 7
        if fn <= 0:
            return None, 0
        if wt == 3:
            ge = _skip_group(buf, pos, end, fn, depth - 1)
            if ge < 0:
                return None, 0
            out.extend(buf[tag_start:ge])
            pos = ge
            continue
        out.extend(buf[tag_start:pos])
        if wt == 0:
            vs = pos
            _, pos = _read_varint(buf, pos, end)
            if pos < 0:
                return None, 0
            out.extend(buf[vs:pos])
        elif wt == 1:
            if pos + 8 > end:
                return None, 0
            out.extend(buf[pos : pos + 8])
            pos += 8
        elif wt == 5:
            if pos + 4 > end:
                return None, 0
            out.extend(buf[pos : pos + 4])
            pos += 4
        elif wt == 2:
            ln, pos = _read_varint(buf, pos, end)
            if ln is None or pos + ln > end:
                return None, 0
            sub = buf[pos : pos + ln]
            pos += ln
            if sub == src_b:
                payload = dst_b
                hits += 1
            elif depth > 1 and src_b in sub:
                nested, nh = transform_raw_pb(sub, 0, len(sub), src_b, dst_b, depth - 1)
                if nested is not None and nh > 0:
                    payload = nested
                    hits += nh
                else:
                    payload = sub
            else:
                payload = sub
            out.extend(_enc_varint(len(payload)))
            out.extend(payload)
        else:
            return None, 0
    if pos != end or hits == 0:
        return None, 0
    return bytes(out), hits


def transform_grpc_or_raw_pb(buf: bytes, src_b: bytes, dst_b: bytes):
    if len(buf) >= 5:
        fp = 0
        valid = True
        total_hits = 0
        framed = bytearray()
        while fp < len(buf):
            if fp + 5 > len(buf):
                valid = False
                break
            flg = buf[fp]
            if flg not in (0x00, 0x01, 0x80, 0x81):
                valid = False
                break
            flen = struct.unpack(">I", buf[fp + 1 : fp + 5])[0]
            if flen > 16777216 or fp + 5 + flen > len(buf):
                valid = False
                break
            pl = buf[fp + 5 : fp + 5 + flen]
            if flg == 0x00 and src_b in pl:
                tr, h = transform_raw_pb(pl, 0, len(pl), src_b, dst_b, 20)
                if tr is not None and h > 0:
                    pl = tr
                    total_hits += h
            framed.append(flg)
            framed.extend(struct.pack(">I", len(pl)))
            framed.extend(pl)
            fp += 5 + flen
        if valid and fp == len(buf) and total_hits > 0:
            return bytes(framed), total_hits
    return transform_raw_pb(buf, 0, len(buf), src_b, dst_b, 20)


def request(flow: http.HTTPFlow) -> None:
    host = flow.request.pretty_host
    path = flow.request.path
    if host == "one.google.com" and path.startswith("/g1-sku-report"):
        flow.response = http.Response.make(
            200,
            json.dumps({"ok": True, **STATS}, ensure_ascii=False, indent=2).encode("utf-8"),
            {"Content-Type": "application/json; charset=utf-8"},
        )
        return
    if host == "subscriptionsmobile-pa.googleapis.com" and "GetDynamicStorefrontInfo" in path:
        flow.request.headers["Accept-Encoding"] = "identity"
        flow.request.headers["grpc-accept-encoding"] = "identity"


def response(flow: http.HTTPFlow) -> None:
    if not flow.response or not flow.response.raw_content:
        return
    host = flow.request.pretty_host
    path = flow.request.path
    pairs = PAIRS_BY_MODE.get(MODE, PAIRS_BY_MODE["tri_eft_smart"])

    if host == "one.google.com" and re.match(r"^/(?:u/\d+/)?ai(?:[/?#].*)?$", path):
        txt = flow.response.get_text(strict=False)
        if not txt:
            return
        hits = 0
        for s_b, d_b in pairs:
            s_str, d_str = s_b.decode(), d_b.decode()
            if s_str in txt:
                hits += txt.count(s_str)
                txt = txt.replace(s_str, d_str)
        txt, pro_n = re.subn(r"g1\.ios\.2tb\.[A-Za-z0-9._-]+", "g1.2tb.ai.12months_ip_90p", txt)
        hits += pro_n
        if hits:
            STATS["web_hits"] += hits
            flow.response.set_text(txt)
    elif host == "subscriptionsmobile-pa.googleapis.com" and "GetDynamicStorefrontInfo" in path:
        cur = flow.response.content
        if not cur:
            return
        any_hit = 0
        for s_b, d_b in pairs:
            tr, h = transform_grpc_or_raw_pb(cur, s_b, d_b)
            if tr is not None and h > 0:
                cur = tr
                any_hit += h
        if any_hit:
            STATS["pb_hits"] += any_hit
            flow.response.content = cur
