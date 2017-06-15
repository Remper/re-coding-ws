import json

KNOWLEDGE_BASE_API = "http://ganymede.fbk.eu/dbpedia2/sparql"
QUERY = """select
  ?relation ?property
where {
 ?property ?relation <http://en.wikipedia.org/wiki/:id>
}
group by ?property ?relation"""


class Counter:
    def __init__(self):
        self.value = 0
        self.cur = None
        self.cur_uid = None
        self.categories = {}
        self.friends = 0
        self.first = True

    def add(self, target, uid, score, categories):
        if self.cur != target:
            result = self._dump()
            self.cur = target
            self.cur_uid = uid
            self.categories = {}
            self.friends = 0
        else:
            result = None

        for category in categories:
            if category not in self.categories:
                self.categories[category] = categories[category] * score
            else:
                self.categories[category] += categories[category] * score
        self.friends += 1

        return result

    def _dump(self):
        if self.cur is None:
            return None

        for category in self.categories:
            self.categories[category] /= self.friends

        return self.cur, self.cur_uid, self.categories

    def inc(self):
        self.value += 1

    def done(self):
        self.first = False


def load_wiki_data():
    data = {}
    with open('data/en_resolved.tsv', 'r') as reader:
        counter = 0
        for line in reader:
            row = line.split("\t")
            categories = {}
            for idx in range(1, len(row), 2):
                categories[row[idx]] = float(row[idx+1])
            data[row[0]] = categories
            counter += 1
            if counter % 10000 == 0:
                print("Processed", str(counter))
    return data


def process(row, writer, counter, wiki_data):
    name = row[0]
    uid = row[1]
    max_candidate = row[3]
    max_score = float(row[4])

    counter.inc()

    if max_candidate not in wiki_data:
        return

    categories = wiki_data[max_candidate]
    result = counter.add(name, uid, max_score, categories)

    if result is None:
        return

    cur, cur_uid, categories = result

    if not counter.first:
        writer.write('\n')

    counter.done()
    writer.write(cur)
    writer.write('\t')
    writer.write(cur_uid)
    writer.write('\t')
    writer.write(json.dumps(categories))

    top_cat = None
    top_score = 0

    for category in categories:
        if categories[category] > top_score:
            top_score = categories[category]
            top_cat = category

    print("(%5d)" % counter.value, cur, "->", top_cat, str(top_score))


def __main__():
    wiki_data = load_wiki_data()
    final_writer = open('data/final.tsv', 'w')
    with open('data/friends_aligned.tsv', 'r') as reader:
        counter = Counter()
        for line in reader:
            row = line.split("\t")
            process(row, final_writer, counter, wiki_data)

    final_writer.close()

__main__()