"""Snapshot the profile cards so GitHub serves the SVGs from this repository."""

from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


def download_svg(filename, bases, params):
    errors = []
    for base in bases:
        url = base + "?" + urlencode(params)
        try:
            with urlopen(Request(url, headers={"User-Agent": "GitHub-profile-assets"}), timeout=45) as response:
                data = response.read()
            root = ET.fromstring(data)
            if root.tag != "{http://www.w3.org/2000/svg}svg":
                raise ValueError("The response is not an SVG")
            text = " ".join(root.itertext()).lower()
            if any(message in text for message in ("something went wrong", "deployment not found", "rate limit", "could not fetch", "user not found")):
                raise ValueError("The SVG contains a service error")
            Path("dist", filename).write_bytes(data)
            print(f"Saved {filename} from {base}")
            return
        except Exception as error:
            errors.append(f"{base}: {error}")
    raise RuntimeError("No working source for " + filename + "\n" + "\n".join(errors))


def main():
    Path("dist").mkdir(exist_ok=True)
    download_svg("activity-royal-blue.svg", [
        "https://github-readme-activity-graph.vercel.app/graph",
    ], {
        "username": "Maaad162", "bg_color": "0D1117", "color": "E6EDF3",
        "line": "4169E1", "point": "FFFFFF", "area_color": "4169E1",
        "area": "true", "hide_border": "true", "custom_title": "Atividade no GitHub",
    })
    download_svg("trophies.svg", [
        "https://github-profile-trophy.vercel.app/",
        "https://github-profile-trophy-fork-two.vercel.app/",
        "https://github-profile-trophy-liard-delta.vercel.app/",
        "https://github-profile-trophy-winning.vercel.app/",
    ], {
        "username": "Maaad162", "theme": "algolia", "no-frame": "true",
        "no-bg": "true", "column": "4", "margin-w": "10", "margin-h": "10",
    })


if __name__ == "__main__":
    main()
