def load_wiki_data():
    print("Loading category information")
    data = {}
    with open('data/en_resolved.tsv', 'r') as reader:
        counter = 0
        for line in reader:
            row = line.rstrip().split("\t")
            categories = {}
            for idx in range(1, len(row), 2):
                categories[row[idx]] = float(row[idx+1])
            data[row[0]] = categories
            counter += 1
            if counter % 100000 == 0:
                print("Processed %.1fm pages" % (float(counter)/1000000))
    print("Done (%d)" % counter)
    return data


def load_gold_data():
    print("Loading gold standard")
    data = {}
    with open('data/gold.csv', 'r') as reader:
        counter = 0
        for line in reader:
            counter += 1
            if counter == 0:
                continue
            row = line.rstrip().split(",")
            data[row[1]] = row[0]
            if counter % 10000 == 0:
                print("Processed %.0fk alignments" % (float(counter)/1000))
    print("Done (%d)" % counter)
    return data
