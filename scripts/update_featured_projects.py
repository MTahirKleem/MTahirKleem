import html
import json
import os
import re
import sys
import urllib.request
from datetime import datetime

USERNAME = os.getenv("GITHUB_USERNAME", "MTahirKleem")
TOKEN = os.getenv("GH_TOKEN", "")
README_FILE = "README.md"

MAX_REPOS = 4
SORT_MODE = "created"  # created = newest repos appear first
EXCLUDED_REPOS = {
USERNAME.lower(),
".github",
}

START_MARKER = "<!-- FEATURED-PROJECTS:START -->"
END_MARKER = "<!-- FEATURED-PROJECTS:END -->"

def github_request(url):
headers = {
"Accept": "application/vnd.github+json",
"X-GitHub-Api-Version": "2022-11-28",
"User-Agent": "featured-projects-readme-updater",
}

```
if TOKEN:
    headers["Authorization"] = f"Bearer {TOKEN}"

request = urllib.request.Request(url, headers=headers)

with urllib.request.urlopen(request, timeout=30) as response:
    return json.loads(response.read().decode("utf-8"))
```

def clean_text(value, fallback="Not provided"):
if not value:
return fallback
return html.escape(str(value).strip())

def format_date(value):
if not value:
return "Unknown"

```
try:
    date = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    return date.strftime("%b %d, %Y")
except ValueError:
    return "Unknown"
```

def repo_tags(repo):
tags = []

```
language = repo.get("language")
if language:
    tags.append(language)

for topic in repo.get("topics", [])[:4]:
    tags.append(topic)

if not tags:
    tags.append("Project")

return " ".join(f"<code>{html.escape(tag)}</code>" for tag in tags[:5])
```

def repo_card(repo):
name = clean_text(repo.get("name"), "Repository")
description = clean_text(repo.get("description"), "No description provided.")
url = clean_text(repo.get("html_url"), "#")
homepage = repo.get("homepage")
stars = repo.get("stargazers_count", 0)
forks = repo.get("forks_count", 0)
updated = format_date(repo.get("updated_at"))
tags = repo_tags(repo)

```
links = f'<a href="{url}">Repository</a>'

if homepage and str(homepage).startswith(("http://", "https://")):
    links += f' · <a href="{html.escape(homepage)}">Live Demo</a>'

return f"""
```

<td width="50%" valign="top">

<h3><a href="{url}">{name}</a></h3>

<p>{description}</p>

<p>{tags}</p>

<p>
Stars: <b>{stars}</b> · Forks: <b>{forks}</b> · Updated: <b>{updated}</b>
</p>

<p>{links}</p>

</td>
""".strip()

def generate_projects_section(repos):
cards = [repo_card(repo) for repo in repos]

```
if not cards:
    return f"{START_MARKER}\nNo public repositories found.\n{END_MARKER}"

rows = []

for index in range(0, len(cards), 2):
    first = cards[index]
    second = cards[index + 1] if index + 1 < len(cards) else '<td width="50%"></td>'
    rows.append(f"<tr>\n{first}\n{second}\n</tr>")

table = "<table>\n" + "\n".join(rows) + "\n</table>"

return f"{START_MARKER}\n{table}\n{END_MARKER}"
```

def fetch_public_repos():
url = (
f"https://api.github.com/users/{USERNAME}/repos"
f"?type=owner&sort={SORT_MODE}&direction=desc&per_page=100"
)

```
repos = github_request(url)

filtered = []

for repo in repos:
    name = repo.get("name", "").lower()

    if name in EXCLUDED_REPOS:
        continue

    if repo.get("fork"):
        continue

    if repo.get("archived"):
        continue

    filtered.append(repo)

return filtered[:MAX_REPOS]
```

def update_readme(projects_section):
if not os.path.exists(README_FILE):
print(f"{README_FILE} not found.")
sys.exit(1)

```
with open(README_FILE, "r", encoding="utf-8") as file:
    readme = file.read()

pattern = re.compile(
    rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
    re.DOTALL,
)

if not pattern.search(readme):
    print("Featured projects markers not found in README.md.")
    sys.exit(1)

updated_readme = pattern.sub(projects_section, readme)

with open(README_FILE, "w", encoding="utf-8") as file:
    file.write(updated_readme)
```

def main():
repos = fetch_public_repos()
projects_section = generate_projects_section(repos)
update_readme(projects_section)
print(f"Updated Featured Projects with {len(repos)} repositories.")

if **name** == "**main**":
main()
