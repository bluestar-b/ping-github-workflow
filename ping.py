import json
import time
import requests
import sys
from datetime import datetime, timezone, timedelta

class DiscordWebhook:
    def __init__(self, url):
        self.url = url
        self.embed = {}
        self.content = None
        self.username = None
        self.avatar_url = None

    def set_username(self, username):
        self.username = username
        return self

    def set_avatar_url(self, avatar_url):
        self.avatar_url = avatar_url
        return self

    def set_content(self, content):
        self.content = content
        return self

    def set_title(self, title):
        self.embed["title"] = title
        return self

    def set_description(self, description):
        self.embed["description"] = description
        return self

    def set_color(self, color):
        self.embed["color"] = color
        return self

    def add_field(self, name, value, inline=False):
        if "fields" not in self.embed:
            self.embed["fields"] = []
        self.embed["fields"].append(
            {"name": name, "value": value, "inline": inline})
        return self

    def send(self):
        payload = {
            "username": self.username,
            "avatar_url": self.avatar_url,
            "content": self.content,
            "embeds": [self.embed]
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(self.url, json=payload, headers=headers)
        response.raise_for_status()

def save_ping_data(ping_data, file_path):
    with open(file_path, 'w') as file:
        json.dump(ping_data, file)

def ping_link(link, timeout):
    start = time.time()
    try:
        resp = requests.get(link['url'], timeout=timeout)
        is_up = True
        status_code = resp.status_code
    except requests.exceptions.Timeout:
        is_up = False
        status_code = 400
    except requests.exceptions.RequestException:
        is_up = False
        status_code = 500

    response_time = int((time.time() - start) * 1000)

    if 500 <= status_code < 600:
        is_up = False

    ping_data = {
        'id': link['id'],
        'isUp': is_up,
        'responseTime_ms': response_time,
        'statusCode': status_code,
        'time': time.time(),
        'description': link['description'],
        'url': link['url']
    }

    return ping_data

def ping_links_once(links, timeout):
    ping_data = {}
    for link in links:
        ping_data[link['id']] = ping_link(link, timeout)
    return ping_data

def load_config(file_path):
    with open(file_path, 'r') as file:
        config_data = json.load(file)

    timeout_str = config_data['timeout']
    timeout = parse_duration(timeout_str)

    return config_data, timeout

def parse_duration(duration_str):
    unit_map = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
    unit = duration_str[-1]
    if unit in unit_map:
        return int(duration_str[:-1]) * unit_map[unit]
    else:
        raise ValueError("Invalid duration string")

def main(webhook_url):
    config, timeout = load_config('config.json')
    ping_data = ping_links_once(config['links'], timeout)
    print(ping_data)
    save_ping_data(ping_data, 'pingdata.json')
    webhook = DiscordWebhook(webhook_url)
    webhook.set_title("Uptime Monitoring Results")

    for key, value in ping_data.items():
        status = "**Alive**" if value["isUp"] else "**Dead**"
        response_time = value["responseTime_ms"]
        status_code = value["statusCode"]
        time = datetime.utcfromtimestamp(value["time"]).replace(
            tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=7)))
        time_str = time.strftime("%Y-%m-%d %H:%M:%S")
        description = value["description"]
        url = value["url"]

        field_value = f"📜 Status: {status}\n📡 Response Time: {response_time} ms\n🔊 Status Code: {status_code}\n🕛 Time: {time_str}\n📋Description: {description}\n📎 URL: {url}"
        webhook.add_field(f"Service {key}", field_value)

    webhook.send()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 file.py <webhook_url>")
        sys.exit(1)
    webhook_url = sys.argv[1]
    main(webhook_url)
