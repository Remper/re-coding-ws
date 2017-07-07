from urllib import request
from urllib.error import HTTPError
from urllib.parse import urlencode

import argparse

from utils.queries import KNOWLEDGE_BASE_API, RESOURCE_QUERY

PROPERTY_WHITELIST = ["http://xmlns.com/foaf/0.1/isPrimaryTopicOf"]


class Counter:
    def __init__(self):
        self.value = 0
        self.first = True

    def inc(self):
        self.value += 1

    def done(self):
        self.first = False


def find_resource(wiki_id):
    url = KNOWLEDGE_BASE_API + '?' + urlencode({'accept': 'text/csv', 'query': RESOURCE_QUERY.replace(":id", wiki_id)})

    try:
        with request.urlopen(url) as raw:
            triples = raw.read().decode('utf-8').split('\n')
    except HTTPError as e:
        print("Error happened:", e, "Request:", wiki_id)
        return None

    candidates = set()

    for triple in triples:
        triple = triple.rstrip().split(',')
        if triple[0] in PROPERTY_WHITELIST and "wikidata.dbpedia.org" in triple[1]:
            candidates.add(triple[1])

    if len(candidates) == 1:
        return candidates.pop()

    options = "—"
    if len(candidates) > 1:
        options = ", ".join(candidates)

    print("Ambiguous entity:", wiki_id, "With options: ", options)
    return None


def process(id, row, writer, counter):
    wiki_id = row[id]

    try:
        counter.inc()
        resolved_id = find_resource(wiki_id)
        if resolved_id is None:
            return

        if not counter.first:
            writer.write('\n')

        counter.done()
        for idx in range(len(row)):
            if idx > 0:
                writer.write('\t')
            if idx == id:
                writer.write(resolved_id)
            else:
                writer.write(row[idx])
    except HTTPError as e:
        print("Error happened:", e, "Request:", wiki_id)


def __main__(args):
    print(vars(args))
    friends_writer = open(args.output, 'w')
    with open(args.input, 'r') as reader:
        counter = Counter()
        for line in reader:
            row = line.rstrip().split("\t")
            process(args.index, row, friends_writer, counter)
            friends_writer.flush()

    friends_writer.close()


def params():
    # Parsing parameters
    parser = argparse.ArgumentParser(description='Resolve wiki IDs against our knowledge base')
    parser.add_argument('--input', default='data/en.csv',
                        help='Input file to resolve', metavar='#')
    parser.add_argument('--index', default='0',
                        help='Index in the tab separated file to resolve', metavar='#')
    args = parser.parse_args()
    args.index = int(args.index)
    if args.input.endswith(".csv") or args.input.endswith(".tsv"):
        args.output = args.input[:-4]
    else:
        args.output = args.input
    args.output = args.output + "_resolved.tsv"

    return args

__main__(params())
