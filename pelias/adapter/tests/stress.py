import random
import requests
from ott.utils.tests.stress import stress_main


#url_path="https://ws-st.trimet.org/peliaswrap/v1"
url_path="http://localhost:45554/pelias"

urls = [
    f"{url_path}/autocomplete?text=834%20SE%20Lamb",
    f"{url_path}/rtp/search?text=1931%20NE%20Sandy",
    f"{url_path}/search?text=pdx",
    f"{url_path}/rtp/autocomplete?text=14606",
    f"{url_path}/rtp/autocomplete?text=5",
    f"{url_path}/rtp/autocomplete?text=6",
    f"{url_path}/rtp/autocomplete?text=999%20SE%20Lambert",
    f"{url_path}/rtp/search?text=66"
]


def curl_example_query():
    ret_val = False

    try:
        u = random.choice(urls)
        resp = requests.get(u)
        if resp.status_code == 200:
            j = resp.json()
            j.get('features')[0].get('properties').get('id')  # test for good content
            ret_val = True
        # import pdb; pdb.set_trace()
    except Exception as e:        
        # print(e, flush=True)
        ret_val = False
    return ret_val


def main():
    print("Stress out pelias wrapper")
    stress_main(curl_example_query)
