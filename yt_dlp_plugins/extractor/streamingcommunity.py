import re
import json
from dateutil import parser
# from datetime import datetime
# from yt_dlp.utils import (
#     clean_html,
#     extract_attributes,
#     get_element_by_attribute,
#     get_element_by_class,
#     get_element_html_by_class,
#     get_elements_by_class,
#     int_or_none,
#     join_nonempty,
#     parse_count,
#     parse_duration,
#     unescapeHTML,
# )
from yt_dlp.utils.traversal import traverse_obj

from yt_dlp.extractor.common import InfoExtractor


class StreamingCommunityIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?streamingcommunity\.\w+/watch/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://streamingcommunity.li/watch/7540',
        'md5': 'cfbfd17eccb0ead7d64cd432ce82b37b',
        'info_dict': {
            'id': '7540',
            'ext': 'mp4',
            # 'description': "",
            'title': 'Hazbin Hotel - Ouverture',
            'duration': 1500,
            'series': 'Hazbin Hotel',
            'series_id': '7540',
            'episode_id': 50635,
            'timestamp': 1705636441.0,
            'modified_timestamp': 1705636442.0,
            'season_id': 3965,
            'modified_date': '20240119',
            'playable_in_embed': True,
            'description': 'md5:49cdbc07b5b6c694d00c61c9dd91d924',
            'episode': 'Ouverture',
            'episode_number': 1,
            'season': 'Season 1',
            'season_number': 1,
            'upload_date': '20240119',
            # 'series': '',
            # Then if the test run fails, it will output the missing/incorrect fields.
            # Properties can be added as:
            # * A value, e.g.
            #     'title': 'Video title goes here',
            # * MD5 checksum; start the string with 'md5:', e.g.
            #     'description': 'md5:098f6bcd4621d373cade4e832627b4f6',
            # * A regular expression; start the string with 're:', e.g.
            #     'thumbnail': r're:^https?://.*\.jpg$',
            # * A count of elements in a list; start the string with 'count:', e.g.
            #     'tags': 'count:10',
            # * Any Python type, e.g.
            #     'view_count': int,
        },

    }]

    def _iso8601_to_unix(self, iso8601_string):
        datetime_obj = parser.parse(iso8601_string)
        unix_timestamp = datetime_obj.timestamp()
        return unix_timestamp

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        info = json.loads(self._html_search_regex(r'data-page="([^"]+)',webpage,'info'))

        iframe = self._download_webpage(traverse_obj(info, ('props', 'embedUrl')), video_id)
        iframeinfo = self._html_search_regex(r'<iframe[^>]+src="([^"]+)',iframe,'iframe info')
        vixcloud_iframe = self._download_webpage(iframeinfo, video_id)
        playlist_info = json.loads(re.sub(r',[^"]+}','}',self._html_search_regex(r'window\.masterPlaylist[^:]+params:[^{]+({[^<]+?})',vixcloud_iframe,'iframe info').replace('\'','"')))
        playlist_url = self._html_search_regex(r'window\.masterPlaylist[^<]+url:[^<]+\'([^<]+?)\'',vixcloud_iframe,'iframe info')
        video_info = json.loads(self._html_search_regex(r'window\.video[^{]+({[^<]+});',vixcloud_iframe,'iframe info'))
        tokens_url = ''
        for x,y in playlist_info.items():
            if y and x=="token":
                tokens_url = x + '=' + y
            if y and "token" in x:
                tokens_url = tokens_url + '&'+ x + '=' + y

        dl_url = playlist_url + '?' + tokens_url + '&expires=' + playlist_info.get('expires')
        formats = self._extract_m3u8_formats_and_subtitles(dl_url, video_id)

        video_return_dic = {
            'id': video_id,
            'title': traverse_obj(info, ('props','title','name')) + " - " + traverse_obj(info, ('props','episode','name')),
            'timestamp': self._iso8601_to_unix(traverse_obj(info, ('props','episode','created_at'))),
            'modified_timestamp': self._iso8601_to_unix(traverse_obj(info, ('props','episode','updated_at'))),
            'description': traverse_obj(info, ('props','episode','plot')),
            'playable_in_embed': True,
            'formats': formats[0],
            'subtitles': formats[1],
            'duration': traverse_obj(info, ('props','episode','duration'))*60,
        }

        if traverse_obj(info, ('props','title','type'))=='tv':
            video_return_dic.update({
                'series': traverse_obj(info, ('props','title','name')),
                'series_id': video_id,
                'season_number': traverse_obj(info, ('props','episode','season','number')),
                'season_id': traverse_obj(info, ('props','episode','season','id')),
                'episode': traverse_obj(info, ('props','episode','name')),
                'episode_number': traverse_obj(info, ('props','episode','number')),
                'episode_id': traverse_obj(info, ('props','episode','id'))
            })


        return video_return_dic