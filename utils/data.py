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
            if counter % 100000 == 0:
                print("Processed %.1fm pages" % (float(counter)/1000000))
    print("Done (%d)" % counter)
    return data
