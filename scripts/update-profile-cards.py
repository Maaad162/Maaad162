"""Build profile cards from GitHub's public contribution calendar, without external card services."""

import argparse
from datetime import date, timedelta
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.request import Request, urlopen


class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.dates = {}
        self.counts = {}
        self.target = None
        self.tooltip = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "data-date" in attrs:
            self.dates[attrs["id"]] = date.fromisoformat(attrs["data-date"])
        if tag == "tool-tip":
            self.target = attrs.get("for")
            self.tooltip = []

    def handle_data(self, data):
        if self.target:
            self.tooltip.append(data)

    def handle_endtag(self, tag):
        if tag == "tool-tip" and self.target:
            text = "".join(self.tooltip).strip()
            match = re.match(r"([\d,]+) contributions? on ", text)
            if text.startswith("No contributions on "):
                self.counts[self.target] = 0
            elif match:
                self.counts[self.target] = int(match[1].replace(",", ""))
            self.target = None

    def days(self):
        today = date.today()
        days = sorted((day, self.counts[key]) for key, day in self.dates.items()
                      if day <= today and key in self.counts)
        if len(days) < 31 or len(days) != sum(day <= today for day in self.dates.values()):
            raise ValueError("GitHub did not return a complete contribution calendar")
        if any(b[0] - a[0] != timedelta(days=1) for a, b in zip(days, days[1:])):
            raise ValueError("Contribution calendar contains missing dates")
        return days


def text(x, y, value, size=14, color="#E6EDF3", extra=""):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" {extra}>{escape(str(value))}</text>'


def svg(title, description, height, content):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 880 {height}" role="img" '
            f'aria-labelledby="title desc"><title id="title">{escape(title)}</title>'
            f'<desc id="desc">{escape(description)}</desc>'
            f'<rect width="880" height="{height}" rx="12" fill="#0D1117"/>'
            '<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif">'
            + content + '</g></svg>')


def activity(days):
    days = days[-31:]
    maximum = max(1, max(count for _, count in days))
    x0, x1, y0, y1 = 62, 844, 82, 240
    points = [(x0 + i * (x1-x0)/(len(days)-1), y1 - count / maximum * (y1-y0))
              for i, (_, count) in enumerate(days)]
    out = text(28, 32, "Atividade no GitHub", 21, "#4169E1")
    out += text(28, 56, "Contribuições diárias · últimos 31 dias", 13, "#9CA3AF")
    for i in range(5):
        value = maximum * i / 4
        y = y1 - i * (y1-y0)/4
        out += f'<path d="M{x0} {y}H{x1}" stroke="#243044" stroke-width="1"/>'
        out += text(x0-12, y+4, f"{value:g}", 11, "#9CA3AF", 'text-anchor="end"')
    coords = ' '.join(f'{x:.2f},{y:.2f}' for x, y in points)
    out += f'<polygon points="{x0},{y1} {coords} {x1},{y1}" fill="#4169E1" opacity=".18"/>'
    out += f'<polyline points="{coords}" fill="none" stroke="#4169E1" stroke-width="3" stroke-linejoin="round"/>'
    for i, ((day, count), (x, y)) in enumerate(zip(days, points)):
        out += f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3" fill="#E6EDF3"><title>{day}: {count} contribuições</title></circle>'
        if i % 5 == 0 or i == len(days)-1:
            out += text(round(x, 2), 265, day.strftime('%d/%m'), 11, "#9CA3AF", 'text-anchor="middle"')
    description = '; '.join(f'{day}: {count}' for day, count in days)
    return svg("Atividade de desenvolvimento", description, 285, out)


def milestones(days):
    best = streak = 0
    for _, count in days:
        streak = streak + 1 if count else 0
        best = max(best, streak)
    cards = [(sum(n for _, n in days), "Contribuições"),
             (sum(n > 0 for _, n in days), "Dias ativos"),
             (best, "Melhor sequência · dias"),
             (max(n for _, n in days), "Recorde em um dia")]
    period = f"{days[0][0]:%d/%m/%Y} a {days[-1][0]:%d/%m/%Y}"
    out = text(28, 32, "Marcos de contribuição", 21, "#4169E1")
    out += text(28, 56, f"Dados públicos do GitHub · {period}", 13, "#9CA3AF")
    for i, (value, label) in enumerate(cards):
        x = 22 + i * 215
        out += f'<rect x="{x}" y="76" width="200" height="146" rx="10" fill="#131D32" stroke="#243B7A"/>'
        out += f'<g transform="translate({x+85},89)" fill="none" stroke="#4169E1" stroke-width="2"><path d="M7 3h16v10a8 8 0 0 1-16 0Z M7 6H2v5a7 7 0 0 0 8 7 M23 6h5v5a7 7 0 0 1-8 7 M15 21v7 M8 29h14"/></g>'
        out += text(x+100, 164, value, 30, "#FFFFFF", 'text-anchor="middle"')
        out += text(x+100, 196, label, 13, "#B9C5DA", 'text-anchor="middle"')
    description = '; '.join(f'{label}: {value}' for value, label in cards) + f'. Período: {period}'
    return svg("Marcos de contribuição", description, 242, out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--calendar', type=Path, help='Use a downloaded GitHub calendar for local validation')
    parser.add_argument('--output-dir', type=Path, default=Path('dist'))
    args = parser.parse_args()
    if args.calendar:
        html = args.calendar.read_text()
    else:
        req = Request('https://github.com/users/Maaad162/contributions',
                      headers={'User-Agent': 'GitHub-profile-assets', 'Accept-Language': 'en-US'})
        with urlopen(req, timeout=45) as response:
            html = response.read().decode()
    calendar = Calendar()
    calendar.feed(html)
    days = calendar.days()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / 'activity-royal-blue.svg').write_text(activity(days))
    (args.output_dir / 'contribution-milestones.svg').write_text(milestones(days))
    print(f'Generated both profile cards from {len(days)} days of public GitHub contributions.')


if __name__ == '__main__':
    main()
