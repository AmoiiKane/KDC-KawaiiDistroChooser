# KDC - Kawaii Distro Chooser
# scraper.py — scrapes DistroWatch + Reddit for distro recommendations

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
}

DISTRO_LOGOS = {
    "ubuntu": "https://assets.ubuntu.com/v1/29985a98-ubuntu-logo32.png",
    "fedora": "https://fedoraproject.org/assets/images/fedora-workstation.png",
    "debian": "https://www.debian.org/logos/openlogo-nd-50.png",
    "arch": "https://archlinux.org/static/logos/archlinux-logo-dark-90dpi.ebdee92a15b3.png",
    "mint": "https://linuxmint.com/web/img/favicon.ico",
    "manjaro": "https://manjaro.org/img/logo.svg",
    "opensuse": "https://www.opensuse.org/build/images/opensuse-logo.svg",
    "pop": "https://pop.system76.com/assets/images/pop-logo.svg",
    "zorin": "https://zorinos.com/assets/img/zorin-logo.svg",
    "elementary": "https://elementary.io/images/logo.svg",
    "kali": "https://www.kali.org/images/kali-logo.svg",
    "endeavouros": "https://endeavouros.com/wp-content/uploads/2021/06/endeavour-logo-sans-logotype.png",
    "garuda": "https://garudalinux.org/images/garuda/logo-white.svg",
    "void": "https://voidlinux.org/assets/img/void_bg.png",
    "gentoo": "https://www.gentoo.org/assets/img/logo/gentoo-logo.svg",
    "nixos": "https://nixos.org/logo/nix-snowflake.svg",
    "default": ""
}

def get_distro_logo(distro_name: str) -> str:
    name_lower = distro_name.lower()
    for key, url in DISTRO_LOGOS.items():
        if key in name_lower:
            return url
    return DISTRO_LOGOS["default"]

def scrape_distrowatch_top() -> list[dict]:
    """Scrape DistroWatch top distros with their descriptions."""
    distros = []
    try:
        url = "https://distrowatch.com/dwres.php?resource=popularity"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        rows = soup.select("table.News tr")
        for row in rows[:20]:
            cells = row.find_all("td")
            if len(cells) >= 3:
                name_cell = cells[2]
                name_link = name_cell.find("a")
                if name_link:
                    name = name_link.get_text(strip=True)
                    distros.append({"name": name, "source": "distrowatch"})
    except Exception as e:
        print(f"[scraper] DistroWatch error: {e}")

    # Fallback popular distros if scrape fails
    if not distros:
        distros = [
            {"name": "Ubuntu", "source": "fallback"},
            {"name": "Fedora", "source": "fallback"},
            {"name": "Arch Linux", "source": "fallback"},
            {"name": "Linux Mint", "source": "fallback"},
            {"name": "Manjaro", "source": "fallback"},
            {"name": "Pop!_OS", "source": "fallback"},
            {"name": "Debian", "source": "fallback"},
            {"name": "openSUSE", "source": "fallback"},
            {"name": "Zorin OS", "source": "fallback"},
            {"name": "EndeavourOS", "source": "fallback"},
        ]
    return distros

def scrape_distrowatch_details(distro_name: str) -> dict:
    """Scrape details for a specific distro from DistroWatch."""
    details = {"name": distro_name, "description": "", "min_ram": 0, "min_disk": 0}
    try:
        slug = distro_name.lower().replace(" ", "").replace("!", "").replace("/", "")
        url = f"https://distrowatch.com/table.php?distribution={slug}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Get description
        desc_tag = soup.find("meta", {"name": "description"})
        if desc_tag:
            details["description"] = desc_tag.get("content", "")[:300]

        # Try to find RAM/disk requirements in the page text
        text = soup.get_text()
        ram_match = re.search(r"(\d+)\s*MB\s*RAM", text, re.IGNORECASE)
        if ram_match:
            details["min_ram"] = int(ram_match.group(1))

        disk_match = re.search(r"(\d+)\s*GB\s*(disk|storage|hard)", text, re.IGNORECASE)
        if disk_match:
            details["min_disk"] = int(disk_match.group(1))

    except Exception as e:
        print(f"[scraper] Detail error for {distro_name}: {e}")
    return details

def scrape_reddit_recommendations(specs_summary: str) -> list[str]:
    """Search Reddit for distro recommendations matching specs."""
    mentioned = {}
    known_distros = [
        "ubuntu", "fedora", "arch", "debian", "mint", "manjaro",
        "pop", "zorin", "elementary", "kali", "endeavouros", "garuda",
        "void", "gentoo", "nixos", "opensuse", "lubuntu", "xubuntu",
        "kubuntu", "mx linux", "lite", "antix"
    ]

    queries = [
        f"best linux distro {specs_summary} site:reddit.com",
        "linux distro recommendation low ram site:reddit.com",
        f"best linux distro beginner {datetime.now().year} site:reddit.com"
    ]

    for query in queries:
        try:
            url = f"https://www.reddit.com/search.json?q={requests.utils.quote(query)}&limit=10&sort=relevance"
            resp = requests.get(url, headers={**HEADERS, "Accept": "application/json"}, timeout=10)
            data = resp.json()
            posts = data.get("data", {}).get("children", [])
            for post in posts:
                body = post.get("data", {}).get("selftext", "").lower()
                title = post.get("data", {}).get("title", "").lower()
                text = body + " " + title
                for distro in known_distros:
                    count = text.count(distro)
                    if count > 0:
                        mentioned[distro] = mentioned.get(distro, 0) + count
            time.sleep(0.5)
        except Exception as e:
            print(f"[scraper] Reddit error: {e}")

    return sorted(mentioned, key=mentioned.get, reverse=True)[:5]


def recommend_distro(specs: dict) -> dict:
    """Main recommendation logic combining specs + scraped data."""
    ram_mb = specs.get("ram_mb", 4096)
    cpu_cores = specs.get("cpu_cores", 2)
    cpu_gen = specs.get("cpu_gen", "modern")
    gpu_vendor = specs.get("gpu_vendor", "unknown")
    disk_gb = specs.get("disk_gb", 50)

    # Build a simple specs summary for Reddit query
    if ram_mb < 2048:
        specs_summary = "very low ram 1gb old pc"
    elif ram_mb < 4096:
        specs_summary = "low ram 2gb lightweight"
    elif ram_mb < 8192:
        specs_summary = "4gb ram mid range"
    else:
        specs_summary = "8gb ram modern gaming"

    # Score distros based on specs
    scores = {
        "Ubuntu": 0, "Fedora": 0, "Arch Linux": 0, "Linux Mint": 0,
        "Manjaro": 0, "Pop!_OS": 0, "Debian": 0, "Zorin OS": 0,
        "EndeavourOS": 0, "Lubuntu": 0, "Void Linux": 0, "openSUSE": 0
    }

    # RAM scoring
    if ram_mb < 1024:
        scores["Void Linux"] += 5
        scores["Lubuntu"] += 5
        scores["Debian"] += 3
    elif ram_mb < 2048:
        scores["Lubuntu"] += 4
        scores["Linux Mint"] += 3
        scores["Zorin OS"] += 2
        scores["Debian"] += 3
    elif ram_mb < 4096:
        scores["Linux Mint"] += 4
        scores["Zorin OS"] += 3
        scores["Ubuntu"] += 3
        scores["Fedora"] += 2
    else:
        scores["Fedora"] += 4
        scores["Pop!_OS"] += 4
        scores["Ubuntu"] += 3
        scores["Arch Linux"] += 3
        scores["Manjaro"] += 3
        scores["EndeavourOS"] += 2

    # GPU scoring
    if gpu_vendor == "nvidia":
        scores["Pop!_OS"] += 4
        scores["Ubuntu"] += 2
        scores["Manjaro"] += 2
    elif gpu_vendor == "amd":
        scores["Fedora"] += 3
        scores["Arch Linux"] += 3
        scores["EndeavourOS"] += 2
    elif gpu_vendor == "intel":
        scores["Ubuntu"] += 2
        scores["Fedora"] += 2

    # CPU gen scoring
    if cpu_gen == "old":
        scores["Lubuntu"] += 3
        scores["Void Linux"] += 2
        scores["Debian"] += 2
    elif cpu_gen == "modern":
        scores["Arch Linux"] += 2
        scores["Fedora"] += 2
        scores["EndeavourOS"] += 2

    # CPU cores
    if cpu_cores >= 8:
        scores["Arch Linux"] += 2
        scores["Fedora"] += 2
        scores["Manjaro"] += 1

    # Disk
    if disk_gb < 20:
        scores["Void Linux"] += 3
        scores["Debian"] += 2
    elif disk_gb >= 50:
        scores["Pop!_OS"] += 1
        scores["Ubuntu"] += 1

    # Get Reddit boost
    reddit_picks = scrape_reddit_recommendations(specs_summary)
    for i, pick in enumerate(reddit_picks):
        for distro in scores:
            if pick in distro.lower():
                scores[distro] += (3 - i)

    # Pick winner
    winner = max(scores, key=scores.get)
    logo_url = get_distro_logo(winner)

    return {
        "recommended": winner,
        "logo_url": logo_url,
        "score": scores[winner],
        "specs_summary": specs_summary,
        "runner_ups": sorted(
            [k for k in scores if k != winner],
            key=scores.get, reverse=True
        )[:3]
    }


if __name__ == "__main__":
    import sys
    specs_json = sys.stdin.read()
    specs = json.loads(specs_json)
    result = recommend_distro(specs)
    print(json.dumps(result, indent=2))
