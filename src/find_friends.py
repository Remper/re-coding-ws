from urllib import request
from urllib.error import HTTPError
from urllib.parse import urlencode
from time import sleep
import json

SMT_API = "http://localhost:5241/recode/friends"


class Counter:
    def __init__(self):
        self.value = 0

    def inc(self):
        self.value += 1


def get_friends(uid):
    url = SMT_API + '?' + urlencode({'uid': uid})

    with request.urlopen(url) as raw:
        users = json.loads(raw.read().decode('utf-8'))['data']

    return users


def process(row, writer, counter):
    name = row[0]
    uid = row[1]

    try:
        friends = get_friends(uid)
        counter.inc()
        first = True
        for user in friends:
            if counter.value > 1 or not first:
                writer.write('\n')

            first = False
            writer.write(name)
            writer.write('\t')
            writer.write(uid)
            writer.write('\t')
            writer.write(str(user['id']))
            writer.write('\t')
            writer.write(user['screenName'])
            writer.write('\t')
            writer.write(user['name'])
            writer.write('\t')
            writer.write(str(user['isVerified']))
            writer.write('\t')
            writer.write(str(user['followersCount']))
            print("(%3d)" % counter.value, name, "->", user['name'])
    except HTTPError as e:
        print("I guess we have to wait:", e)
        sleep(60)
        process(row, writer, counter)


def __main__():
    friends_writer = open('data/friends.tsv', 'w')
    with open('data/alignments.tsv', 'r') as reader:
        counter = Counter()
        for line in reader:
            row = line.split("\t")
            process(row, friends_writer, counter)

    friends_writer.close()

__main__()