# Modified from https://github.com/gumerov-amir/TTMediaBot


import shutil

import requests


def download_file(url: str, file_path: str) -> None:
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
    }
    with requests.get(url, headers=headers, stream=True) as r:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(r.raw, f)
