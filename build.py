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
<div id="inapp" class="step" style="display:none;border-color:var(--accent)">
<b>Opened from TikTok, Instagram or Facebook?</b> Open this page in your
browser first, or joining the testers won't work.
<a class="button" id="open-browser" href="#">Open in browser</a>
<p class="dim">Button not working? Tap <b>&#8942;</b> or <b>&hellip;</b> at the top right and choose
<b>Open in browser</b>.</p></div>
<script>
(function () {
  var ua = navigator.userAgent || "";
  if (!/musical_ly|BytedanceWebview|TikTok|Instagram|FBAN|FBAV|FB_IAB/i.test(ua)) return;
  document.getElementById("inapp").style.display = "block";
  var url = location.href.replace(/^https?:\/\//, "");
  // No package: Android hands it to the person's default browser.
  document.getElementById("open-browser").href = "intent://" + url + "#Intent;scheme=https;end";
})();
</script>"""


# Between steps 1 and 2: Google needs a few minutes to add a new group member
# to the test. Opt in per app: "wait_tip": true.
WAIT_TIP = """
<div class="short" style="border-style:dashed;text-align:center">&#9203; <b>Wait about 5&ndash;10 minutes</b>
before step 2. Google takes a little while to add you to the testers. If step 2
says you&#39;re not a tester yet, wait a bit longer and try again.</div>"""


def app_page(app, data):
    play = f"https://play.google.com/store/apps/details?id={app['package']}"
    name = html.escape(app["name"])
    if app["status"] == "testing":
        group = f"https://groups.google.com/g/{data['testers_group']}"
        test = f"https://play.google.com/apps/testing/{app['package']}"
        how = f"""
<p>{name} is in testing on Google Play. Two taps on your Android phone, with
the same Google account as your Play Store:</p>
<div class="step"><span class="n">1.</span> Join the testers (once; it covers every wonderperk app).
<a class="button" href="{group}">Join testers</a></div>{WAIT_TIP if app.get('wait_tip') else ''}
<div class="step"><span class="n">2.</span> Tap <b>Become a tester</b>, then <b>Download it on Google Play</b>.
<a class="button" href="{test}">Get {name}</a></div>
<p class="dim">Just joined? Step 2 can take a few minutes to recognise you.
Please keep the app installed for two weeks: Google counts testers before the
public release.</p>"""
    else:
        how = f'<a class="button" href="{play}">Get it on Google Play</a>'
    body = f"""
{INAPP_TIP + chr(10) if app.get('inapp_tip') else ''}<div class="hero"><img src="icon.png" alt="">
<div><h1>{name}</h1><div class="dim">{html.escape(app['tagline'])}</div></div></div>
<p>{html.escape(app['about'])}</p>
{how}
<h2>More</h2>
<p><a href="privacy/">Privacy policy</a>{extra_links(app)} &middot; Contact: <a href="mailto:{data['contact']}">{data['contact']}</a></p>"""
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
