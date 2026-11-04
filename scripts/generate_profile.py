#!/usr/bin/env python3
"""Generate the LIVE parts of the profile from real GitHub data.

Writes:
  assets/generated/{stats,langs,activity,snake-dark,snake-light}.svg   self-generated cards (no third-party services)
  assets/generated/data.json                             the data the cards were drawn from
  README.md                                              rendered from README.template.md + featured.yml

Data comes from the GitHub REST + GraphQL APIs (GITHUB_TOKEN). If GraphQL is unavailable the contribution
calendar falls back to the public calendar page. If a critical request fails the script exits non-zero
WITHOUT touching any file, so a bad run never overwrites good cards with zeros.

    python scripts/generate_profile.py                # normal run (needs GITHUB_TOKEN for good rate limits)
    python scripts/generate_profile.py --data-file d.json   # render from a saved data file, no network
"""
import argparse, datetime as dt, hashlib, html, json, os, re, sys, time
import urllib.error, urllib.parse, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yaml
from common import USER
import cards
import snake

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "assets" / "generated"
API = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
GRAPHQL = os.environ.get("GITHUB_GRAPHQL_URL", API + "/graphql")
WEB = os.environ.get("PROFILE_WEB_URL", "https://github.com").rstrip("/")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
LOGIN = os.environ.get("PROFILE_USER") or USER


class ApiError(RuntimeError):
    pass


def http(url, data=None, accept="application/vnd.github+json", retries=3, auth=True):
    headers = {"User-Agent": "profile-readme-generator", "Accept": accept, "X-GitHub-Api-Version": "2022-11-28"}
    if TOKEN and auth:
        headers["Authorization"] = f"Bearer {TOKEN}"
    if data is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(data).encode()
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data, headers), timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:300]
            if e.code in (500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(2 * (attempt + 1)); continue
            raise ApiError(f"HTTP {e.code} for {url}: {body}")
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < retries - 1:
                time.sleep(2 * (attempt + 1)); continue
            raise ApiError(f"Network error for {url}: {e}")


def rest(path, **kw):
    return json.loads(http(f"{API}{path}", **kw))


def paged(path):
    out, page = [], 1
    while True:
        sep = "&" if "?" in path else "?"
        chunk = rest(f"{path}{sep}per_page=100&page={page}")
        out += chunk
        if len(chunk) < 100:
            return out
        page += 1


# --------------------------------------------------------------------------- config
def _names(x):
    return [str(n).strip().lower() for n in (x or []) if str(n).strip()]


def load_config():
    p = ROOT / "featured.yml"
    cfg = yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {}
    cfg = cfg or {}
    feats = []                                             # optional pinned projects (shown first, in this order)
    for e in cfg.get("featured") or []:
        if isinstance(e, str):
            feats.append({"name": e.strip(), "enabled": True, "description": ""})
        elif isinstance(e, dict) and e.get("name"):
            feats.append({"name": str(e["name"]).strip(), "enabled": e.get("enabled", True) is not False,
                          "description": (e.get("description") or "").strip()})
    return {
        "auto": cfg.get("auto_detect", True) is not False,
        "featured": feats,
        "hidden": _names(cfg.get("hidden")),
        "hide_topic": str(cfg.get("hide_topic") or "hide-from-profile").strip().lower(),
        "forks": bool(cfg.get("include_forks", False)),
        "archived": bool(cfg.get("include_archived", False)),
        "max": int(cfg.get("max_projects") or 6),
        "exclude_langs": [str(x).lower() for x in (cfg.get("exclude_from_language_stats") if "exclude_from_language_stats" in cfg else [LOGIN])],
    }


# --------------------------------------------------------------------------- contribution calendar
GQL = """query($login:String!){user(login:$login){contributionsCollection{
totalCommitContributions totalIssueContributions totalPullRequestContributions
contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}"""


def contributions_graphql():
    res = json.loads(http(GRAPHQL, data={"query": GQL, "variables": {"login": LOGIN}}))
    if res.get("errors") or not res.get("data", {}).get("user"):
        raise ApiError(f"GraphQL: {res.get('errors')}")
    cc = res["data"]["user"]["contributionsCollection"]
    days = [{"date": d["date"], "count": d["contributionCount"]}
            for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    days.sort(key=lambda d: d["date"])
    return days


def contributions_scrape():
    page = http(f"{WEB}/users/{LOGIN}/contributions", accept="text/html", auth=False)
    tips = {}
    for m in re.finditer(r'<tool-tip\b[^>]*?\bfor="([^"]+)"[^>]*>\s*([^<]*?)\s*</tool-tip>', page):
        tips[m.group(1)] = m.group(2)
    levels = {0: 0, 1: 1, 2: 3, 3: 6, 4: 10}
    days = []
    for m in re.finditer(r"<td\b[^>]*ContributionCalendar-day[^>]*>", page):
        tag = m.group(0)
        date = re.search(r'data-date="([\d-]+)"', tag)
        if not date:
            continue
        tid = re.search(r'\bid="([^"]+)"', tag)
        tip = tips.get(tid.group(1)) if tid else None
        if tip is not None:
            n = re.match(r"(\d[\d,]*)", tip)
            count = int(n.group(1).replace(",", "")) if n else 0
        else:
            lv = re.search(r'data-level="(\d)"', tag)
            count = levels[int(lv.group(1))] if lv else 0
        days.append({"date": date.group(1), "count": count})
    if not days:
        raise ApiError("Could not read the public contribution calendar")
    days.sort(key=lambda d: d["date"])
    return days


# --------------------------------------------------------------------------- collection
def collect(prev):
    u = rest(f"/users/{LOGIN}")
    repos = [r for r in paged(f"/users/{LOGIN}/repos?type=owner&sort=pushed") if not r.get("private")]
    try:
        days = contributions_graphql() if TOKEN else contributions_scrape()
    except ApiError as e:
        print(f"! GraphQL contributions failed ({e}); falling back to the public calendar page", file=sys.stderr)
        days = contributions_scrape()

    def search(q, key):
        try:
            return rest("/search/issues?" + urllib.parse.urlencode({"q": q, "per_page": 1}))["total_count"]
        except ApiError as e:
            print(f"! search {key} failed ({e}); keeping previous value", file=sys.stderr)
            return prev.get(key, 0)

    cfg = load_config()
    langs, failed = {}, False
    for r in repos:
        if r["fork"] or r["name"].lower() in cfg["exclude_langs"] or r["full_name"].lower() in cfg["exclude_langs"]:
            continue
        try:
            for k, v in rest(f"/repos/{r['full_name']}/languages").items():
                langs[k] = langs.get(k, 0) + v
        except ApiError as e:
            failed = True
            print(f"! languages for {r['full_name']} failed: {e}", file=sys.stderr)
    if failed and prev.get("languages"):
        langs = prev["languages"]

    created = u.get("created_at")
    return {
        "user": LOGIN, "name": u.get("name"), "created_at": created,
        "followers": u["followers"], "following": u["following"], "public_repos": u["public_repos"],
        "stars_earned": sum(r["stargazers_count"] for r in repos if not r["fork"]),
        "prs": search(f"author:{LOGIN} type:pr is:public", "prs"),
        "issues": search(f"author:{LOGIN} type:issue is:public", "issues"),
        "languages": langs, "contrib_days": days,
        "repos": [{k: r.get(k) for k in ("name", "full_name", "html_url", "description", "fork", "archived", "stargazers_count",
                                          "forks_count", "language", "topics", "pushed_at", "private")} for r in repos],
    }


def finalize(d):
    d["generated_at"] = d.get("generated_at") or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    d["contrib_total"] = sum(c["count"] for c in d["contrib_days"])
    d["lang_count"] = sum(1 for v in d["languages"].values() if v > 0)
    ca = d.get("created_at")
    if ca:
        c = dt.datetime.fromisoformat(ca.replace("Z", "+00:00"))
        now = dt.datetime.now(dt.timezone.utc)
        d["joined_year"] = c.year
        d["years"] = max(0, (now - c).days // 365)
    else:
        d["joined_year"], d["years"] = None, 0
    return d


# --------------------------------------------------------------------------- featured projects
def clean_sentence(text, limit=150):
    t = re.sub(r"\s+", " ", text or "").strip()
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)          # markdown links -> text
    t = re.sub(r"[*_`]+", "", t).strip(" -–—:;")
    if not t:
        return ""
    m = re.match(r"(.+?[.!?])(\s|$)", t)                      # keep only the first sentence
    if m:
        t = m.group(1)
    t = t[0].upper() + t[1:]
    if len(t) > limit:
        t = t[:limit].rsplit(" ", 1)[0].rstrip(",;:-") + "…"
        return t
    return t if t[-1] in ".!?…" else t + "."


def readme_lead(full_name):
    try:
        raw = http(f"{API}/repos/{full_name}/readme", accept="application/vnd.github.raw")
    except ApiError:
        return ""
    in_code = False
    for line in raw.splitlines():
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code; continue
        if in_code or not s or s.startswith(("#", "!", "[![", "<", "|", ">", "---", "===", "- ", "* ", "+ ")):
            continue
        plain = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
        if len(plain.split()) >= 4 and len(plain) >= 25:
            return plain
    return ""


def describe(repo, override=""):
    """One sentence built ONLY from real repository information (override > description > README > topics/language)."""
    if override:
        return clean_sentence(override, 200)
    s = clean_sentence(repo.get("description") or "")
    if s:
        return s
    s = clean_sentence(readme_lead(repo["full_name"]))
    if s:
        return s
    topics = [t.replace("-", " ") for t in (repo.get("topics") or [])][:3]
    lang = repo.get("language")
    if topics:
        listed = topics[0] if len(topics) == 1 else ", ".join(topics[:-1]) + " and " + topics[-1]
        return f"A project on {listed}" + (f", written in {lang}." if lang else ".")
    if lang:
        return f"A repository written in {lang}."
    return "A public repository."


def pick_projects(cfg, repos):
    """Pinned entries first (in featured.yml order), then every other public repo found automatically, newest push first.
    A repo is left out if it is in `hidden:`, is toggled off (enabled: false), carries the hide topic, is the profile
    repo itself, is a fork / archived (unless allowed), or is empty."""
    by_name = {r["name"].lower(): r for r in repos}
    off = set(cfg["hidden"]) | {e["name"].rpartition("/")[2].lower() for e in cfg["featured"] if not e["enabled"]}
    off.add(LOGIN.lower())                                  # never feature the profile repo itself

    def allowed(r):
        if r.get("private") or r["name"].lower() in off:
            return False
        if cfg["hide_topic"] in [t.lower() for t in (r.get("topics") or [])]:
            return False
        return True

    chosen, seen = [], set()
    for e in cfg["featured"]:                               # 1) pinned
        if not e["enabled"]:
            continue
        owner, _, rname = e["name"].rpartition("/")
        key = rname.lower()
        if key in seen:
            continue
        r = by_name.get(key) if (not owner or owner.lower() == LOGIN.lower()) else None
        if r is None:
            try:
                r = rest(f"/repos/{owner or LOGIN}/{rname}")
            except ApiError:
                print(f"! pinned repo '{e['name']}' not found — skipped", file=sys.stderr); continue
        if r.get("private"):
            print(f"! pinned repo '{e['name']}' is private — skipped (this README is public)", file=sys.stderr); continue
        seen.add(key)
        chosen.append((r, e.get("description", "")))
    if cfg["auto"]:                                         # 2) auto-detected
        rest_repos = sorted(repos, key=lambda r: r.get("pushed_at") or "", reverse=True)
        for r in rest_repos:
            key = r["name"].lower()
            if key in seen or not allowed(r):
                continue
            if (r.get("fork") and not cfg["forks"]) or (r.get("archived") and not cfg["archived"]):
                continue
            seen.add(key)
            chosen.append((r, ""))
    return chosen[:cfg["max"]]


def featured_html(cfg, repos):
    chosen = pick_projects(cfg, repos)
    if not chosen:
        return ('<p align="center"><sub>Projects appear here automatically as soon as a public repository is published.</sub></p>')
    cells = []
    for r, ov in chosen:
        pushed = ""
        if r.get("pushed_at"):
            pushed = dt.datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00")).strftime("%b %Y")
        meta = " · ".join(x for x in [r.get("language") or "", f"★ {r.get('stargazers_count', 0)}",
                                      f"updated {pushed}" if pushed else "", "archived" if r.get("archived") else ""] if x)
        cells.append(f'<td width="50%" valign="top"><a href="{html.escape(r["html_url"])}"><b>{html.escape(r["name"])}</b></a><br>'
                     f'{html.escape(describe(r, ov))}<br><sub>{html.escape(meta)}</sub></td>')
    rows = ["<tr>" + "".join(cells[i:i + 2]) + ("<td></td>" if len(cells[i:i + 2]) == 1 else "") + "</tr>" for i in range(0, len(cells), 2)]
    return '<table align="center" width="100%">' + "".join(rows) + "</table>"


# --------------------------------------------------------------------------- output
def sha(path):
    p = ROOT / path
    return hashlib.sha1(p.read_bytes()).hexdigest()[:8] if p.exists() else "0"


def render_readme(featured):
    repo = os.environ.get("GITHUB_REPOSITORY") or f"{LOGIN}/{LOGIN}"
    branch = os.environ.get("PROFILE_BRANCH") or os.environ.get("GITHUB_REF_NAME") or "main"
    if "/" in branch or branch.endswith("merge"):
        branch = "main"
    raw = f"https://raw.githubusercontent.com/{repo}/{branch}"
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    t = (ROOT / "README.template.md").read_text(encoding="utf-8")
    t = re.sub(r"\{\{asset:([^}]+)\}\}", lambda m: f"{raw}/{m.group(1)}?v={sha(m.group(1))}", t)
    t = re.sub(r"\{\{snake:(light|dark)\}\}", lambda m: f"https://raw.githubusercontent.com/{repo}/output/github-snake{'-dark' if m.group(1)=='dark' else ''}.svg?v={today.replace('-','')}", t)
    return t.replace("{{featured_projects}}", featured).replace("{{updated}}", today).replace("{{username}}", LOGIN)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-file", help="render from a saved data.json instead of calling GitHub")
    ap.add_argument("--out-dir", help="write cards + README here instead of the repo (for testing)")
    a = ap.parse_args()
    prev = {}
    if (GEN / "data.json").exists():
        try:
            prev = json.loads((GEN / "data.json").read_text())
        except Exception:
            pass
    if a.data_file:
        d = json.loads(Path(a.data_file).read_text())
    else:
        d = collect(prev)
    d = finalize(d)
    cfg = load_config()
    featured = featured_html(cfg, d.get("repos", []))

    out = Path(a.out_dir) if a.out_dir else GEN
    out.mkdir(parents=True, exist_ok=True)
    for name, fn in [("stats", cards.stats_card), ("langs", cards.langs_card), ("activity", cards.activity_card)]:
        (out / f"{name}.svg").write_text(fn(d), encoding="utf-8")
    for mode in ("dark", "light"):
        (out / f"snake-{mode}.svg").write_text(snake.build_snake(d["contrib_days"], mode), encoding="utf-8")
    slim = {k: v for k, v in d.items() if k != "repos"}
    (out / "data.json").write_text(json.dumps(slim, indent=1), encoding="utf-8")
    readme = render_readme(featured)
    (Path(a.out_dir) / "README.md" if a.out_dir else ROOT / "README.md").write_text(readme, encoding="utf-8")
    print(f"OK  repos={d['public_repos']} stars={d['stars_earned']} followers={d['followers']} "
          f"contrib={d['contrib_total']} langs={d['lang_count']} featured_cfg={len(cfg['featured'])}")


if __name__ == "__main__":
    try:
        main()
    except ApiError as e:
        print(f"ERROR: {e}\nNo files were changed.", file=sys.stderr)
        sys.exit(1)
