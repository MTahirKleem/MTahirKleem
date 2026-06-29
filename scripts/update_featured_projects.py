import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request


USERNAME = os.getenv("GITHUB_USERNAME", "MTahirKleem")
TOKEN = os.getenv("GH_TOKEN", "")
README_FILE = "README.md"

MAX_REPOS = 4
SORT_MODE = "created"

START_MARKER = "<!-- FEATURED-PROJECTS:START -->"
END_MARKER = "<!-- FEATURED-PROJECTS:END -->"

EXCLUDED_REPOS = {
    USERNAME.lower(),
    ".github",
}


LANGUAGE_COLORS = {
    "Python": "3776AB",
    "TypeScript": "3178C6",
    "JavaScript": "F7DF1E",
    "HTML": "E34F26",
    "CSS": "1572B6",
    "Java": "007396",
    "C++": "00599C",
    "C": "A8B9CC",
    "Go": "00ADD8",
    "Rust": "000000",
    "PHP": "777BB4",
    "Dart": "0175C2",
    "Kotlin": "7F52FF",
    "Swift": "FA7343",
    "Shell": "4EAA25",
}


def github_request(url):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "featured-projects-readme-updater",
    }

    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    request = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def clean_text(value, fallback="Not provided"):
    if not value:
        return fallback

    return html.escape(str(value).strip())


def badge_url(label, message, color="111111", logo=None, logo_color="white", style="flat-square"):
    query = {
        "style": style,
        "label": label,
        "message": message,
        "color": color,
    }

    if logo:
        query["logo"] = logo
        query["logoColor"] = logo_color

    return "https://img.shields.io/static/v1?" + urllib.parse.urlencode(query)


def language_badge(language):
    if not language:
        return ""

    color = LANGUAGE_COLORS.get(language, "6c757d")
    logo = language.lower().replace("++", "plusplus").replace("#", "sharp").replace(" ", "")

    return f'<img src="{badge_url("Code", language, color, logo)}" alt="{html.escape(language)}"/>'


def topic_badges(repo):
    topics = repo.get("topics", [])[:3]
    badges = []

    for topic in topics:
        safe_topic = str(topic).replace("-", " ")
        badges.append(
            f'<img src="{badge_url("Topic", safe_topic, "1a0533")}" alt="{html.escape(str(topic))}"/>'
        )

    return " ".join(badges)


def repo_description(repo):
    description = repo.get("description")

    if description:
        return clean_text(description)

    language = repo.get("language")

    if language:
        return f"A public {html.escape(language)} project from my GitHub workspace."

    return "A public project from my GitHub workspace, updated automatically from GitHub."


def repo_card(repo):
    name = clean_text(repo.get("name"), "Repository")
    url = clean_text(repo.get("html_url"), "#")
    description = repo_description(repo)
    language = repo.get("language")
    homepage = repo.get("homepage")

    encoded_repo = urllib.parse.quote(repo.get("name", ""), safe="")
    encoded_user = urllib.parse.quote(USERNAME, safe="")

    language_html = language_badge(language)
    topics_html = topic_badges(repo)

    repo_button = (
        f'<a href="{url}">'
        f'<img src="https://img.shields.io/badge/View_Repository-111111?style=for-the-badge&logo=github&logoColor=white" alt="View Repository"/>'
        f'</a>'
    )

    live_button = ""

    if homepage and str(homepage).startswith(("http://", "https://")):
        live_button = (
            f' <a href="{html.escape(str(homepage))}">'
            f'<img src="https://img.shields.io/badge/Live_Demo-ff2d55?style=for-the-badge&logo=vercel&logoColor=white" alt="Live Demo"/>'
            f'</a>'
        )

    return f"""
<td width="50%" valign="top">

<h3>
<a href="{url}">{name}</a>
</h3>

<p>{description}</p>

<p>
{language_html}
{topics_html}
</p>

<p>
<img src="https://img.shields.io/github/stars/{encoded_user}/{encoded_repo}?style=flat-square&color=ff2d55&label=Stars" alt="Stars"/>
<img src="https://img.shields.io/github/forks/{encoded_user}/{encoded_repo}?style=flat-square&color=7c3aed&label=Forks" alt="Forks"/>
<img src="https://img.shields.io/github/last-commit/{encoded_user}/{encoded_repo}?style=flat-square&color=0ea5e9&label=Updated" alt="Last Commit"/>
</p>

<p>
{repo_button}{live_button}
</p>

</td>
""".strip()


def generate_projects_section(repos):
    cards = [repo_card(repo) for repo in repos]

    if not cards:
        return f"{START_MARKER}\nNo public repositories found.\n{END_MARKER}"

    rows = []

    for index in range(0, len(cards), 2):
        first = cards[index]
        second = cards[index + 1] if index + 1 < len(cards) else '<td width="50%"></td>'
        rows.append(f"<tr>\n{first}\n{second}\n</tr>")

    section = f"""
<div align="center">

<table>
{"".join(rows)}
</table>

</div>
""".strip()

    return f"{START_MARKER}\n{section}\n{END_MARKER}"


def fetch_public_repos():
    url = (
        f"https://api.github.com/users/{USERNAME}/repos"
        f"?type=owner&sort={SORT_MODE}&direction=desc&per_page=100"
    )

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


def update_readme(projects_section):
    if not os.path.exists(README_FILE):
        print(f"{README_FILE} not found.")
        sys.exit(1)

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


def main():
    repos = fetch_public_repos()
    projects_section = generate_projects_section(repos)
    update_readme(projects_section)
    print(f"Updated Featured Projects with {len(repos)} repositories.")


if __name__ == "__main__":
    main()