import json
from urllib import request

API_KEY = "d504d8905694b7fbcf0968ab86172884"
ISBNS = [
    "978-3-319-46523-4",  # 2016
    "978-3-319-25007-6",  # 2015
    "978-3-319-11915-1"   # 2014
]


def download(isbn, start):
    url = "http://api.springer.com/metadata/json?q=isbn:%s&api_key=%s&p=241&s=%d" % (isbn, API_KEY, start)

    with request.urlopen(url) as raw:
        response = json.loads(raw.read().decode('utf-8'))
        total = int(response['result'][0]['total'])
        papers = response['records']
    print('Dowloaded %d papers for ISBN "%s" starting from %d' % (len(papers), isbn, start))

    if start+len(papers) < total:
        for paper in download(isbn, start+len(papers)):
            papers.append(paper)

    return papers


def clear_abstract(abstract):
    if abstract[0:8].lower() == "abstract":
        return abstract[8:]
    return abstract


def __main__():
    papers = []
    authors = {}
    for isbn in ISBNS:
        for paper in download(isbn, 0):
            abstract = clear_abstract(paper['abstract'])

            paper_authors = []
            for author in paper['creators']:
                author = author['creator']
                paper_authors.append(author)
                if author not in authors:
                    authors[author] = {
                        'count': 0,
                        'title_context': '',
                        'context': ''
                    }

                authors[author]['count'] += 1
                prefix = ' '
                if len(authors[author]['context']) == 0:
                    prefix = ''
                authors[author]['title_context'] += prefix + paper['title'].replace('\t', ' ').replace('\n', '')
                authors[author]['context'] += prefix + abstract.replace('\t', ' ').replace('\n', '')

            papers.append({
                'doi': paper['doi'],
                'title': paper['title'],
                'authors': authors,
                'abstract': abstract
            })

    print("Downloaded %d papers" % len(papers))
    with open('data/papers.json', 'w') as output:
        json.dump(papers, output)

    first = True
    with open('data/authors.tsv', 'w') as output:
        for key in authors:
            if not first:
                output.write('\n')
            first = False

            output.write(key)
            output.write('\t')
            output.write(str(authors[key]['count']))
            output.write('\t')
            output.write(authors[key]['title_context'])
            output.write('\t')
            output.write(authors[key]['context'])

__main__()
