from flatten.user2cat import Dictionary, User2Cat
from flatten.flatten import *
from time import time
from os import path
from utils import data
import numpy as np

from utils.data import best_score_diff

SAMPLES = 100

# Load a dictionary with categorical data
watch = time()
dictionary = Dictionary.restore_from_data_folder('data')
print("Done in %.2f seconds" % (time() - watch))

# Initialise user2cat
user2cat = User2Cat(dictionary)

# Initialise flattens
flattens = [
    RandomFlatten(user2cat),
    GreedyFlatten(user2cat)
]

# Total evaluation values
avg_old_loss = 0.0
avg_changes = {}
avg_new_loss = {}
for flatten in flattens:
    avg_new_loss[flatten.__class__.__name__] = 0.0
    avg_changes[flatten.__class__.__name__] = 0.0

# Run the entire pipeline for a subset of samples
with open(path.join('data', 'alignments.tsv'), 'r') as reader:
    counter = 0
    for line in reader:
        # Parsing user data
        row = line.rstrip().split('\t')
        user = data.user_from_alignments(row)

        # Retrieving friends
        data.resolve_friends(user)

        # Mapping user to categories
        categories = user2cat.categorize(user)

        # Some reporting
        if np.sum(categories) == 0:
            print("User %s (@%s) can't be aligned to any categories" % (user.name, user.screen_name))
            continue

        counter += 1
        if counter > SAMPLES:
            break

        print("[%3d] Cat dist: %s for user %s (@%s)" % (counter, str(categories), user.name, user.screen_name))
        top_category, best, diff = best_score_diff(categories, Flatten._get_top_categories(categories, 2))
        print("[%3d] Top category: %s (p:%.2f, d:%.2f) " % (counter, dictionary.cat_index[top_category], best, diff))

        # Flattening the distribution
        results = []
        for flatten in flattens:
            updated_user, changes = flatten.update(user)
            results.append((user2cat.categorize(updated_user), changes, flatten.__class__.__name__))

        # Evaluation
        old_loss = data.compute_error(categories)
        avg_old_loss += old_loss
        print("[%3d] Old diff from uniform: %.3f" % (counter, old_loss))
        for updated_categories, changes, name in results:
            new_loss = data.compute_error(updated_categories)
            top_category, best, diff = best_score_diff(updated_categories, Flatten._get_top_categories(updated_categories, 2))
            print("[%3d] %s" % (counter, name))
            print("[%3d]    Top category: %s (p:%.2f, d:%.2f) " % (counter, dictionary.cat_index[top_category], best, diff))
            print("[%3d]    Diff from uniform: %.3f" % (counter, new_loss))
            print("[%3d]    Friends suggested: %d" % (counter, changes))
            avg_new_loss[name] += new_loss
            avg_changes[name] += changes

avg_old_loss /= counter
for flatten in flattens:
    avg_new_loss[flatten.__class__.__name__] /= counter
    avg_changes[flatten.__class__.__name__] /= counter

print("Final evaluation: ")
print(" Avg. old loss: %.2f" % avg_old_loss)
for flatten in flattens:
    name = flatten.__class__.__name__
    print(" [%s] Avg. new loss: %.2f" % (name, avg_new_loss[name]))
    print(" [%s] Avg. new friends: %.2f" % (name, avg_changes[name]))
