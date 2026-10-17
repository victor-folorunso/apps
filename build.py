"""Builds wonderperk's app site from apps.json.

  index.html              every app as a card
  <id>/index.html         an app's page: join the test and install (testing),
                          or a Google Play button (live)
  <id>/privacy/index.html the app's privacy policy (from privacy/<id>.html)
  <id>/<slug>/            extra pages for apps with accounts, each optional:
                          "terms", "delete_account", "child_safety" (see
                          EXTRA_PAGES), e.g. "terms": "terms/<id>.html"

Add an app: put its icon in <id>/icon.png, its privacy text in
privacy/<id>.html, an entry in apps.json, then run `python build.py` and
push. When an app goes public, change its "status" to "live" and rebuild.

Served by GitHub Pages at https://victor-folorunso.github.io/apps/
"""

import html
import json
from pathlib import Path

ROOT = Path(__file__).parent
SITE = "https://victor-folorunso.github.io/apps/"

STYLE = """
:root { --bg:#0f1115; --panel:#181b21; --line:#2a2e36; --text:#ece6da; --dim:#a8a192; --accent:#e0a36a; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--text);
       font:17px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; }
main { max-width:720px; margin:0 auto; padding:32px 16px 64px; }
a { color:var(--accent); }
h1 { font-size:2rem; margin:0 0 4px; letter-spacing:.02em; }
h2 { font-size:1.1rem; margin:32px 0 8px; color:var(--accent); }
.dim { color:var(--dim); }
.card { display:flex; gap:16px; align-items:center; padding:16px; margin:12px 0;
        background:var(--panel); border:1px solid var(--line); border-radius:16px;
        color:inherit; text-decoration:none; }
.card img { width:72px; height:72px; border-radius:16px; flex:none; }
.card b { font-size:1.15rem; }
.badge { display:inline-block; font-size:.75rem; padding:2px 8px; border-radius:99px;
         border:1px solid var(--line); color:var(--dim); margin-left:6px; vertical-align:middle; }
.hero { display:flex; gap:20px; align-items:center; margin:8px 0 24px; }
.hero img { width:96px; height:96px; border-radius:22px; }
.step { background:var(--panel); border:1px solid var(--line); border-radius:16px;
        padding:20px; margin:16px 0; }
.step .n { font-weight:700; color:var(--accent); }
.button { display:block; text-align:center; padding:16px; margin-top:12px;
          border-radius:14px; background:var(--accent); color:#1a0f07;
          font-weight:700; font-size:1.1rem; text-decoration:none; }
.button.secondary { background:transparent; color:var(--text); border:1px solid var(--line); }
footer { margin-top:48px; font-size:.9rem; color:var(--dim); }
.short { background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:16px 20px; margin:20px 0; }
"""


def page(title, description, body, depth, accent="#e0a36a"):
    base = "../" * depth
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<style>{STYLE} :root {{ --accent:{accent}; }}</style>
</head>
<body><main>
{body}
<footer><a href="{base}">All apps</a> &middot; &copy; wonderperk</footer>
</main></body>
</html>
"""


# Shown only inside TikTok / Instagram / Facebook's in-app browsers, where
# people aren't signed in to Google, so "Join testers" asks for a Google
# password and the Play link may not open. Opt in per app: "inapp_tip": true.
INAPP_TIP = r"""
<div id="inapp" style="display:none;margin:0 0 18px;padding:18px;border-radius:16px;background:var(--accent);color:#fff;text-align:center">
<div style="font-size:1.15rem;font-weight:800;margin-bottom:6px">First: open this page in your browser</div>
<div style="opacity:.9">You opened it inside TikTok, Instagram or Facebook, where joining the testers
doesn&#39;t work.</div>
<a class="button" id="open-browser" href="#" data-track="open_browser"
style="background:#fff;color:var(--accent);font-size:1.1rem;margin-top:14px">Open in browser</a>
<div style="opacity:.85;font-size:.9rem;margin-top:10px">Not working? Tap <b>&#8942;</b> or <b>&hellip;</b>
at the top right, then <b>Open in browser</b>.</div></div>
<!-- Plain fallback for everyone: the banner above relies on recognising the
     in-app browser, which can fail. Hidden only when the banner shows. -->
<div id="inapp-help" class="short" style="margin:0 0 18px">
<b>Came here from TikTok, Instagram or Facebook?</b> Open this page in your phone&#39;s browser
first, or joining won&#39;t work:
<ol style="margin:8px 0 0;padding-left:22px">
<li>Tap <b>&hellip;</b> or <b>&#8942;</b> at the <b>top right</b> of your screen</li>
<li>Tap <b>Open in browser</b></li></ol>
<div style="margin-top:10px">Can&#39;t find it? Copy this link and paste it into your browser:<br>
<b style="word-break:break-all">%LINK%</b></div>
<a class="button secondary" id="copy-link" href="#" data-track="copy_link">Copy link</a></div>
<script>
(function () {
  var btn = document.getElementById("copy-link");
  btn.addEventListener("click", function (e) {
    e.preventDefault();
    var url = location.href;
    var done = function () { btn.textContent = "Copied! Now paste it in your browser"; };
    var fallback = function () { window.prompt("Copy this link:", url); };
    try { navigator.clipboard.writeText(url).then(done, fallback); } catch (err) { fallback(); }
  });
})();
</script>
<script>
(function () {
  var ua = navigator.userAgent || "";
  if (!/musical_ly|BytedanceWebview|TikTok|Instagram|FBAN|FBAV|FB_IAB/i.test(ua)) return;
  document.getElementById("inapp").style.display = "block";
  document.getElementById("inapp-help").style.display = "none";
  // Keep where the visit came from when it moves to the real browser: the
  // ad's click id (ttclid, fbclid) can get dropped on the way, ?src= is ours.
  var q = new URLSearchParams(location.search);
  if (!q.get("src")) {
    q.set("src", q.get("ttclid") ? "tiktok_ad" : q.get("fbclid") ? "facebook_ad"
      : /Instagram/i.test(ua) ? "instagram" : /FBAN|FBAV|FB_IAB/i.test(ua) ? "facebook" : "tiktok");
    // Also covers the in-app browser's own "Open in browser" menu, which uses the current URL.
    try { history.replaceState(null, "", location.pathname + "?" + q.toString() + location.hash); } catch (e) {}
  }
  // No package: Android hands it to the person's default browser.
  var toBrowser = function (href) { return "intent://" + href.replace(/^https?:\/\//, "") + "#Intent;scheme=https;end"; };
  document.getElementById("open-browser").href = toBrowser(location.href);
  // The step buttons too: Google sign-in only works in the real browser.
  // (They come later in the page, so wait for it to load.)
  if (/android/i.test(ua)) document.addEventListener("DOMContentLoaded", function () {
    var buttons = document.querySelectorAll("a.button[data-track='join'], a.button[data-track='get']");
    for (var i = 0; i < buttons.length; i++) buttons[i].href = toBrowser(buttons[i].href);
  });
})();
</script>"""


# Between steps 1 and 2: Google needs a few minutes to add a new group member
# to the test. Opt in per app: "wait_tip": true.
WAIT_TIP = """
<div class="short" style="border-style:dashed;text-align:center">&#9203; <b>Wait about 5&ndash;10 minutes</b>
before step 2. Google takes a little while to add you to the testers. If step 2
says you&#39;re not a tester yet, wait a bit longer and try again.</div>"""


# Anonymous step counts (page opened, "Join testers", "Get <app>", "Open in
# browser") sent to the app's own backend. No cookies or personal data: only
# the step, Android/iPhone/other, which in-app browser if any, and ?src= from
# the link. Opt in per app: "track_url": "<endpoint>". Buttons carry
# data-track names; the endpoint must accept them (ContactSync: Supabase
# function `track`, table site_events).
TRACK = r"""
<script>
(function () {
  var url = "%(url)s", app = "%(app)s";
  var ua = navigator.userAgent || "";
  var platform = /android/i.test(ua) ? "android" : /iphone|ipad|ipod/i.test(ua) ? "ios" : "other";
  var browser = /musical_ly|BytedanceWebview|TikTok/i.test(ua) ? "tiktok"
    : /Instagram/i.test(ua) ? "instagram" : /FBAN|FBAV|FB_IAB/i.test(ua) ? "facebook" : "browser";
  // ?src= wins; otherwise the click IDs ad platforms add to ad links.
  var q = new URLSearchParams(location.search);
  var source = (q.get("src") || (q.get("ttclid") ? "tiktok_ad" : (q.get("gclid") || q.get("gbraid") || q.get("wbraid")) ? "google_ad"
    : q.get("fbclid") ? "facebook" : "")).slice(0, 20);
  function send(event) {
    var body = JSON.stringify({ app: app, event: event, platform: platform, browser: browser, source: source });
    try { if (navigator.sendBeacon(url, new Blob([body], { type: "text/plain" }))) return; } catch (e) {}
    fetch(url, { method: "POST", body: body, keepalive: true, headers: { "Content-Type": "text/plain" } });
  }
  send("page_view");
  document.addEventListener("click", function (e) {
    var el = e.target.closest && e.target.closest("[data-track]");
    if (el) send(el.getAttribute("data-track"));
  });
})();
</script>"""


# A checklist for people who've never joined a test: one big numbered card per
# step, the current one highlighted, finished ones ticked, and a live countdown
# for the wait (Google takes minutes to add a new group member). Progress is
# kept in this browser so coming back from Google Groups or Play picks up where
# they were. Opt in per app: "guided_steps": true ("after_install" sets step 4).
GUIDED_STYLE = """
.flow-head { font-size:1.35rem; font-weight:800; margin:28px 0 2px; }
.gstep { display:flex; gap:14px; background:var(--panel); border:2px solid var(--line);
         border-radius:18px; padding:18px; margin:14px 0; transition:opacity .2s, border-color .2s; }
.gstep .num { flex:none; width:44px; height:44px; border-radius:50%; display:flex; align-items:center;
              justify-content:center; font-weight:800; font-size:1.3rem; background:var(--line); color:var(--text); }
.gstep .gbody { flex:1; min-width:0; }
.gstep .gtitle { font-size:1.2rem; font-weight:800; line-height:1.3; margin-top:8px; }
.gstep .gtext { color:var(--dim); margin-top:4px; }
.gstep[data-state="now"] { border-color:var(--accent); }
.gstep[data-state="now"] .num { background:var(--accent); color:#1a0f07; }
.gstep[data-state="later"] { opacity:.6; }
.gstep[data-state="done"] { opacity:.8; }
.gstep[data-state="done"] .num { background:#3aa76d; color:#fff; font-size:0; }
.gstep[data-state="done"] .num::after { content:"✓"; font-size:1.4rem; }
.gstep[data-state="done"] .timer, .gstep[data-state="done"] .here { display:none; }
.gstep .here { display:none; font-size:.8rem; font-weight:800; letter-spacing:.08em; color:var(--accent); }
.gstep[data-state="now"] .here { display:block; }
.timer { margin-top:12px; }
.timer .clock { font-size:2.2rem; font-weight:800; font-variant-numeric:tabular-nums; }
.timer .bar { height:8px; border-radius:8px; background:var(--line); overflow:hidden; margin-top:6px; }
.timer .bar i { display:block; height:100%; width:0; background:var(--accent); transition:width 1s linear; }
.skip { display:inline-block; margin:10px 16px 0 0; font-size:.95rem; }
.flow-head { margin-top:6px; }
.inapp-help { margin-top:12px; font-size:.9rem; color:var(--dim); }
.inapp-help .row { display:flex; gap:8px; margin-top:8px; }
.inapp-help .button { flex:1; margin-top:0; padding:10px; font-size:.95rem; }
.inapp-help.detected { color:var(--text); border-left:3px solid var(--accent); padding-left:10px; }
"""

GUIDED_SCRIPT = """
<script>
(function () {
  var WAIT = 5 * 60 * 1000, KEY = "wp-steps-%(id)s";
  var ua = navigator.userAgent || "";
  if (/iphone|ipad|ipod/i.test(ua)) document.getElementById("ios-note").style.display = "block";
  var load = function () { try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { return {}; } };
  var save = function (s) { try { localStorage.setItem(KEY, JSON.stringify(s)); } catch (e) {} };
  var st = load();
  var set = function (id, state) { document.getElementById(id).setAttribute("data-state", state); };
  var timer, last;
  function render() {
    var left = st.joined ? Math.max(0, st.joined + WAIT - Date.now()) : WAIT;
    var step = st.got ? 4 : !st.joined ? 1 : left > 0 ? 2 : 3;
    ["g1", "g2", "g3", "g4"].forEach(function (id, i) {
      set(id, i + 1 < step ? "done" : i + 1 === step ? "now" : "later");
    });
    document.getElementById("g-skip").style.display = step === 1 ? "inline-block" : "none";
    document.getElementById("g-reset").style.display = step > 1 ? "inline-block" : "none";
    document.getElementById("g-timer").style.display = step === 2 ? "block" : "none";
    if (step === 2) {
      var sec = Math.ceil(left / 1000);
      document.getElementById("g-clock").textContent = Math.floor(sec / 60) + ":" + ("0" + (sec %% 60)).slice(-2);
      document.getElementById("g-bar").style.width = (100 - (left / WAIT) * 100) + "%%";
      if (!timer) timer = setInterval(render, 1000);
    } else if (timer) { clearInterval(timer); timer = null; }
    // Moving on to a new step: bring it into view.
    if (last && last !== step) document.getElementById("g" + step).scrollIntoView({ behavior: "smooth", block: "center" });
    last = step;
  }
  document.getElementById("g-join").addEventListener("click", function () {
    if (!st.joined) { st.joined = Date.now(); save(st); }
    setTimeout(render, 300);
  });
  document.getElementById("g-get").addEventListener("click", function () {
    if (!st.joined) st.joined = Date.now() - WAIT;
    st.got = Date.now(); save(st); setTimeout(render, 300);
  });
  document.getElementById("g-skip").addEventListener("click", function (e) {
    e.preventDefault(); st.joined = Date.now() - WAIT; save(st); render();
  });
  document.getElementById("g-reset").addEventListener("click", function (e) {
    e.preventDefault(); st = {}; save(st); render();
  });
  document.addEventListener("visibilitychange", function () { if (!document.hidden) render(); });

  // Inside TikTok / Instagram / Facebook: Google sign-in (joining the group)
  // doesn't work there. Keep where the visit came from (?src=, which survives
  // the move), send the step buttons to the real browser on Android, and offer
  // Open in browser. The plain how-to and Copy link show for everyone, in case
  // the in-app browser isn't recognised.
  var inapp = /musical_ly|BytedanceWebview|TikTok|Instagram|FBAN|FBAV|FB_IAB/i.test(ua);
  var q = new URLSearchParams(location.search);
  if (inapp && !q.get("src")) {
    q.set("src", q.get("ttclid") ? "tiktok_ad" : q.get("fbclid") ? "facebook_ad"
      : /Instagram/i.test(ua) ? "instagram" : /FBAN|FBAV|FB_IAB/i.test(ua) ? "facebook" : "tiktok");
    try { history.replaceState(null, "", location.pathname + "?" + q.toString() + location.hash); } catch (e) {}
  }
  var toBrowser = function (href) { return "intent://" + href.replace(/^https?:\/\//, "") + "#Intent;scheme=https;end"; };
  if (inapp) {
    document.getElementById("inapp-help").className += " detected";
    if (/android/i.test(ua)) {
      var ob = document.getElementById("open-browser");
      ob.style.display = "block";
      ob.href = toBrowser(location.href);
      ["g-join", "g-get"].forEach(function (id) { var a = document.getElementById(id); a.href = toBrowser(a.href); });
    }
  }
  var copy = document.getElementById("copy-link");
  copy.addEventListener("click", function (e) {
    e.preventDefault();
    var url = location.href;
    var done = function () { copy.textContent = "Copied! Paste it in your browser"; };
    var fallback = function () { window.prompt("Copy this link:", url); };
    try { navigator.clipboard.writeText(url).then(done, fallback); } catch (err) { fallback(); }
  });
  render();
})();
</script>"""


def guided_steps(app, name, group, test, link):
    track = bool(app.get("track_url"))
    t = lambda event: f' data-track="{event}"' if track else ""
    after = html.escape(app.get("after_install", f"Open {app['name']} and sign in."))
    return f"""
<style>{GUIDED_STYLE}</style>
<div id="ios-note" class="short" style="display:none;border-color:var(--accent)">&#128241; <b>{name} is
Android only for now.</b> Open this page on an Android phone to join.</div>
<div class="flow-head">Get it in 4 steps</div>
<div class="dim">About 10 minutes, on your Android phone.</div>

<div class="gstep" id="g1" data-state="now"><div class="num">1</div><div class="gbody">
<div class="here">DO THIS NOW</div>
<div class="gtitle">Join the testers</div>
<div class="gtext">Tap the button. On the page that opens, tap <b>Join group</b>. Then come back to this page.</div>
<a class="button" id="g-join" href="{group}"{t("join")}>Join testers</a>
<div class="inapp-help" id="inapp-help"><b>In TikTok, Instagram or Facebook?</b> Joining only works in your
browser: tap <b>&hellip;</b> or <b>&#8942;</b> at the top right, then <b>Open in browser</b>.
<div class="row"><a class="button" id="open-browser" href="#" style="display:none"{t("open_browser")}>Open in browser</a>
<a class="button secondary" id="copy-link" href="#"{t("copy_link")}>Copy link</a></div>
<div style="margin-top:6px;word-break:break-all">{link}</div></div></div></div>

<div class="gstep" id="g2" data-state="later"><div class="num">2</div><div class="gbody">
<div class="here">DO THIS NOW</div>
<div class="gtitle">Wait 5 minutes &#9203;</div>
<div class="gtext">Google is adding you to the testers. Stay on this page or come back later: it remembers where you are.</div>
<div class="timer" id="g-timer" style="display:none"><div class="clock" id="g-clock">5:00</div>
<div class="bar"><i id="g-bar"></i></div></div></div></div>

<div class="gstep" id="g3" data-state="later"><div class="num">3</div><div class="gbody">
<div class="here">DO THIS NOW</div>
<div class="gtitle">Get the app</div>
<div class="gtext">Tap the button, then tap <b>Become a tester</b>, then <b>Download it on Google Play</b>.
If it says you&#39;re not a tester, wait a few more minutes and try again.</div>
<a class="button" id="g-get" href="{test}"{t("get")}>Get {name}</a></div></div>

<div class="gstep" id="g4" data-state="later"><div class="num">4</div><div class="gbody">
<div class="here">DO THIS NOW</div>
<div class="gtitle">Open it and sign in</div>
<div class="gtext">{after}</div></div></div>

<a href="#" class="skip" id="g-skip">Already joined the testers before? Skip to step 3</a>
<a href="#" class="skip" id="g-reset">Start over</a>
<p class="dim">Your Play Store must use the same Google account you joined with. Please keep the app
installed for two weeks: Google counts testers before the public release.</p>
{GUIDED_SCRIPT % {"id": app["id"]}}"""


def promo_box(promo):
    """Bonus reminder: {"code": "...", "text": "..."} in apps.json."""
    return f"""
<div class="short" style="text-align:center">&#127873; {html.escape(promo['text'])}
<div style="margin:12px auto 4px;display:inline-block;padding:10px 22px;border:2px dashed var(--accent);
border-radius:12px;font-size:1.5rem;font-weight:800;letter-spacing:.06em">{html.escape(promo['code'])}</div>
<div class="dim">{html.escape(promo.get('where', ''))}</div></div>"""


def app_page(app, data):
    play = f"https://play.google.com/store/apps/details?id={app['package']}"
    name = html.escape(app["name"])
    if app["status"] == "testing" and app.get("guided_steps"):
        how = guided_steps(app, name, f"https://groups.google.com/g/{data['testers_group']}",
                           f"https://play.google.com/apps/testing/{app['package']}",
                           SITE.split('//')[1] + app['id'])
    elif app["status"] == "testing":
        group = f"https://groups.google.com/g/{data['testers_group']}"
        test = f"https://play.google.com/apps/testing/{app['package']}"
        how = f"""
<p>{name} is in testing on Google Play. Two taps on your Android phone, with
the same Google account as your Play Store:</p>
<div class="step"><span class="n">1.</span> Join the testers (once; it covers every wonderperk app).
<a class="button" href="{group}"{' data-track="join"' if app.get('track_url') else ''}>Join testers</a></div>{WAIT_TIP if app.get('wait_tip') else ''}
<div class="step"><span class="n">2.</span> Tap <b>Become a tester</b>, then <b>Download it on Google Play</b>.
<a class="button" href="{test}"{' data-track="get"' if app.get('track_url') else ''}>Get {name}</a></div>
<p class="dim">Just joined? Step 2 can take a few minutes to recognise you.
Please keep the app installed for two weeks: Google counts testers before the
public release.</p>"""
    else:
        how = f'<a class="button" href="{play}">Get it on Google Play</a>'
    if app.get("guided_steps") and app["status"] == "testing":
        # The app, then the first step, all without scrolling on a phone; the
        # in-app-browser help lives under step 1, the bonus after the steps.
        body = f"""
<div class="hero" style="margin:0 0 12px;gap:16px"><img src="icon.png" alt="" style="width:72px;height:72px;border-radius:18px">
<div><h1 style="font-size:1.7rem">{name}</h1><div class="dim">{html.escape(app['tagline'])}</div></div></div>
<p style="margin:0">{html.escape(app['about'])}</p>
{how}
{promo_box(app['promo']) + chr(10) if app.get('promo') else ''}<h2>More</h2>
<p><a href="privacy/">Privacy policy</a>{extra_links(app)} &middot; Contact: <a href="mailto:{data['contact']}">{data['contact']}</a></p>"""
        if app.get("track_url"):
            body += TRACK % {"url": app["track_url"], "app": app["id"]}
        return page(f"{app['name']} by wonderperk", app["tagline"], body, 1, app.get("accent", "#e0a36a"))
    body = f"""
{INAPP_TIP.replace('%LINK%', SITE.split('//')[1] + app['id']) + chr(10) if app.get('inapp_tip') else ''}<div class="hero"><img src="icon.png" alt="">
<div><h1>{name}</h1><div class="dim">{html.escape(app['tagline'])}</div></div></div>
<p>{html.escape(app['about'])}</p>
{promo_box(app['promo']) + chr(10) if app.get('promo') else ''}{how}
<h2>More</h2>
<p><a href="privacy/">Privacy policy</a>{extra_links(app)} &middot; Contact: <a href="mailto:{data['contact']}">{data['contact']}</a></p>"""
    if app.get("track_url"):
        body += TRACK % {"url": app["track_url"], "app": app["id"]}
    return page(f"{app['name']} by wonderperk", app["tagline"], body, 1, app.get("accent", "#e0a36a"))


def privacy_page(app):
    text = (ROOT / app["privacy"]).read_text(encoding="utf-8")
    body = f"""<h1>{html.escape(app['name'])}: Privacy Policy</h1>
<p class="dim">Last updated {html.escape(app['privacy_updated'])}</p>
{text}"""
    return page(f"{app['name']} Privacy Policy", f"Privacy policy for {app['name']}.", body, 2,
                app.get("accent", "#e0a36a"))


# Optional extra pages: apps.json key -> (folder under <id>/, link label, page title).
# Each key's value is the HTML body file; "<key>_updated" sets its date
# (defaults to the privacy policy's).
EXTRA_PAGES = {
    "terms": ("terms", "Terms of service", "Terms of Service"),
    "delete_account": ("delete-account", "Delete your account", "Delete your account"),
    "child_safety": ("child-safety", "Child safety", "Child Safety Standards"),
}


def extra_page(app, key):
    _, _, title = EXTRA_PAGES[key]
    text = (ROOT / app[key]).read_text(encoding="utf-8")
    updated = app.get(f"{key}_updated", app["privacy_updated"])
    body = f"""<h1>{html.escape(app['name'])}: {html.escape(title)}</h1>
<p class="dim">Last updated {html.escape(updated)}</p>
{text}"""
    return page(f"{app['name']} {title}", f"{title} for {app['name']}.", body, 2,
                app.get("accent", "#e0a36a"))


def extra_links(app):
    return "".join(f' &middot; <a href="{folder}/">{label}</a>'
                   for key, (folder, label, _) in EXTRA_PAGES.items() if app.get(key))


def index_page(data):
    cards = []
    for app in data["apps"]:
        badge = "Testing" if app["status"] == "testing" else "On Google Play"
        cards.append(f"""<a class="card" href="{app['id']}/"><img src="{app['icon']}" alt="">
<div><b>{html.escape(app['name'])}</b><span class="badge">{badge}</span>
<div class="dim">{html.escape(app['tagline'])}</div></div></a>""")
    body = f"""<h1>wonderperk</h1>
<p class="dim">Games and apps by wonderperk. Want to try new ones before
anyone else? <a href="https://groups.google.com/g/{data['testers_group']}">Join the testers</a>.</p>
{''.join(cards)}"""
    return page("wonderperk apps", "Games and apps by wonderperk.", body, 0)


def main():
    data = json.loads((ROOT / "apps.json").read_text(encoding="utf-8"))
    (ROOT / "index.html").write_text(index_page(data), encoding="utf-8")
    for app in data["apps"]:
        folder = ROOT / app["id"]
        (folder / "privacy").mkdir(parents=True, exist_ok=True)
        (folder / "index.html").write_text(app_page(app, data), encoding="utf-8")
        (folder / "privacy" / "index.html").write_text(privacy_page(app), encoding="utf-8")
        for key, (slug, _, _) in EXTRA_PAGES.items():
            if app.get(key):
                (folder / slug).mkdir(exist_ok=True)
                (folder / slug / "index.html").write_text(extra_page(app, key), encoding="utf-8")
        print(f"built {app['id']}/ ({app['status']})")
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")


if __name__ == "__main__":
    main()
