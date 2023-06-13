import scrapy
import re
import json


class YtSpider(scrapy.Spider):
    name = "yt"

    def __init__(self, query, **kwargs):
        self.query = query.replace(' ', '+')
        self.location = kwargs.get('location', 'US')
        super().__init__(**kwargs)

    def start_requests(self):
        urls = [
            f'https://www.youtube.com/results?search_query={self.query}',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        url = "https://www.youtube.com/youtubei/v1/search?prettyPrint=false"
        continuation_token = re.findall(
            'continuationCommand.*token":"(.*?)"', response.text)[0]
        clientVersion = response.meta.get('clientVersion') if response.meta.get(
            'clientVersion') else re.findall('clientVersion":"(.*?)"', response.text)[0]
        clientName = response.meta.get('clientName') if response.meta.get(
            'clientName') else re.findall('clientName":"(.*?)"', response.text)[0]
        userAgent = response.meta.get('userAgent') if response.meta.get(
            'userAgent') else re.findall('userAgent":"(.*?)"', response.text)[0]

        payload = json.dumps({
            "context": {
                "client": {
                    "hl": "en",
                    "gl": self.location,
                    "userAgent": userAgent,
                    "clientName": clientName,
                    "clientVersion": clientVersion,
                },

            },
            "continuation": continuation_token
        })
        headers = {
            'authority': 'www.youtube.com',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.7',
            'content-type': 'application/json',
            'origin': 'https://www.youtube.com',
            'referer': 'https://www.youtube.com/results?search_query=python',
            'sec-ch-ua': '"Brave";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"macOS"',
            'sec-ch-ua-platform-version': '"13.3.0"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'same-origin',
            'sec-fetch-site': 'same-origin',
            'sec-gpc': '1',

        }
        if response.meta.get('second', False):
            json_file = response.json()
            contents = json_file.get('onResponseReceivedCommands')[
                0]['appendContinuationItemsAction']['continuationItems'][0]['itemSectionRenderer']['contents']
            for content in contents:
                video = content.get('videoRenderer')
                if video:
                    title = video.get('title', {}).get(
                        'runs', [{}])[0].get('text')
                    video_id = video.get('videoId')
                    thumbnail = video.get('thumbnail', {}).get(
                        'thumbnails', [{}, {}])[-1].get('url')
                    description = ''
                    views = video.get('viewCountText', {}).get('simpleText')
                    subscriber = video.get('ownerBadges', [{}])[0].get(
                        'metadataBadgeRenderer', {}).get('label',)
                    published = video.get(
                        'publishedTimeText', {}).get('simpleText')
                    duration = video.get('lengthText', {}).get('simpleText')
                    channel_name = video.get('ownerText', {}).get('runs')[
                        0].get('text')
                    video_url = f'https://www.youtube.com/watch?v={video_id}'
                    channel_id = video.get('ownerText', {}).get('runs', [{}])[0].get(
                        'navigationEndpoint', {}).get('browseEndpoint', {}).get('browseId', {})
                    yield {
                        'title': title,
                        'video_url': video_url,
                        'channel_id': channel_id,
                        'channel_name': channel_name,
                        'thumbnail': thumbnail,
                        'description': description,
                        'views': views,
                        'published': published,
                        'duration': duration,

                    }

                # detailedMetadataSnippets
                # description = video.get('detailedMetadataSnippets')[0].get(
                #     'snippetText').get('runs')[1].get('text')
        yield scrapy.Request(url=url, method='POST', headers=headers, body=payload, meta={'second': True, 'clientVersion': clientVersion, 'clientName': clientName, 'userAgent': userAgent})
