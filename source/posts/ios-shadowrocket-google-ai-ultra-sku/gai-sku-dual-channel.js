// Google AI iOS StoreKit Dual-Channel SKU Adapter (3-Tier Free-Trial Smart Mode (G1-ACQ v7.6) · 5x 1m Free + 20x 1m Free + Pro $1.99x12m)
(function() {
// 可选模式: "tri_eft_smart" (默认: 5x/20x 首月 $0 免费试用 + Pro $1.99, 无资格自动回退一折)
//          "tri_smart"     (老号付费一折专版: 5x $9.99/月 + 20x $19.99/月 + Pro $1.99/月)
//          "eft_20x_direct"(全部 Ultra 按钮直通 20x 30TB 首月 $0 免费试用)
const MODE_KIND = "tri_eft_smart";
const SRC_STR = "g1.ios.20tb.m.v2";
const DST_STR = "g1.20tb.1month_eft.acq";
function toAsciiBytes(s) {
  const a = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) a[i] = s.charCodeAt(i) & 0xff;
  return a;
}
function encVarint(v) {
  const out = [];
  while (true) {
    const b = v & 0x7f;
    v >>>= 7;
    if (v) out.push(b | 0x80);
    else { out.push(b); break; }
  }
  return out;
}
function eqBytes(buf, off, len, pat) {
  if (len !== pat.length) return false;
  for (let i = 0; i < len; i++) if (buf[off + i] !== pat[i]) return false;
  return true;
}
function hasSubBytes(buf, off, len, pat) {
  if (len < pat.length) return false;
  const last = off + len - pat.length;
  outer: for (let i = off; i <= last; i++) {
    for (let j = 0; j < pat.length; j++) if (buf[i + j] !== pat[j]) continue outer;
    return true;
  }
  return false;
}
function skipGroup(buf, pos, end, expectedField, depth) {
  if (depth <= 0) return -1;
  while (pos < end) {
    let tag = 0, shift = 0;
    while (pos < end) {
      const b = buf[pos++];
      tag |= (b & 0x7f) << shift;
      if (!(b & 0x80)) break;
      shift += 7;
      if (shift > 35) return -1;
    }
    const fn = tag >>> 3;
    const wt = tag & 7;
    if (fn <= 0) return -1;
    if (wt === 4) return (fn === expectedField) ? pos : -1;
    if (wt === 0) {
      while (pos < end && (buf[pos++] & 0x80)) {}
    } else if (wt === 1) {
      if (pos + 8 > end) return -1; pos += 8;
    } else if (wt === 5) {
      if (pos + 4 > end) return -1; pos += 4;
    } else if (wt === 2) {
      let ln = 0, ls = 0;
      while (pos < end) {
        const b = buf[pos++]; ln |= (b & 0x7f) << ls;
        if (!(b & 0x80)) break;
        ls += 7; if (ls > 28) return -1;
      }
      if (ln < 0 || pos + ln > end) return -1; pos += ln;
    } else if (wt === 3) {
      pos = skipGroup(buf, pos, end, fn, depth - 1);
      if (pos < 0) return -1;
    } else { return -1; }
  }
  return -1;
}
function transformRawPb(buf, start, end, srcB, dstB, depth) {
  if (depth <= 0 || !hasSubBytes(buf, start, end - start, srcB)) return null;
  const chunks = [];
  let pos = start;
  let hits = 0;
  while (pos < end) {
    const tagStart = pos;
    let tag = 0, shift = 0;
    while (pos < end) {
      const b = buf[pos++];
      tag |= (b & 0x7f) << shift;
      if (!(b & 0x80)) break;
      shift += 7;
      if (shift > 35) return null;
    }
    const fn = tag >>> 3;
    const wt = tag & 7;
    if (fn <= 0) return null;
    if (wt === 3) {
      const ge = skipGroup(buf, pos, end, fn, depth - 1);
      if (ge < 0) return null;
      chunks.push(buf.subarray(tagStart, ge));
      pos = ge;
      continue;
    }
    chunks.push(buf.subarray(tagStart, pos));
    if (wt === 0) {
      const vs = pos;
      while (pos < end && (buf[pos++] & 0x80)) {}
      chunks.push(buf.subarray(vs, pos));
    } else if (wt === 1) {
      if (pos + 8 > end) return null;
      chunks.push(buf.subarray(pos, pos + 8)); pos += 8;
    } else if (wt === 5) {
      if (pos + 4 > end) return null;
      chunks.push(buf.subarray(pos, pos + 4)); pos += 4;
    } else if (wt === 2) {
      let ln = 0, ls = 0;
      while (pos < end) {
        const b = buf[pos++];
        ln |= (b & 0x7f) << ls;
        if (!(b & 0x80)) break;
        ls += 7;
        if (ls > 28) return null;
      }
      if (ln < 0 || pos + ln > end) return null;
      const subStart = pos; pos += ln;
      let rep = null;
      if (eqBytes(buf, subStart, ln, srcB)) {
        rep = dstB; hits++;
      } else if (depth > 1 && hasSubBytes(buf, subStart, ln, srcB)) {
        const nested = transformRawPb(buf, subStart, subStart + ln, srcB, dstB, depth - 1);
        if (nested) { rep = nested.bytes; hits += nested.hits; }
      }
      const payload = rep || buf.subarray(subStart, subStart + ln);
      chunks.push(new Uint8Array(encVarint(payload.length)));
      chunks.push(payload);
    } else {
      return null;
    }
  }
  if (pos !== end || hits === 0) return null;
  let total = 0;
  for (const c of chunks) total += c.length;
  const out = new Uint8Array(total);
  let off = 0;
  for (const c of chunks) { out.set(c, off); off += c.length; }
  return { bytes: out, hits };
}
function transformFramedOrRawPb(buf, srcB, dstB) {
  if (buf.length >= 5) {
    let fp = 0, validFrames = true, fHits = 0;
    const fChunks = [];
    while (fp < buf.length) {
      if (fp + 5 > buf.length) { validFrames = false; break; }
      const flg = buf[fp];
      if (flg !== 0x00 && flg !== 0x01 && flg !== 0x80 && flg !== 0x81) { validFrames = false; break; }
      const flen = ((buf[fp + 1] << 24) >>> 0) + (buf[fp + 2] << 16) + (buf[fp + 3] << 8) + buf[fp + 4];
      if (flen > 16777216 || fp + 5 + flen > buf.length) { validFrames = false; break; }
      const pStart = fp + 5, pEnd = pStart + flen;
      let pl = buf.subarray(pStart, pEnd);
      if (flg === 0x00 && hasSubBytes(buf, pStart, flen, srcB)) {
        const tr = transformRawPb(buf, pStart, pEnd, srcB, dstB, 20);
        if (tr) { pl = tr.bytes; fHits += tr.hits; }
      }
      const hdr = new Uint8Array(5);
      hdr[0] = flg;
      const nl = pl.length;
      hdr[1] = (nl >>> 24) & 0xff; hdr[2] = (nl >>> 16) & 0xff; hdr[3] = (nl >>> 8) & 0xff; hdr[4] = nl & 0xff;
      fChunks.push(hdr); fChunks.push(pl);
      fp = pEnd;
    }
    if (validFrames && fp === buf.length && fHits > 0) {
      let tot = 0; for (const c of fChunks) tot += c.length;
      const out = new Uint8Array(tot);
      let o = 0; for (const c of fChunks) { out.set(c, o); o += c.length; }
      return { bytes: out, hits: fHits };
    }
  }
  return transformRawPb(buf, 0, buf.length, srcB, dstB, 20);
}
const respObj = (typeof $response !== 'undefined' && $response) ? $response : {};
const isQxBytes = (respObj.bodyBytes instanceof ArrayBuffer);
let raw = isQxBytes ? new Uint8Array(respObj.bodyBytes) : respObj.body;
if (raw instanceof ArrayBuffer) raw = new Uint8Array(raw);
if (raw instanceof Uint8Array) {
  let cur = raw, anyHit = false;
  const pairs = (MODE_KIND === 'tri_eft_smart') ? [
    ['g1.ios.20tb.m.v2', 'g1.20tb.1month_eft.acq'],
    ['g1.ios.30tb.ai.pro.m', 'g1.ai.ultra.1month_eft.acq']
  ] : (MODE_KIND === 'eft_20x_direct') ? [
    ['g1.ios.20tb.m.v2', 'g1.ai.ultra.1month_eft.acq'],
    ['g1.ios.30tb.ai.pro.m', 'g1.ai.ultra.1month_eft.acq']
  ] : (MODE_KIND === 'tri_smart') ? [
    ['g1.ios.20tb.m.v2', 'g1.20tb.3months_ip_90p.acq'],
    ['g1.ios.30tb.ai.pro.m', 'g1.ai.ultra.3months_ip_90p.acq']
  ] : [[SRC_STR, DST_STR]];
  for (const [s, d] of pairs) {
    const r = transformFramedOrRawPb(cur, toAsciiBytes(s), toAsciiBytes(d));
    if (r && r.hits > 0) { cur = r.bytes; anyHit = true; }
  }
  if (!anyHit) { $done({}); return; }
  if (isQxBytes) {
    $done({ bodyBytes: cur.buffer.slice(cur.byteOffset, cur.byteOffset + cur.byteLength) });
  } else {
    $done({ body: cur });
  }
} else if (typeof raw === 'string' && raw.length > 0) {
  if (MODE_KIND === 'tri_eft_smart' || MODE_KIND === 'tri_smart') {
    const obs = raw.match(/g1\.[a-z0-9._]{2,60}acq/g) || [];
    const sm = (MODE_KIND === 'tri_eft_smart')
      ? { 'g1.ios.20tb.m.v2': 'g1.20tb.1month_eft.acq', 'g1.ios.30tb.ai.pro.m': 'g1.ai.ultra.1month_eft.acq' }
      : { 'g1.ios.20tb.m.v2': 'g1.20tb.3months_ip_90p.acq', 'g1.ios.30tb.ai.pro.m': 'g1.ai.ultra.3months_ip_90p.acq' };
    const fb = (MODE_KIND === 'tri_eft_smart')
      ? { 'g1.20tb.1month_eft.acq': 'g1.20tb.3months_ip_90p.acq', 'g1.ai.ultra.1month_eft.acq': 'g1.ai.ultra.3months_ip_90p.acq' }
      : {};
    let hits = 0;
    const out = raw.replace(/(^|[^A-Za-z0-9._@%-])(g1\.[A-Za-z0-9._-]+)(?=$|[^A-Za-z0-9._-])/g, (m, pre, id) => {
      if (id.indexOf('g1.ios.2tb.') === 0 && id.length > 11) { hits++; return pre + 'g1.2tb.ai.12months_ip_90p'; }
      if (Object.prototype.hasOwnProperty.call(sm, id)) {
        let t = sm[id];
        if (obs.indexOf(t) === -1 && fb[t] && obs.indexOf(fb[t]) !== -1) t = fb[t];
        hits++; return pre + t;
      }
      return m;
    });
    $done(hits ? { body: out } : {});
  } else if (MODE_KIND === 'eft_20x_direct') {
    const out = raw.replace(/g1\.ios\.(?:20tb\.m\.v2|30tb\.ai\.pro\.m)/g, 'g1.ai.ultra.1month_eft.acq');
    $done(out !== raw ? { body: out } : {});
  } else {
    const out = raw.replace(/g1\.ios\.20tb\.m\.v2/g, DST_STR);
    $done(out !== raw ? { body: out } : {});
  }
} else {
  $done({});
}
})();
