import os
import json
import urllib.request
from datetime import datetime, timedelta
from collections import Counter


USERNAME = "nathnaelashenafi"

TOKEN = os.environ.get("GITHUB_TOKEN")

API_HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": USERNAME,
}


def github_api(url):
    request = urllib.request.Request(
        url,
        headers=API_HEADERS
    )

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())


def graphql(query):
    data = json.dumps({"query": query}).encode()

    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=data,
        headers={
            **API_HEADERS,
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())


def escape(text):
    if not text:
        return ""

    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def svg_header(width, height):
    return f'''<svg xmlns="http://www.w3.org/2000/svg"
width="{width}"
height="{height}"
viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" rx="20"
fill="#051f20"/>
'''


def save_svg(filename, content):
    os.makedirs("profile", exist_ok=True)

    with open(
        f"profile/{filename}",
        "w",
        encoding="utf-8"
    ) as file:
        file.write(content)


# ---------------------------------------------------------
# USER INFORMATION
# ---------------------------------------------------------

user = github_api(
    f"https://api.github.com/users/{USERNAME}"
)

public_repos = user.get("public_repos", 0)
followers = user.get("followers", 0)
following = user.get("following", 0)


# ---------------------------------------------------------
# REPOSITORIES
# ---------------------------------------------------------

repositories = github_api(
    f"https://api.github.com/users/{USERNAME}/repos"
    "?per_page=100&sort=updated"
)

repositories = [
    repo
    for repo in repositories
    if not repo.get("fork", False)
]


total_stars = sum(
    repo.get("stargazers_count", 0)
    for repo in repositories
)

total_forks = sum(
    repo.get("forks_count", 0)
    for repo in repositories
)


# ---------------------------------------------------------
# LANGUAGES
# ---------------------------------------------------------

language_counter = Counter()

for repo in repositories:

    languages = github_api(
        repo["languages_url"]
    )

    for language, amount in languages.items():
        language_counter[language] += amount


languages = language_counter.most_common(8)


# ---------------------------------------------------------
# CONTRIBUTIONS
# ---------------------------------------------------------

query = f"""
query {{
  user(login: "{USERNAME}") {{
    contributionsCollection {{
      contributionCalendar {{
        totalContributions
        weeks {{
          contributionDays {{
            date
            contributionCount
            weekday
          }}
        }}
      }}
    }}
  }}
}}
"""


graphql_result = graphql(query)

calendar = (
    graphql_result["data"]["user"]
    ["contributionsCollection"]
    ["contributionCalendar"]
)

weeks = calendar["weeks"]

days = []

for week in weeks:
    for day in week["contributionDays"]:
        days.append(day)


# ---------------------------------------------------------
# STREAK CALCULATION
# ---------------------------------------------------------

contribution_dates = {
    day["date"]
    for day in days
    if day["contributionCount"] > 0
}


today = datetime.utcnow().date()


def calculate_current_streak():

    current = today

    if current.isoformat() not in contribution_dates:

        current -= timedelta(days=1)

        if current.isoformat() not in contribution_dates:
            return 0

    streak = 0

    while current.isoformat() in contribution_dates:

        streak += 1
        current -= timedelta(days=1)

    return streak


def calculate_longest_streak():

    longest = 0
    current = 0

    sorted_dates = sorted(
        contribution_dates
    )

    previous = None

    for date_string in sorted_dates:

        current_date = datetime.strptime(
            date_string,
            "%Y-%m-%d"
        ).date()

        if previous is not None:

            difference = (
                current_date - previous
            ).days

            if difference == 1:
                current += 1

            else:
                current = 1

        else:
            current = 1

        longest = max(
            longest,
            current
        )

        previous = current_date

    return longest


current_streak = calculate_current_streak()
longest_streak = calculate_longest_streak()

contribution_days = len(contribution_dates)

total_contributions = calendar[
    "totalContributions"
]


# ---------------------------------------------------------
# STATS SVG
# ---------------------------------------------------------

stats = svg_header(900, 300)

stats += f'''
<text x="50" y="55"
font-family="Arial"
font-size="26"
font-weight="bold"
fill="#daf1de">
GITHUB OVERVIEW
</text>

<text x="50" y="85"
font-family="Arial"
font-size="14"
fill="#8eb69b">
NATHNAEL ASHENAFI
</text>

<rect x="40" y="115" width="190" height="130"
rx="16" fill="#0b2b26"/>

<text x="60" y="150"
font-family="Arial"
font-size="14"
fill="#8eb69b">
PUBLIC REPOSITORIES
</text>

<text x="60" y="205"
font-family="Arial"
font-size="38"
font-weight="bold"
fill="#daf1de">
{public_repos}
</text>

<rect x="250" y="115" width="190" height="130"
rx="16" fill="#163832"/>

<text x="270" y="150"
font-family="Arial"
font-size="14"
fill="#8eb69b">
CONTRIBUTIONS
</text>

<text x="270" y="205"
font-family="Arial"
font-size="38"
font-weight="bold"
fill="#6ee7b7">
{total_contributions}
</text>

<rect x="460" y="115" width="190" height="130"
rx="16" fill="#0b2b26"/>

<text x="480" y="150"
font-family="Arial"
font-size="14"
fill="#8eb69b">
STARS
</text>

<text x="480" y="205"
font-family="Arial"
font-size="38"
font-weight="bold"
fill="#daf1de">
{total_stars}
</text>

<rect x="670" y="115" width="190" height="130"
rx="16" fill="#163832"/>

<text x="690" y="150"
font-family="Arial"
font-size="14"
fill="#8eb69b">
FOLLOWERS
</text>

<text x="690" y="205"
font-family="Arial"
font-size="38"
font-weight="bold"
fill="#6ee7b7">
{followers}
</text>
'''

stats += "</svg>"

save_svg(
    "stats.svg",
    stats
)


# ---------------------------------------------------------
# STREAK SVG
# ---------------------------------------------------------

streak = svg_header(1000, 330)

streak += f'''
<text x="50" y="55"
font-family="Arial"
font-size="27"
font-weight="bold"
fill="#daf1de">
CONTRIBUTION STREAK
</text>

<rect x="40" y="90"
width="280"
height="190"
rx="18"
fill="#0b2b26"/>

<text x="70" y="130"
font-family="Arial"
font-size="15"
fill="#8eb69b">
🔥 CURRENT STREAK
</text>

<text x="70" y="205"
font-family="Arial"
font-size="54"
font-weight="bold"
fill="#6ee7b7">
{current_streak}
</text>

<text x="70" y="240"
font-family="Arial"
font-size="16"
fill="#daf1de">
DAYS
</text>


<rect x="350" y="90"
width="280"
height="190"
rx="18"
fill="#163832"/>

<text x="380" y="130"
font-family="Arial"
font-size="15"
fill="#8eb69b">
🏆 LONGEST STREAK
</text>

<text x="380" y="205"
font-family="Arial"
font-size="54"
font-weight="bold"
fill="#daf1de">
{longest_streak}
</text>

<text x="380" y="240"
font-family="Arial"
font-size="16"
fill="#daf1de">
DAYS
</text>


<rect x="660" y="90"
width="280"
height="190"
rx="18"
fill="#0b2b26"/>

<text x="690" y="130"
font-family="Arial"
font-size="15"
fill="#8eb69b">
📅 CONTRIBUTION DAYS
</text>

<text x="690" y="205"
font-family="Arial"
font-size="54"
font-weight="bold"
fill="#6ee7b7">
{contribution_days}
</text>

<text x="690" y="240"
font-family="Arial"
font-size="16"
fill="#daf1de">
ACTIVE DAYS
</text>
'''

streak += "</svg>"

save_svg(
    "streak.svg",
    streak
)


# ---------------------------------------------------------
# CONTRIBUTION CALENDAR
# ---------------------------------------------------------

width = 1200
height = 250

contributions = svg_header(
    width,
    height
)

contributions += f'''
<text x="40" y="42"
font-family="Arial"
font-size="25"
font-weight="bold"
fill="#daf1de">
CONTRIBUTION GARDEN
</text>

<text x="40" y="67"
font-family="Arial"
font-size="13"
fill="#8eb69b">
{total_contributions} contributions in the last year
</text>
'''


colors = [
    "#0b2b26",
    "#163832",
    "#235347",
    "#8eb69b",
    "#daf1de",
]


start_x = 40
start_y = 95

cell = 13
gap = 4

for week_index, week in enumerate(weeks):

    x = start_x + week_index * (
        cell + gap
    )

    for day_index, day in enumerate(
        week["contributionDays"]
    ):

        y = start_y + day_index * (
            cell + gap
        )

        count = day["contributionCount"]

        if count == 0:
            color = colors[0]

        elif count <= 2:
            color = colors[1]

        elif count <= 5:
            color = colors[2]

        elif count <= 10:
            color = colors[3]

        else:
            color = colors[4]

        contributions += f'''
<rect
x="{x}"
y="{y}"
width="{cell}"
height="{cell}"
rx="3"
fill="{color}">
<title>
{day["date"]}: {count} contributions
</title>
</rect>
'''


contributions += f'''
<text x="40" y="225"
font-family="Arial"
font-size="13"
fill="#8eb69b">
Less
</text>

<rect x="75" y="215" width="13" height="13"
rx="3" fill="#0b2b26"/>

<rect x="95" y="215" width="13" height="13"
rx="3" fill="#163832"/>

<rect x="115" y="215" width="13" height="13"
rx="3" fill="#235347"/>

<rect x="135" y="215" width="13" height="13"
rx="3" fill="#8eb69b"/>

<rect x="155" y="215" width="13" height="13"
rx="3" fill="#daf1de"/>

<text x="180" y="225"
font-family="Arial"
font-size="13"
fill="#8eb69b">
More
</text>
'''

contributions += "</svg>"

save_svg(
    "contributions.svg",
    contributions
)


# ---------------------------------------------------------
# LANGUAGES SVG
# ---------------------------------------------------------

languages_svg = svg_header(
    900,
    430
)

languages_svg += '''
<text x="40" y="50"
font-family="Arial"
font-size="26"
font-weight="bold"
fill="#daf1de">
LANGUAGES
</text>
'''

total_language_bytes = sum(
    value for _, value in languages
)

language_colors = [
    "#daf1de",
    "#8eb69b",
    "#6ee7b7",
    "#235347",
    "#34d399",
    "#163832",
    "#a7f3d0",
    "#4ade80",
]


for index, (language, amount) in enumerate(
    languages
):

    percentage = (
        amount /
        total_language_bytes *
        100
        if total_language_bytes
        else 0
    )

    y = 95 + index * 38

    languages_svg += f'''
<text x="50" y="{y}"
font-family="Arial"
font-size="15"
fill="#daf1de">
{escape(language)}
</text>

<rect
x="190"
y="{y - 13}"
width="520"
height="16"
rx="8"
fill="#0b2b26"/>

<rect
x="190"
y="{y - 13}"
width="{520 * percentage / 100}"
height="16"
rx="8"
fill="{language_colors[index % len(language_colors)]}"/>

<text
x="735"
y="{y}"
font-family="Arial"
font-size="14"
fill="#8eb69b">
{percentage:.1f}%
</text>
'''


languages_svg += "</svg>"

save_svg(
    "languages.svg",
    languages_svg
)


# ---------------------------------------------------------
# REPOSITORIES SVG
# ---------------------------------------------------------

repo_svg = svg_header(
    1000,
    max(180, 170 * min(len(repositories), 5))
)

repo_svg += '''
<text x="40" y="50"
font-family="Arial"
font-size="26"
font-weight="bold"
fill="#daf1de">
LIVE REPOSITORIES
</text>
'''


for index, repo in enumerate(
    repositories[:5]
):

    y = 90 + index * 150

    repo_svg += f'''
<rect
x="35"
y="{y - 25}"
width="930"
height="120"
rx="16"
fill="#0b2b26"/>

<text
x="60"
y="{y + 10}"
font-family="Arial"
font-size="20"
font-weight="bold"
fill="#6ee7b7">
{escape(repo["name"])}
</text>

<text
x="60"
y="{y + 38}"
font-family="Arial"
font-size="13"
fill="#8eb69b">
{escape(repo.get("description", "")[:100])}
</text>

<text
x="60"
y="{y + 70}"
font-family="Arial"
font-size="13"
fill="#daf1de">
⭐ {repo.get("stargazers_count", 0)}
</text>

<text
x="140"
y="{y + 70}"
font-family="Arial"
font-size="13"
fill="#daf1de">
🍴 {repo.get("forks_count", 0)}
</text>

<text
x="250"
y="{y + 70}"
font-family="Arial"
font-size="13"
fill="#8eb69b">
{escape(repo.get("language", "Unknown"))}
</text>
'''


repo_svg += "</svg>"

save_svg(
    "repositories.svg",
    repo_svg
)


# ---------------------------------------------------------
# ACTIVITY SVG
# ---------------------------------------------------------

activity_width = 1000
activity_height = 400

activity = svg_header(
    activity_width,
    activity_height
)

activity += '''
<text x="40" y="50"
font-family="Arial"
font-size="26"
font-weight="bold"
fill="#daf1de">
ACTIVITY OVERVIEW
</text>
'''

recent_days = days[-90:]

maximum = max(
    [d["contributionCount"] for d in recent_days]
    or [1]
)

chart_x = 50
chart_y = 100

bar_width = 8
bar_gap = 3

for index, day in enumerate(
    recent_days
):

    count = day["contributionCount"]

    bar_height = (
        count / maximum * 220
        if maximum
        else 0
    )

    x = (
        chart_x +
        index * (
            bar_width + bar_gap
        )
    )

    y = 330 - bar_height

    activity += f'''
<rect
x="{x}"
y="{y}"
width="{bar_width}"
height="{bar_height}"
rx="3"
fill="#8eb69b">
<title>
{day["date"]}: {count}
</title>
</rect>
'''


activity += '''
<line
x1="45"
y1="330"
x2="950"
y2="330"
stroke="#235347"
stroke-width="2"/>

<text x="45" y="360"
font-family="Arial"
font-size="13"
fill="#8eb69b">
Last 90 days
</text>

<text x="830" y="360"
font-family="Arial"
font-size="13"
fill="#8eb69b">
GitHub activity
</text>
'''

activity += "</svg>"

save_svg(
    "activity.svg",
    activity
)


print("Profile dashboard generated successfully.")

print(f"Repositories: {public_repos}")
print(f"Stars: {total_stars}")
print(f"Followers: {followers}")
print(f"Contributions: {total_contributions}")
print(f"Contribution days: {contribution_days}")
print(f"Current streak: {current_streak}")
print(f"Longest streak: {longest_streak}")