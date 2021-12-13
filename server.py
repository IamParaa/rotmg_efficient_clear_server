import re
from flask import Flask, session, request
import json
import redis


app = Flask(__name__)
_redis = redis.Redis('localhost',charset="utf-8", decode_responses=True)

def fixedTemplate():
    data = {}
    data['server'] = "undefined"
    data['pw'] = "default"
    data['mapIdx'] = 0
    for i in range(128):
        data[i] = 0
    return data

@app.route("/<lobby>", methods=["GET", "PUT", "POST"])
def derp(lobby):

    if lobby == "favicon.ico": #browser stuff...
        return "lmao"

    pw = request.args.get('pw')
    if not pw:
        print("pw did not get set, defaulting")
        pw = "default"

    if request.method == "POST":
        data = {}
        try:
            data = request.get_json(force=True)
        except Exception as e:
            print("Uknown Error with post Request, {}".format(e))
            data = {}

        roomExists = _redis.exists(lobby) == True
        if roomExists == True:
            if _redis.hget(lobby,'pw') != pw:
                return "WRONG PASSWORD"

        d = fixedTemplate()
        for key in data.keys():
            b_continue = False
            if roomExists == True and key == 'pw':
                b_continue = True
            else:
                d['pw'] = pw
            if not b_continue:
                d[key] = data[key]
        for key in d.keys():
            _redis.hset(lobby, key, d[key])
        return "new lobby set"

    if request.method == "PUT":
        data = request.get_json(force=True)
        print("PUT DATA", data, type(data))
        if _redis.exists(lobby):
            if pw != _redis.hget(lobby, 'pw'):
                return "WRONG PASSWORD"
            clientMapIdx = data.pop('mapIdx')
            clientServer = data.pop('server')
            serverMapIdx = _redis.hget(lobby, "mapIdx")
            if clientMapIdx != serverMapIdx:
                return "lobby existed, did not update though"
            for k in data.keys():
                v = data[k]
                _redis.hset(lobby, k, v)
                _redis.expire(lobby, 1800)
            return "lobby existed"
        else:
            d = fixedTemplate()
            for k in data.keys():
                v = data[k]
                d[k] = v
            for key in d.keys():
                _redis.hset(lobby, key, d[key])
            _redis.expire(lobby, 1800)
            return "lobby now exists and key set"

    if request.method == "GET":
        if not _redis.exists(lobby):
            d = fixedTemplate()
            d['pw'] = pw
            for key in d.keys():
                _redis.hset(lobby, key, d[key])

        if _redis.hget(lobby,"pw") != pw:
            return "WRONG PASSWORD"

        data = {}
        data['server'] = _redis.hget(lobby, "server")
        data['mapIdx'] = _redis.hget(lobby, "mapIdx")

        circleIds = []
        for i in range(128):
            circleIds.append(_redis.hget(lobby, i))
        data['markerPiIdxs'] = circleIds
       # print("hmmm", data)
        _redis.expire(lobby, 1800)
        return json.dumps(data)
    
    return "UNSUPPORTED"

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)
