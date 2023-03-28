import vk_api
import time
from datetime import datetime


class VkInteraction:
    def __init__(self, token):
        self.vk_session = vk_api.VkApi(token=token)
        self.user_fields = ['country', 'city', 'bdate', 'sex']

    def get_user_candidates(self, user):
        search_params = {'status': 6}
        for field in self.user_fields:
            if field not in user:
                continue
            if field == 'sex':
                search_params['sex'] = get_partner_sex(user['sex'])
            elif field == 'bdate':
                if user['bdate'].count('.') < 2:
                    continue
                age = calculate_age(user['bdate'])
                search_params['age_from'] = age - 3
                search_params['age_to'] = age + 3
            else:
                search_params[f'{field}_id'] = user[field]['id']
        user_candidates = self.vk_session.method('users.search', values=search_params)['items']
        return user_candidates

    def photos_get(self, user_id, album_id='profile', photos_count=1000):
        photos_get_params = {
            'owner_id': user_id,
            'album_id': album_id,
            'count': 1000,
            'extended': 1,
            'photo_sizes': 1
        }
        result = self.vk_session.method('photos.get', values=photos_get_params)
        if result['count'] >= 1000:
            offset = 0
            while offset < result['count']:
                offset += 1000
                time.sleep(0.34)
                next_res = self.vk_session.method('photos.get', values={
                    **photos_get_params,
                    'offset': offset
                })
                result['items'].extend(next_res['items'])
        photos_info = []
        for photo in result['items']:
            new_info = filter_photo_info(photo)
            photos_info.append(new_info)
        photos_info.sort(key=lambda d: d['likes'], reverse=True)
        return photos_info


def get_partner_sex(user_sex):
    partner_sex = {0: None, 1: '2', 2: '1'}
    return partner_sex[user_sex]


def calculate_age(bdate):
    today = datetime.today()
    bdate_date = datetime.strptime(bdate, '%d.%m.%Y')
    age = today.year - bdate_date.year - ((today.month, today.day) < (bdate_date.month, bdate_date.day))
    return age


def filter_photo_info(photo_info):
    new_photo_info = {
        'likes': photo_info['likes']['count'],
        'id': photo_info['id']
    }
    return new_photo_info
