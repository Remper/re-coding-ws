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

directory = '/Users/remper/Downloads/recode/prod-wtf'

avg_loss = {}
avg_diff = {}
top5_prec = {}
top10_prec = {}
top15_prec = {}

counter = 0
for current_dir in listdir(directory):
    current_path = path.join(directory, current_dir)
    if not path.isdir(current_path) or not path.exists(path.join(current_path, 'suggestions-clean.txt')):
        continue

    counter += 1
    clean_friends = set()
    with open(path.join(current_path, 'suggestions-clean.txt'), 'r') as reader:
        for line in reader:
            clean_friends.add(line.rstrip().lower())

    top_updated_categories = None
    for file in ['suggestions-pre.txt', 'suggestions-post.txt']:
        if "suggestions" in file:
            user = User(-241, "Target user", "target")
            with open(path.join(current_path, file), 'r') as reader:
                for line in reader:
                    line = line.rstrip().lower()
                    if line in clean_friends:
                        continue
                    user.friends.add(User(-hash(line), screen_name=line))

            if file not in top5_prec:
                top5_prec[file] = 0.0
                top10_prec[file] = 0.0
                top15_prec[file] = 0.0
                avg_loss[file] = 0.0
                avg_diff[file] = 0.0

            updated_categories = user2cat.categorize(user)
            loss = data.compute_error(updated_categories)
            top_categories = top_updated_categories
            top_updated_categories = Flatten._get_top_categories(updated_categories, 15)
            top_category, best, diff = data.best_score_diff(updated_categories, top_updated_categories)

            print("%s" % file)
            print("    Top category: %s (p:%.2f, d:%.2f) " % (dictionary.cat_index[top_category], best, diff))
            print("    Score: %.2f" % loss)
            print("    Friends: %d" % len(user.friends))

            if top_categories is not None:
                top5_int = len(np.intersect1d(top_categories[:5], top_updated_categories[:5]))
                top10_int = len(np.intersect1d(top_categories[:10], top_updated_categories[:10]))
                top15_int = len(np.intersect1d(top_categories[:15], top_updated_categories[:15]))
                top5_prec[file] += top5_int
                top10_prec[file] += top10_int
                top15_prec[file] += top15_int
                print("    Intersects Top5: %d Top10: %d Top15: %d" % (top5_int, top10_int, top15_int))

            print()

            avg_loss[file] += loss
            avg_diff[file] += diff

print()
for file in avg_loss:
    avg_loss[file] /= counter
    avg_diff[file] /= counter
    top5_prec[file] /= counter * 5
    top10_prec[file] /= counter * 10
    top15_prec[file] /= counter * 15

    print("Average for %s" % file)
    print("    Score: %.2f" % avg_loss[file])
    print("    Diff: %.2f" % avg_diff[file])
    print("    Top  5 precision: %.2f" % (top5_prec[file]))
    print("    Top 10 precision: %.2f" % (top10_prec[file]))
    print("    Top 15 precision: %.2f" % (top15_prec[file]))