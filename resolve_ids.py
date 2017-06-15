from urllib import request
from urllib.error import HTTPError
from urllib.parse import urlencode

KNOWLEDGE_BASE_API = "http://ganymede.fbk.eu/dbpedia2/sparql"
QUERY = """select
  ?relation ?property
where {
 ?property ?relation <http://en.wikipedia.org/wiki/:id>
}
group by ?property ?relation"""
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
    url = KNOWLEDGE_BASE_API + '?' + urlencode({'accept': 'text/csv', 'query': QUERY.replace(":id", wiki_id)})

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


def process(row, writer, counter):
    wiki_id = row[0]

    try:
        counter.inc()
        id = find_resource(wiki_id)
        if id is None:
            return

        if not counter.first:
            writer.write('\n')

        counter.done()
        writer.write(id)
        for value in row[1:]:
            writer.write('\t')
            writer.write(value)
    except HTTPError as e:
        print("Error happened:", e, "Request:", wiki_id)


def __main__():
    friends_writer = open('data/en_resolved.tsv', 'w')
    with open('data/en.csv', 'r') as reader:
        counter = Counter()
        for line in reader:
            row = line.rstrip().split("\t")
            process(row, friends_writer, counter)
            friends_writer.flush()

    friends_writer.close()

__main__()