import argparse
from urllib import request
from urllib.error import HTTPError
from urllib.parse import urlencode

import json

from utils.data import load_wiki_data, load_gold_data

SMT_API = "http://api.smt.futuro.media/alignments/by_twitter_id"


class Counter:
    def __init__(self, args):
        self.value = 0
        self.first = True
        self.wiki_data = None
        self.gold_data = None
        if args.whitelist:
            self.wiki_data = load_wiki_data()
        if args.gold:
            self.gold_data = load_gold_data()

    def inc(self):
        self.value += 1

    def done(self):
        self.first = False

    def in_data(self, ele):
        return self.wiki_data is None or ele in self.wiki_data


def align(uid):
    url = SMT_API + '?' + urlencode({'id': uid})

    with request.urlopen(url) as raw:
        candidates = json.loads(raw.read().decode('utf-8'))['data']['candidates']

    return candidates


def assign_candidate_sl(counter, friend_uid):
    candidates = align(int(friend_uid))

    maxScore = 0
    maxCandidate = None
    for candidate in candidates:
        resource_id = candidate['resourceId']
        score = candidate['score']

        if not counter.in_data(resource_id):
            continue

        if maxScore < score and score > 0.2:
            maxScore = score
            maxCandidate = resource_id

    return maxScore, maxCandidate


def assign_candidate_gold(counter, friend_handler):
    maxScore = 0
    maxCandidate = None
    if friend_handler in counter.gold_data:
        maxScore = 1.0
        maxCandidate = counter.gold_data[friend_handler]

    return maxScore, maxCandidate


def process(row, writer, counter):
    name = row[0]
    uid = row[1]
    friend_uid = row[2]
    friend_handler = row[3]
    friend_name = row[4]

    try:
        counter.inc()
        if counter.gold_data is None:
            maxScore, maxCandidate = assign_candidate_sl(counter, friend_uid)
        else:
            maxScore, maxCandidate = assign_candidate_gold(counter, friend_handler)

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


def __main__(args):
    print(vars(args))
    friends_writer = open('data/friends_aligned.tsv', 'w')
    with open('data/friends.tsv', 'r') as reader:
        counter = Counter(args)
        for line in reader:
            row = line.split("\t")
            process(row, friends_writer, counter)
            friends_writer.flush()

    friends_writer.close()


def params():
    # Parsing parameters
    parser = argparse.ArgumentParser(description='Align friends to DBpedia entities')
    parser.add_argument('--whitelist', action='store_true', help='Filter candidates against the whitelist (en.csv)')
    parser.add_argument('--gold', action='store_true', help='Align using the gold standard instead of SocialLink')
    args = parser.parse_args()

    return args

__main__(params())
