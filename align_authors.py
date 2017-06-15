from time import sleep
from urllib import request
from urllib.error import HTTPError
from urllib.parse import urlencode
import json

SMT_API = "http://api.smt.futuro.media/annotate/twitter/simple"


def normalize_name(name):
    name_parts = name.split(', ')
    if len(name_parts) > 1:
        name = name_parts[1] + ' ' + name_parts[0]

    return name


def annotate(name, text):
    url = SMT_API + '?' + urlencode({'token': name, 'text': text[:150], 'ner': 'PERSON'})

    with request.urlopen(url) as raw:
        users = json.loads(raw.read().decode('utf-8'))['data']

    return users


def get_candidates(name, text):
    try:
        return annotate(name, text)
    except HTTPError as e:
        print("I guess we have to wait:", e)
        sleep(60)
    return get_candidates(name, text)


def __main__():
    author_candidates = open('data/candidates.tsv', 'w')
    author_alignments = open('data/alignments.tsv', 'w')
    counter = 0
    with open('data/authors.tsv', 'r') as reader:
        first_alignments = True
        first_candidates = True
        for line in reader:
            row = line.split("\t")
            name = normalize_name(row[0])
            counter += 1
            print("(%3d)" % counter, name)
            candidates = get_candidates(name, row[2] + ' ' + row[3])

            maxScore = 0
            maxCandidate = None
            for candidate in candidates:
                if not first_candidates:
                    author_candidates.write('\n')
                first_candidates = False
                author_candidates.write(name)
                author_candidates.write('\t')
                author_candidates.write(str(candidate['user']['id']))
                author_candidates.write('\t')
                author_candidates.write(candidate['user']['screenName'])
                author_candidates.write('\t')
                author_candidates.write(candidate['user']['name'])
                author_candidates.write('\t')
                author_candidates.write(str(candidate['score']['score']))

                if candidate['score']['score'] > maxScore:
                    maxScore = candidate['score']['score']
                    maxCandidate = candidate['user']

            if maxScore == 0:
                print("No suitable candidate")
                continue
            print("Candidates:", len(candidates), "Alignment:", "@"+maxCandidate['screenName'], "Score:", maxScore)

            if not first_alignments:
                author_alignments.write('\n')
            first_alignments = False
            author_alignments.write(name)
            author_alignments.write('\t')
            author_alignments.write(str(maxCandidate['id']))
            author_alignments.write('\t')
            author_alignments.write(str(maxCandidate['screenName']))
            author_alignments.write('\t')
            author_alignments.write(maxCandidate['name'])
            author_alignments.write('\t')
            author_alignments.write(str(maxScore))

    author_alignments.close()
    author_candidates.close()

__main__()
