/*
Google One 控制台版 1.0
来源：用户提供的 google_pro_6_12_24(1).rar，已核对主脚本 SHA256。
默认关闭；不自动打开收银台、不自动点击订阅、不读取银行卡或登录凭据。
沿用样本中的优惠令牌和 AI + YouTube 两项商品，不保证优惠可用或价格为零。
本脚本仅在当前网页存在，刷新即清除；它不包含扩展的免费价格提示脚本。
*/
(() => {
  "use strict";
  if (location.protocol !== "https:" || location.hostname !== "one.google.com") {
    console.warn("请在 https://one.google.com/plans 登录后的顶层页面运行。");
    return;
  }
  if (window.top !== window) {
    console.warn("请选择 Google One 顶层页面的控制台，不要在付款 iframe 中运行。");
    return;
  }
  if (window.G1Console) {
    console.info("G1Console 已存在；本次未重复安装。", window.G1Console.status?.());
    return;
  }
  if (window.__GAPT_HOOKED) {
    console.warn("检测到原扩展的 Hook。请先关闭该扩展并刷新，再运行控制台版。");
    return;
  }
  const originals = {
    send: XMLHttpRequest.prototype.send,
    iframeSrc: Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype, "src"),
    setAttribute: Element.prototype.setAttribute,
    trusted: window.TrustedTypePolicy ? TrustedTypePolicy.prototype.createScriptURL : null,
  };
  const stats = { requestBodyRewrites: 0, checkoutUrlRewriteCalls: 0 };
  let removed = false;
  const PREFIX = "subs:com.google.android.apps.subscriptions.red:";

  const TOKENS = {
    "12m": "AVbCH/cspB8VdqKJ+ax/uPxUFAVuYRPX4iSjtg4Fu0PG9zUeURSM7y//LlQva1dCd/rbKVM6EJmyiG/C9BoQ95pMl8yDCHuiwCvM5CuGJME=",
    "6m_ss": "AVbCH/cgl4zvPT2Lqw95Gn+RYAJIVwFwi783i6uVprX7u3MCa5J4CcTXH5RABa5WjBrUoQnwf8vI10TNV7ktd26myIdxqIwGmNoJ5ofYNqpQ10RKoSvHs75wsfA=",
    "6m": "AVbCH/fUON3w8hpfeutprA3BMQwrBwYIB6Y8CSWi1isDCDswKUUhGQ3dluj5WXsNKOvr8K5UULBGrRsf4KlW1rHLz0fF3SvxQhBFRbBOHCA=",
    "6m_2": "AVbCH/cJ5SeHgkVRt+bdcrapx/aLSu2kbsBgMdI413zbllDNsNQoC/zVlG/Npbu55WlMzBwWPhUedIvZFDg7fw0CmCv/8DKj04IZ21pK7mrV/hh5"
  };
  const YT_FREE_TOK = "AVbCH/eW4Nfp8KBl0zlm7x9PhaiCvpnqwUuL2D8NFPBQgmM9+HuYS1h2xH5lLWU/BsBj775LK5GqK8UHKqoSzhDDz+PqP3paNesqLU0r9i6XCrYa";

  let currentTest = null;
  let subId = null;

  function makeCfg(layer) {
    if (!layer || layer === "off" || !TOKENS[layer]) return null;
    return {
      name: "gapt_" + layer,
      full_items: [
        [[PREFIX + "g1.2tb.ai.subs_variant", 21], null, null, null, 1, [TOKENS[layer]]],
        [[PREFIX + "g1.youtube_premium_individual_add_on", 21], null, null, null, 1, [YT_FREE_TOK]]
      ],
      ear8: null
    };
  }

  /* ---------- Bottom-right status badge ---------- */
  let badge = null;
  function showBadge(text, color) {
    try {
      if (!document.body) return;
      if (!badge) {
        badge = document.createElement("div");
        badge.style.cssText = "position:fixed;right:14px;bottom:14px;z-index:2147483647;" +
          "padding:8px 12px;border-radius:8px;font:12px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;" +
          "box-shadow:0 2px 10px rgba(0,0,0,.15);border:1px solid #d0d0d0;background:#fff;color:#333;max-width:260px;";
        document.body.appendChild(badge);
      }
      badge.textContent = text;
      badge.style.background = color || "#fff";
    } catch (e) {}
  }

  function refreshBadge() {
    if (!currentTest) {
      showBadge("Google One 控制台脚本：关闭", "#f5f5f5");
    } else {
      const label = { "12m": "12 Months", "6m_ss": "6 Months (SS)", "6m": "6 Months", "6m_2": "6 Months (Alt)" }[currentTest.layer] || currentTest.layer;
      showBadge("已启用 " + label + " · 含 YouTube 附加项 · 未验证价格", "#eef2f7");
    }
  }

  /* ---------- Request rewriting ---------- */
  function patchNode(node) {
    if (!Array.isArray(node) || !currentTest || !Array.isArray(currentTest.full_items)) return false;
    let patched = false;
    if (node.length > 12 && Array.isArray(node[12])) {
      if (Array.isArray(node[7]) && Array.isArray(node[7][5]) && node[7][5].length > 0) subId = node[7][5][0];
      node[12] = currentTest.full_items;
      const mode = (currentTest.ear8 && currentTest.ear8[1]) || 5;
      if (currentTest.ear8) node[7] = currentTest.ear8;
      else if (Array.isArray(node[7]) && Array.isArray(node[7][5]) && node[7][5].length > 0) node[7][1] = mode;
      else if (subId) node[7] = [null, mode, null, null, null, [subId]];
      patched = true;
    }
    if (node.length > 10 && Array.isArray(node[10]) && Array.isArray(node[10][0])) {
      node[10] = [currentTest.full_items];
      if (Array.isArray(node[2]) && Array.isArray(node[2][2]) && Array.isArray(node[2][2][8])) {
        node[2][2][8] = [currentTest.full_items];
      }
      if (currentTest.ear8) node[6] = currentTest.ear8;
      patched = true;
    }
    return patched;
  }

  function rewriteFreq(bodyStr) {
    if (typeof bodyStr !== "string" || !bodyStr.includes("f.req=") || !currentTest) return bodyStr;
    try {
      const parts = bodyStr.split("&");
      for (let i = 0; i < parts.length; i++) {
        if (parts[i].startsWith("f.req=")) {
          const raw = decodeURIComponent(parts[i].slice(6).replace(/\+/g, " "));
          const outer = JSON.parse(raw);
          let changed = false;
          if (Array.isArray(outer)) {
            for (const group of outer) {
              if (!Array.isArray(group)) continue;
              for (const call of group) {
                if (Array.isArray(call) && call[0] === "Ngbm" && typeof call[1] === "string") {
                  const payload = JSON.parse(call[1]);
                  if (Array.isArray(payload)) {
                    if (patchNode(payload[0])) changed = true;
                    if (patchNode(payload[1])) changed = true;
                  }
                  if (changed) call[1] = JSON.stringify(payload);
                }
              }
            }
          }
          if (changed) {
            parts[i] = "f.req=" + encodeURIComponent(JSON.stringify(outer));
            stats.requestBodyRewrites++;
            return parts.join("&");
          }
        }
      }
    } catch (e) {}
    return bodyStr;
  }

  const origSend = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.send = function (body) {
    try {
      if (typeof body === "string" && body.includes("Ngbm")) body = rewriteFreq(body);
    } catch (e) {}
    return origSend.call(this, body);
  };

  function rewriteUrl(val) {
    const s = String(val || "");
    if (!s.includes("/eacquire/multiline") || !currentTest) return val;
    try {
      const u = new URL(s, location.origin);
      if (u.protocol !== "https:" || u.hostname !== "tokenized.play.google.com") return val;
      const earStr = u.searchParams.get("ear");
      if (!earStr) return val;
      const ear = JSON.parse(earStr);
      if (Array.isArray(ear[8]) && Array.isArray(ear[8][5]) && ear[8][5].length > 0) subId = ear[8][5][0];
      if (Array.isArray(ear[13]) && Array.isArray(currentTest.full_items)) ear[13][0] = currentTest.full_items;
      if (Array.isArray(ear[4]) && typeof ear[4][0] === "string" && Array.isArray(currentTest.full_items)) {
        try {
          const inner4 = JSON.parse(atob(ear[4][0]));
          if (Array.isArray(inner4) && inner4.length > 8) {
            inner4[8] = [currentTest.full_items];
            ear[4][0] = btoa(JSON.stringify(inner4));
          }
        } catch (e4) {}
      }
      const mode = (currentTest.ear8 && currentTest.ear8[1]) || 5;
      if (currentTest.ear8) ear[8] = currentTest.ear8;
      else if (Array.isArray(ear[8]) && Array.isArray(ear[8][5]) && ear[8][5].length > 0) ear[8][1] = mode;
      else if (subId) ear[8] = [null, mode, null, null, null, [subId]];
      ear[24] = null;
      u.searchParams.set("ear", JSON.stringify(ear));
      stats.checkoutUrlRewriteCalls++;
      return u.toString();
    } catch (e) {
      return val;
    }
  }

  if (window.TrustedTypePolicy && TrustedTypePolicy.prototype.createScriptURL) {
    const origCreate = TrustedTypePolicy.prototype.createScriptURL;
    TrustedTypePolicy.prototype.createScriptURL = function (input, ...args) {
      return origCreate.call(this, rewriteUrl(input), ...args);
    };
  }

  const srcDesc = Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype, "src");
  if (srcDesc && srcDesc.set) {
    Object.defineProperty(HTMLIFrameElement.prototype, "src", {
      ...srcDesc,
      set(v) {
        if (typeof v === "string") v = rewriteUrl(v);
        return srcDesc.set.call(this, v);
      }
    });
  }
  const origSetAttr = Element.prototype.setAttribute;
  Element.prototype.setAttribute = function (name, val) {
    if (this instanceof HTMLIFrameElement && String(name).toLowerCase() === "src") val = rewriteUrl(String(val));
    return origSetAttr.call(this, name, val);
  };


  // 不使用扩展存储或跨窗口消息，控制台直接调用本地闭包。
  const tiers = Object.freeze(["off", "12m", "6m_ss", "6m", "6m_2"]);
  const owned = {
    send: XMLHttpRequest.prototype.send,
    iframeSrc: Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype, "src"),
    setAttribute: Element.prototype.setAttribute,
    trusted: window.TrustedTypePolicy ? TrustedTypePolicy.prototype.createScriptURL : null,
  };
  function status() {
    return {
      version: "1.0",
      removed,
      enabled: !removed && !!currentTest,
      tier: currentTest?.layer || "off",
      includesYouTubeAddonWhenEnabled: true,
      requestBodyRewrites: stats.requestBodyRewrites,
      checkoutUrlRewriteCalls: stats.checkoutUrlRewriteCalls,
      priceVerified: false,
      note: "计数表示参数改写次数，不表示请求获批、零元或订阅成功。",
    };
  }
  function setTier(layer) {
    if (removed) throw new Error("脚本已移除，请重新运行完整脚本。");
    if (!tiers.includes(layer)) throw new Error("档位须为：" + tiers.join(", "));
    const cfg = makeCfg(layer);
    currentTest = cfg ? Object.assign({layer}, cfg) : null;
    if (!currentTest) subId = null;
    refreshBadge();
    return status();
  }
  function remove() {
    if (removed) return {removed: true, restored: [], preservedLaterHooks: []};
    currentTest = null;
    subId = null;
    const restored = [], preservedLaterHooks = [];
    if (XMLHttpRequest.prototype.send === owned.send) {
      XMLHttpRequest.prototype.send = originals.send;
      restored.push("XMLHttpRequest.send");
    } else preservedLaterHooks.push("XMLHttpRequest.send");
    if (Element.prototype.setAttribute === owned.setAttribute) {
      Element.prototype.setAttribute = originals.setAttribute;
      restored.push("Element.setAttribute");
    } else preservedLaterHooks.push("Element.setAttribute");
    const srcNow = Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype, "src");
    if (owned.iframeSrc?.set !== originals.iframeSrc?.set) {
      if (srcNow?.set === owned.iframeSrc.set && srcNow?.get === owned.iframeSrc.get) {
        Object.defineProperty(HTMLIFrameElement.prototype, "src", originals.iframeSrc);
        restored.push("HTMLIFrameElement.src");
      } else preservedLaterHooks.push("HTMLIFrameElement.src");
    }
    if (originals.trusted && owned.trusted !== originals.trusted) {
      if (TrustedTypePolicy.prototype.createScriptURL === owned.trusted) {
        TrustedTypePolicy.prototype.createScriptURL = originals.trusted;
        restored.push("TrustedTypePolicy.createScriptURL");
      } else preservedLaterHooks.push("TrustedTypePolicy.createScriptURL");
    }
    if (badge) badge.remove();
    if (window.G1Console === api) delete window.G1Console;
    if (window.__GAPT_HOOKED === true) delete window.__GAPT_HOOKED;
    removed = true;
    return {removed: true, restored, preservedLaterHooks,
      note: "移除只影响今后的调用，不撤销已经发出的请求或已打开的结账页面。"};
  }
  const api = Object.freeze({setTier, off: () => setTier("off"), status, remove, tiers});
  window.__GAPT_HOOKED = true;
  window.G1Console = api;
  setTier("off");
  console.info("控制台脚本已加载，当前关闭。可用命令：G1Console.setTier('12m')、G1Console.off()、G1Console.status()、G1Console.remove()。启用后会包含 YouTube 附加项；不保证优惠或零元价格。");
  return api.status();
})();
