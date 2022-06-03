import requests
import json

def parse(urls):
    requrl = 'https://xd-core-api.onrender.com/xdlinks/encode'
    jsondata = {"channelId":"","urls":urls}
    headers = {"Content-type":"application/json"}
    resp = requests.post(requrl,data=json.dumps(jsondata),headers=headers)
    return parsejson(resp.text)

def parsejson(json):
        data = {}
        tokens = str(json).replace('{','').replace('}','').split(',')
        for t in tokens:
            split = str(t).split(':',1)
            data[str(split[0]).replace('"','')] = str(split[1]).replace('"','')
        return data['data']