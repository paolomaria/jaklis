import requests
from time import time
from lib.cesiumCommon import CesiumCommon
from lib.gvaWallets import ListWallets


class GeolocProfiles(CesiumCommon):
    def getCesiumProfiles(self):
        # Send a POST request to the Cesium profiles API
        response = requests.post(
            "https://g1.data.e-is.pro/user/profile/_search?scroll=2m",
            json={
                "query": {
                    "constant_score": {
                        "filter": [
                            {"exists": {"field": "geoPoint"}},
                            {
                                "geo_bounding_box": {
                                    "geoPoint": {
                                        "top_left": {"lat": 90, "lon": -180},
                                        "bottom_right": {"lat": -90, "lon": 180},
                                    }
                                }
                            },
                        ]
                    }
                },
                "_source": [
                    "title",
                    "avatar._content_type",
                    "description",
                    "city",
                    "address",
                    "socials.url",
                    "creationTime",
                    "membersCount",
                    "type",
                    "geoPoint",
                ],
                "size": 20000,
            },
        )

        scroll_id = response.json()["_scroll_id"]
        finalResult: dict | None = response.json()["hits"]["hits"]

        while True:
            # Send a scroll request to get the next page
            response_scroll = requests.post(
                "https://g1.data.e-is.pro/_search/scroll",
                json={"scroll_id": scroll_id, "scroll": "2m"},
            )

            # Check if the response is empty (no results) or if there's an error
            if (
                not response_scroll.json()["hits"]["hits"]
                or "error" in response_scroll.json()
            ):
                break
            else:
                finalResult.extend(response_scroll.json()["hits"]["hits"])

            # Process the results here

        # Delete the scroll context when done
        requests.delete(
            "https://g1.data.e-is.pro/_search/scroll", json={"scroll_id": [scroll_id]}
        )

        return finalResult

    def getGVAProfiles(self, node):
        # Retrieve GVA profiles using the ListWallets class
        gva = ListWallets(node, map=True)
        return gva.sendDoc()

    def formatProfiles(self, cesiumProfiles, gvaProfiles):
        walletsResult = []
        for profile in cesiumProfiles:
            source: dict = profile["_source"]
            pubkey: dict = profile["_id"]

            if pubkey not in gvaProfiles:
                continue

            # Extract necessary information from the profiles
            id_info: dict = gvaProfiles[pubkey].get("id") or {}
            isMember = id_info.get("isMember", False)
            userId = id_info.get("username")
            title = source.get("title")
            city = source.get("city")
            avatar = source.get("avatar")
            socials = source.get("socials")
            description = source.get("description")
            address = source.get("address")

            walletsResult.append(
                {
                    "pubkey": pubkey,
                    **({"address": address} if address else {}),
                    **({"city": city} if city else {}),
                    **({"description": description} if description else {}),
                    **({"avatar": avatar} if avatar else {}),
                    **({"userId": userId} if userId else {}),
                    "isMember": isMember,
                    "geoPoint": source["geoPoint"],
                    **({"socials": socials} if socials else {}),
                    **({"title": title} if title else {}),
                }
            )

        return {"wallets": walletsResult, "time": int(time())}
