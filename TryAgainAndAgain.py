import requests
import json
from tqdm import tqdm
import time


class YandexMovements:
    def __init__(self, token):
        self.token = token
        self.headers = {'Authorization': f'OAuth {token}', 'Content-Type': 'application/json'}
        self.url_create_folder = 'https://cloud-api.yandex.net/v1/disk/resources'
        self.url_for_upload = 'https://cloud-api.yandex.net/v1/disk/resources/upload'

    def create_folder(self, name_folder: str):
        """Create new folder on Yandex Disk.
        Return None"""
        params = {'path': f'/{name_folder}'}
        response = requests.put(url=self.url_create_folder, headers=self.headers, params=params)
        if response.status_code == 201:
            print(f'Папка {name_folder} на Я.Диске создана успешно')
            return None
        else:
            print(response.json().get('message'))
            return None

    def upload_to_disk(self, file_urls: list, file_names, name_folder: str):
        """Upload file on Yandex Disk
        Return 1 - success, 0 - defeat"""
        for file in tqdm(range(len(file_urls))):
            url = file_urls[file]
            name = file_names[file]['file_name']
            path_on_yadisk = f'/{name_folder}/{name}'
            params = {'path': path_on_yadisk, 'url': url}
            response = requests.post(url=self.url_for_upload, params=params, headers=self.headers)
            if response.status_code != 202:
                print(f'При загрузке файла {name} произошла ошибка {response.status_code}: '
                      f'{response.json().get("message")}')
                return 0
        return 1


class Vk:
    def __init__(self, token, id_target_vk):
        self.get_photo_url = 'https://api.vk.com/method/photos.get'
        self.id_vk = id_target_vk
        self.token = token
        self.headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'multipart/form-data'}

    def _create_name_photo(self, photo_list):
        """Create list photo's name and size"""
        i = 0
        while i < len(photo_list):
            photo_name = photo_list[i]['file_name']
            for k in range(i+1, len(photo_list)):
                if photo_name == photo_list[k]['file_name']:
                    photo_list[k]['file_name'] = f'{photo_list[k]["date"]}.{photo_list[k]["file_name"]}'
                    photo_list[i]['file_name'] = f'{photo_list[i]["date"]}.{photo_list[i]["file_name"]}'
            i += 1
        return photo_list

    def _create_json_file(self, response):
        """Create json-file "photo_vk_info.json" with information
        about photos"""
        photo_info = []
        all_photo_url = []
        for items in response['response']['items']:
            max_size = 0
            file_url = ''
            my_dict = {}
            for sizes in items['sizes']:
                if sizes['height'] * sizes['width'] >= max_size:
                    max_size = sizes['height'] * sizes['width']
                    file_url = sizes['url']
                    file_size = sizes['type']
                    file_date = time.gmtime(items['date'])
                    file_name = f"{items['likes']['count']}.jpg"
                    my_dict = {
                        'file_name': file_name, 'size': file_size,
                        'date': f'{file_date.tm_mday}.{file_date.tm_mon}.{file_date.tm_year}'
                    }
            photo_info.append(my_dict)
            all_photo_url.append(file_url)
        photo_info = self._create_name_photo(photo_info)
        with open('photo_vk_info.json', 'w', encoding='utf-8') as file:
            json.dump(photo_info, file, indent=4)
        print('Json-файл создан успешно')
        return all_photo_url, photo_info

    def get_info_vk(self, photo_counter: int):
        """Get information about photo in profile VK.
        Create json-file 'photo_vk_info.json'.
        Return list photos url and list photo information.
        Version API VK 5.131"""
        params = {
            'owner_id': f'{self.id_vk}',
            'album_id': 'profile',
            'rev': 1,
            'extended': 1,
            'count': photo_counter,
            'v': '5.131'
        }
        response = requests.get(url=self.get_photo_url, params=params, headers=self.headers)
        if response.status_code == 200:
            photo_url_list, photo_information = self._create_json_file(response.json())
            print('Информация из VK получена успешно')
            return photo_url_list, photo_information
        else:
            print('При получении информации о фото из VK произошла ошибка.\nПроверьте правильность введённых данных.')
            return 0, 0


if __name__ == '__main__':
    vk_token = input('Введите access_token для VK : ')
    ya_token = input('Введите token для Я.Диска : ')
    id_vk = input('Введите id пользователя из VK : ')
    name_new_folder = input('Введите имя новой папки на Я.Диске для фото из VK : ')
    count_photo = int(input('Введите сколько последних фотографий необходимо загрузить : '))
    get_photo_vk = Vk(vk_token, id_vk)
    upload_photo_disk = YandexMovements(ya_token)
    photos_url, photos_inf = get_photo_vk.get_info_vk(count_photo)
    upload_photo_disk.create_folder(name_new_folder)
    a = upload_photo_disk.upload_to_disk(photos_url, photos_inf, name_new_folder)
    if photos_inf == 0 or photos_url == 0 or a == 0:
        print('Во время выполнение программы возникла ошибка.\n'
              'Программа не выполнила все действия, попробуйте ещё раз.')
    else:
        print(f'Программа отработала все положенные действия\n'
              f'{count_photo} последних фотографий загружены из профиля vk на Я.Диск')
