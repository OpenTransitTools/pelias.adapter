from logging import getLogger
from urllib.parse import quote

import requests

logger = getLogger(__name__)


def autocomplete(search_term, def_val=None):
    ret_val = def_val
    ret_index = -1

    try:
        url = "https://ws-st.trimet.org/peliaswrap/v1/autocomplete?text={}".format(
            quote(search_term)
        )
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            features = data.get("features")
            if features and len(features) > 0:
                for i, f in enumerate(features):
                    n = f.get("properties").get("name")
                    if search_term == n:
                        ret_val = f
                        ret_index = i + 1
                        break
        else:
            # print("nope")
            pass
    except Exception as e:
        logger.info(e)
    return ret_val, ret_index


def main():
    url = "https://ws-st.trimet.org/rtp/routers/default/park_and_ride?maxTransitDistance=100000"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        data = sorted(data, key=lambda d: d["name"])
        # print(data, len(data))
        for d in data:
            n = d.get("name")
            r, i = autocomplete(n)
            if r:
                if i >= 4:
                    print("* ", end="")
                print(
                    "{} was found at result #{} ({})".format(
                        n, i, r.get("properties").get("label")
                    )
                )
            else:
                print("! {} was NOT found in Pelias".format(d))
            # break
    else:
        print("Can't pull {}".format(url))
