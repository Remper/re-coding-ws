"""
Converts entity_id -> categories list to twitter -> categories via SocialLink
"""

import psycopg2

QUERY = """
    SELECT a.resource_id, a.uid, a.score, u.object->'screen_name', u.object->'name' FROM alignments AS a
    LEFT JOIN user_objects AS u ON a.uid = u.uid
    WHERE resource_id = %s	
    ORDER BY score DESC LIMIT 2 
"""

RESOLVE_QUERY = """
    SELECT object->'screen_name', object->'name' FROM user_objects AS a
    WHERE uid = %s
"""


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
            data[row[0]] = row[1]
            if counter % 10000 == 0:
                print("Processed %.0fk alignments" % (float(counter)/1000))
    print("Done (%d)" % counter)
    return data


# Connecting to the database
conn = psycopg2.connect(user="nechaev", password="", port=5433, dbname="alignments", host="localhost")
gold = load_gold_data()


def align_entity(entity):
    if entity in gold:
        return gold[entity]

    with conn.cursor() as cursor:
        try:
            cursor.execute(QUERY, (entity, ))
        except BaseException as e:
            conn.rollback()
            print("Error while handling entity %s" % entity)
            print(e)
            return None
        rows = cursor.fetchall()

        if len(rows) == 0:
            return None
        first_score = rows[0][2]
        second_score = 0.0
        if len(rows) > 1:
            second_score = rows[1][2]

        if first_score <= 0.4 or first_score - second_score <= 0.4:
            return None
        return rows[0][3]

filename = 'data/en_resolved.tsv'
output_filename = 'data/en_resolved_final.tsv'

with open(output_filename, 'w') as writer:
    with open(filename, 'r') as reader:
        for line in reader:
            row = line.rstrip().split('\t')
            aligned_entity = align_entity(row[0])

            if aligned_entity is None:
                continue

            writer.write(str(aligned_entity))
            for element in row[1:]:
                writer.write('\t')
                writer.write(element)
            writer.write('\n')

conn.close()
