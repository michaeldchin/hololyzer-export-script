import csv
import os
import requests
import re
import sys
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
if not HOLODEX_API_KEY:
    raise ValueError("HOLODEX_API_KEY not found in environment variables")

hololyzer_url = "https://hololyzer.net"
holodex_api_url = "https://holodex.net/api/v2"

# Single source of truth for CSV field order and default keys.
FIELDS = [
    'video_id',
    'video_title',
    'holodex_topic_id',
    'holodex_published_at',
    'holodex_available_at',
    'public_time',
    'start_time',
    'end_time',
    'total_time',
    'chat_num_total',
    'chat_num_ja',
    'chat_num_emoji',
    'chat_num_en',
    'uniq_user_num',
    'uniq_member_num',
    'total_super_chat_amount_yen',
    'english_chat_ratio',
    'member_chat_ratio',
    'chat_per_second',
    'max_ccv',
    'member_num',
    'member_gift_num_from',
    'member_gift_num_to',
    'milestone_num',
    'channel_id',
    'channel_en_name',
    'channel_ja_name',
    'channel_en_category',
    'channel_ja_category',
]

response_string_en = requests.get(hololyzer_url + "/youtube/locales/string_en.json")
response_string_en.raise_for_status()
response_string_en.encoding = "utf-8"
string_en = response_string_en.json()

response_string_ja = requests.get(hololyzer_url + "/youtube/locales/string_ja.json")
response_string_ja.raise_for_status()
response_string_ja.encoding = "utf-8"
string_ja = response_string_ja.json()

def channels():
    response = requests.get(hololyzer_url)
    response.raise_for_status()
    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, 'html.parser')
    
    channel_labels = soup.find_all(attrs={"data-i18n": "label.sidemenu.list"})
    channels = []

    for channel_label in channel_labels:
        id = channel_label.parent.get('href').split('/')[-1].replace('.html', '')

        channel_parent = channel_label.find_parent('details')
        label_name = channel_parent.select_one('[data-i18n^="label.name."]').get('data-i18n').split('.')[-1]
        en_name = string_en['label']['name'].get(label_name, channel_parent.find('summary').text)
        ja_name = string_ja['label']['name'].get(label_name, channel_parent.find('summary').text)

        category_parent = channel_parent.find_parent('details')
        label_category = category_parent.select_one('[data-i18n^="label.category."]').get('data-i18n').split('.')[-1]
        en_category = string_en['label']['category'].get(label_category, category_parent.find('summary').text)
        ja_category = string_ja['label']['category'].get(label_category, category_parent.find('summary').text)

        # channels.append(Channel(id, en_name, ja_name, en_category, ja_category))

        channels.append({
            "id": id,
            "en_name": en_name,
            "ja_name": ja_name,
            "en_category": en_category,
            "ja_category": ja_category
        })

    return channels

def get_video_data(holodex_info):
    # initialize all expected fields with empty defaults from FIELDS
    data = {k: '' for k in FIELDS}
    # fill holodex-provided metadata
    data['video_id'] = holodex_info.get('id', '')
    data['video_title'] = holodex_info.get('title', '')
    data['holodex_topic_id'] = holodex_info.get('topic_id', '')
    data['holodex_published_at'] = holodex_info.get('published_at', '')
    data['holodex_available_at'] = holodex_info.get('available_at', '')

    try:
        response = requests.get(f"{hololyzer_url}/youtube/video/{holodex_info['id']}.html")
        response.raise_for_status()

    except requests.exceptions.HTTPError as error:
        if error.response is not None and error.response.status_code != 404: raise
        return data
    else:
        response.encoding = "utf-8"

        soup = BeautifulSoup(response.text, 'html.parser')

        table = soup.select_one('table[height]')

        if not table: raise

        table_text = table.get_text()

        table_text = table_text.replace("\r\n", "\n").strip("\n")
        lines = [line.replace('　', '').strip() for line in table_text.split('\n') if '：' in line]

        def extract_field(field_type, line):
            if '-' not in line:
                field = line.split('：')[1]

                if field_type == 'date':
                    string_no_timezone = field.replace("(JST)", "")

                    if not string_no_timezone: return ''

                    dt_naive = datetime.strptime(string_no_timezone.strip(), "%Y/%m/%d %H:%M:%S")

                    jst = timezone(timedelta(hours=9))
                    dt_jst = dt_naive.replace(tzinfo=jst)

                    return dt_jst.isoformat()
                elif field_type == 'string':
                    return field if field else ''
                elif field_type == 'int':
                    match = re.search(r"\d+", field.replace(',', ''))
                    return int(match.group()) if match else ''
                elif field_type == 'percent':
                    match = re.search(r"[\d\.]+", field.replace(',', ''))
                    return float(match.group()) / 100 if match else ''
                elif field_type == 'float':
                    match = re.search(r"[\d\.]+", field.replace(',', ''))
                    return float(match.group()) if match else ''
            else: return ''

        for line in lines:
            if line.startswith('公開日時'): data['public_time'] = extract_field('date', line)
            if line.startswith('開始日時'): data['start_time'] = extract_field('date', line)
            if line.startswith('終了日時'): data['end_time'] = extract_field('date', line)

            if line.startswith('動画時間'): data['total_time'] = extract_field('string', line)

            if line.startswith('総チャット数'): data['chat_num_total'] = extract_field('int', line)
            if line.startswith('チャット数（日本語）'): data['chat_num_ja'] = extract_field('int', line)
            if line.startswith('チャット数（スタンプ）'): data['chat_num_emoji'] = extract_field('int', line)
            if line.startswith('チャット数（英語）'): data['chat_num_en'] = extract_field('int', line)

            if line.startswith('ユニークユーザー数'): data['uniq_user_num'] = extract_field('int', line)
            if line.startswith('ユニークメンバー数'): data['uniq_member_num'] = extract_field('int', line)

            if line.startswith('総スパチャ金額'): data['total_super_chat_amount_yen'] = extract_field('int', line)

            if line.startswith('英語コメ率'): data['english_chat_ratio'] = extract_field('percent', line)
            if line.startswith('メンバーコメ率'): data['member_chat_ratio'] = extract_field('percent', line)

            if line.startswith('平均毎秒コメ数'): data['chat_per_second'] = extract_field('float', line)

            if line.startswith('最大同接'): data['max_ccv'] = extract_field('int', line)

            if line.startswith('メンシ入り'): data['member_num'] = extract_field('int', line)

            if line.startswith('メンシギフト') and '-' not in line:
                match = re.search(r"(\d+)\D+(\d+)", line)

                if match:
                    data['member_gift_num_from'] = int(match.group(1))
                    data['member_gift_num_to'] = int(match.group(2))

            if line.startswith('マイルストーン'): data['milestone_num'] = extract_field('int', line)

        return data


def videos_with_data(channel, csv_writer, fieldnames, existing_ids=None):
    """Fetch video ids for channel, stream each video's data into csv_writer.

    csv_writer is expected to be a csv.DictWriter already configured with fieldnames.
    """
    videos_result = []

    print(f"Fetching video info from Holodex for channel", channel['en_name'], channel['id'])

    # If caller attached a 'last_n' hint to the channel, only fetch that many newest videos
    last_n = channel.get('last_n') if isinstance(channel.get('last_n'), int) else None

    if last_n is not None:
        params = {"type": "stream", "limit": last_n, "offset": 0}
        headers = { "X-APIKEY": HOLODEX_API_KEY }
        response = requests.get(f"{holodex_api_url}/channels/{channel['id']}/videos", params=params, headers=headers)
        response.raise_for_status()
        response.encoding = "utf-8"
        holodex_video_info_response = response.json()
        for holodex_video in holodex_video_info_response:
            videos_result.append({
                'id': holodex_video['id'],
                'title': holodex_video.get('title'),
                'topic_id': holodex_video.get('topic_id'),
                'published_at': holodex_video.get('published_at'),
                'available_at': holodex_video.get('available_at'),
            })
        print(f"Fetched {len(videos_result)} (latest) video info from Holodex for channel", channel['en_name'], channel['id'])
    else:
        while True:
            params = {
                "type": "stream",
                "limit": 50,
                "offset": len(videos_result),
            }

            headers = { "X-APIKEY": HOLODEX_API_KEY }

            response = requests.get(f"{holodex_api_url}/channels/{channel['id']}/videos", params=params, headers=headers)
            response.raise_for_status()
            response.encoding = "utf-8"

            holodex_video_info_response = response.json()

            for holodex_video in holodex_video_info_response:
                videos_result.append({
                    'id': holodex_video['id'],
                    'title': holodex_video['title'],
                    # topic_id, published_at, available_at may be missing for some videos
                    'topic_id': holodex_video['topic_id'] if 'topic_id' in holodex_video else None,
                    'published_at': holodex_video['published_at'] if 'published_at' in holodex_video else None,
                    'available_at': holodex_video['available_at'] if 'available_at' in holodex_video else None,
                })

            if len(holodex_video_info_response) < 50:
                print(f"Fetched {len(videos_result)} video info from Holodex for channel", channel['en_name'], channel['id'])
                break

    existing_ids = existing_ids or set()

    total = len(videos_result)
    for idx, holodex_info in enumerate(videos_result, start=1):
        if holodex_info['id'] in existing_ids:
            # already present in CSV, skip
            print(f"[{idx}/{total}] Channel: {channel['en_name']} ({channel['id']}) - Video: {holodex_info['id']} - Skipped (already present)")
            continue
        # fetch and build complete data
        complete_data = {
            **get_video_data(holodex_info),
            'channel_id': channel['id'],
            'channel_en_name': channel['en_name'],
            'channel_ja_name': channel['ja_name'],
            'channel_en_category': channel['en_category'],
            'channel_ja_category': channel['ja_category'],
        }

        # prepare a flat mapping for CSV writer following fieldnames order
        row = { name: complete_data.get(name) for name in fieldnames }

        # print channel and id to show progress with counter
        print(f"[{idx}/{total}] Channel: {channel['en_name']} ({channel['id']}) - Video: {holodex_info['id']} - Wrote to CSV")

        csv_writer.writerow(row)


def load_existing_ids(output_file):
    """Return a tuple (existing_ids_set, counts_by_channel_dict).

    existing_ids_set is a set of video_id strings found in the CSV.
    counts_by_channel_dict maps channel_id -> count of rows for that channel.
    If the file doesn't exist or cannot be read, returns (set(), {}).
    """
    existing_ids = set()
    counts_by_channel = {}
    if not os.path.exists(output_file):
        return existing_ids, counts_by_channel

    try:
        with open(output_file, 'r', newline='', encoding='utf-8') as readfile:
            reader = csv.DictReader(readfile)
            for row in reader:
                vid = row.get('video_id')
                ch = row.get('channel_id')
                if vid:
                    existing_ids.add(vid)
                if ch:
                    counts_by_channel[ch] = counts_by_channel.get(ch, 0) + 1
    except Exception:
        # if reading fails for any reason, return empty structures so we try all
        return set(), {}

    return existing_ids, counts_by_channel


def process_output_file(output_file, fieldnames, limit_recent_only=False):
    """Create or append to CSV, streaming video rows and skipping existing ids.
    
    If limit_recent_only is True, only fetch the latest 50 entries for each channel.
    """
    existing_ids, counts_by_channel = load_existing_ids(output_file)

    # iterate channels and decide whether to skip based on Holodex 'total'
    channel_list = channels()

    # helper: query Holodex paginated total for a channel. Returns int or None
    def holodex_total_for_channel(ch):
        try:
            params = {"type": "stream", "paginated": "true"}
            headers = {"X-APIKEY": HOLODEX_API_KEY}
            resp = requests.get(f"{holodex_api_url}/channels/{ch['id']}/videos", params=params, headers=headers)
            resp.raise_for_status()
            resp.encoding = 'utf-8'
            data = resp.json()
            # expected top-level 'total' when paginated=true
            if isinstance(data, dict) and 'total' in data:
                return int(data['total'])
        except Exception:
            return None
        return None

    # ensure output directory exists before possibly opening file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # open in append mode if exists (we'll have header already), otherwise write with header
    mode = 'a' if os.path.exists(output_file) else 'w'
    with open(output_file, mode, newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if mode == 'w':
            writer.writeheader()

        for channel in channel_list:
            existing_count = counts_by_channel.get(channel['id'], 0)
            total = holodex_total_for_channel(channel)

            # If limit_recent_only flag is set, always fetch only the latest 50
            if limit_recent_only:
                channel['last_n'] = 50
                print(f"Fetching latest 50 entries for channel {channel['en_name']} ({channel['id']})")
            # If Holodex reported total and it's less/equal to our existing rows, skip
            elif total is not None and existing_count >= total:
                print(f"Skipping channel {channel['en_name']} ({channel['id']}) — existing rows ({existing_count}) >= Holodex total ({total})")
                continue
            # If channel already has rows and is within 50 of Holodex total, only fetch latest 50
            elif total is not None and existing_count > 0 and (total - existing_count) <= 50:
                channel['last_n'] = 50
                print(f"Partial update for channel {channel['en_name']} ({channel['id']}): fetching latest 50 (missing {total - existing_count})")
            else:
                channel['last_n'] = None

            videos_with_data(channel, writer, fieldnames, existing_ids)


def main():
    output_file = "output/dataset.csv"
    
    # Check for --latest-only flag to limit to most recent 50 entries per channel
    limit_recent_only = "--latest-only" in sys.argv

    process_output_file(output_file, FIELDS, limit_recent_only)

    print(f"Wrote CSV to {output_file}")


if __name__ == "__main__":
    main()
