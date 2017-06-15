from urllib import request
from urllib.error import HTTPError
from urllib.parse import urlencode

import json

SMT_API = "http://api.smt.futuro.media/alignments/by_twitter_id"


class Counter:
    def __init__(self):
        self.value = 0
        self.first = True

    def inc(self):
        self.value += 1

    def done(self):
        self.first = False


def align(uid):
    url = SMT_API + '?' + urlencode({'id': uid})

    with request.urlopen(url) as raw:
        candidates = json.loads(raw.read().decode('utf-8'))['data']['candidates']

    return candidates


def process(row, writer, counter):
    name = row[0]
    uid = row[1]
    friend_uid = row[2]
    friend_handler = row[3]
    friend_name = row[4]

    try:
        candidates = align(int(friend_uid))
        counter.inc()

        maxScore = 0
        maxCandidate = None
        for candidate in candidates:
            resource_id = candidate['resourceId']
            score = candidate['score']

            if maxScore < score and score > 0.2:
                maxScore = score
                maxCandidate = resource_id

        if maxCandidate is None or maxScore == 0:
            return

        if not counter.first:
            writer.write('\n')

        counter.done()
        writer.write(name)
        writer.write('\t')
        writer.write(uid)
        writer.write('\t')
        writer.write(friend_uid)
        writer.write('\t')
        writer.write(maxCandidate)
        writer.write('\t')
        writer.write(str(maxScore))
        print("(%5d)" % counter.value, name, "->", friend_name, "(@%s)" % friend_handler, "->", maxCandidate)
    except HTTPError as e:
        print("Error happened:", e, "Request:", friend_uid)


def __main__():
    friends_writer = open('data/friends_aligned.tsv', 'w')
    with open('data/friends.tsv', 'r') as reader:
        counter = Counter()
        for line in reader:
            row = line.split("\t")
            process(row, friends_writer, counter)
            friends_writer.flush()

    friends_writer.close()

__main__()