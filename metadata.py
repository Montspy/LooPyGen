import json

dataPath = "./metadata"

#### Generate Metadata for each Image

f = open(dataPath + '/all-traits.json',)
data = json.load(f)

# Changes this IMAGES_BASE_URL to yours
IMAGES_BASE_URL = "https://gateway.pinata.cloud/ipfs/QmXHpoB7scTiutQ3Hc2Qm3EuWsMMzSGV1oqmJrX31gZoye/"
PROJECT_NAME = "Sacred Bodies"

def getAttribute(key, value):
    return {
        "trait_type": key,
        "value": value
    }
for i in data:
    token_id = i['tokenId']
    token = {
        "image": IMAGES_BASE_URL + str(token_id) + '.png',
        "tokenId": token_id,
        "name": PROJECT_NAME + ' ' + str(token_id),
        "attributes": []
    }
    token["attributes"].append(getAttribute("Chakra", i["Chakra"]))
    token["attributes"].append(getAttribute("Cover", i["Cover"]))
    token["attributes"].append(getAttribute("Shape", i["Shape"]))
    token["attributes"].append(getAttribute("Opacity", i["Opacity"]))
    token["attributes"].append(getAttribute("Hubble Image", i["Hubble Image"]))
    token["attributes"].append(getAttribute("Crop Location", i["Crop Location"]))

    with open(dataPath + '/' + str(token_id) + ".json", 'w') as outfile:
        json.dump(token, outfile, indent=4)

f.close()