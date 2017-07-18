from time import time

from flatten.flatten import *
from flatten.user2cat import Dictionary, User2Cat
from os import path, listdir

from utils import data

"""
Compare all parts of the evaluation
"""

# Load a dictionary with categorical data
watch = time()
dictionary = Dictionary.restore_from_data_folder('../data')
print("Done in %.2f seconds" % (time() - watch))

# Initialise user2cat
user2cat = User2Cat(dictionary)

directory = '/Users/remper/Downloads/recode/us-test-3-who-to-follow'
clean_friends = set()
with open(path.join(directory, 'suggestions-clean.txt'), 'r') as reader:
    for line in reader:
        clean_friends.add(line.rstrip().lower())

for file in listdir(directory):
    if "suggestions" in file:
        user = User(-241, "Target user", "target")
        with open(path.join(directory, file), 'r') as reader:
            for line in reader:
                line = line.rstrip().lower()
                if line in clean_friends:
                    continue
                user.friends.add(User(-hash(line), screen_name=line))
        categories = user2cat.categorize(user)
        loss = data.compute_error(categories)
        top_category, best, diff = data.best_score_diff(categories, Flatten._get_top_categories(categories, 2))
        print("%s" % file)
        print("    Top category: %s (p:%.2f, d:%.2f) " % (dictionary.cat_index[top_category], best, diff))
        print("    Score: %.3f" % loss)
        print("    Friends: %d" % len(user.friends))
