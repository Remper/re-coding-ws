
data = set()
with open('data/en.csv', 'r') as reader:
    counter = 0
    for line in reader:
        row = line.rstrip().split("\t")
        for idx in range(1, len(row), 2):
            data.add(row[idx])
        counter += 1
        if counter % 100000 == 0:
            print("Processed %.1fm pages" % (float(counter)/1000000))
print("Done (%d)" % counter)

writer = open('data/taxonomy.tsv', 'w')
first = True
for category in data:
    if not first:
        writer.write('\n')
    first = False
    writer.write(category)
writer.close()
