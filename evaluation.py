from flatten.joint_flatten import JointFlatten
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
    GreedyFlatten(user2cat),
    JointFlatten(user2cat)
]

# Total evaluation values
avg_old_loss = 0.0
avg_changes = {}
avg_new_loss = {}
avg_diff = {}
avg_diff_base = 0.0

top5_prec = {}
top10_prec = {}
top15_prec = {}

for flatten in flattens:
    name = flatten.__class__.__name__
    avg_new_loss[name] = 0.0
    avg_changes[name] = 0.0
    avg_diff[name] = 0.0

    top5_prec[name] = 0.0
    top10_prec[name] = 0.0
    top15_prec[name] = 0.0

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
        top_categories = Flatten._get_top_categories(categories, 15)
        top_category, best, diff = best_score_diff(categories, top_categories)
        print("[%3d] Top category: %s (p:%.2f, d:%.2f) " % (counter, dictionary.cat_index[top_category], best, diff))
        avg_diff_base += diff

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
            top_updated_categories = Flatten._get_top_categories(updated_categories, 15)
            top5_int = len(np.intersect1d(top_categories[:5], top_updated_categories[:5]))
            top10_int = len(np.intersect1d(top_categories[:10], top_updated_categories[:10]))
            top15_int = len(np.intersect1d(top_categories[:15], top_updated_categories[:15]))
            top5_prec[name] += top5_int
            top10_prec[name] += top10_int
            top15_prec[name] += top15_int
            top_category, best, diff = best_score_diff(updated_categories, top_updated_categories)
            print("[%3d] %s" % (counter, name))
            print("[%3d]    Top category: %s (p:%.2f, d:%.2f) " % (counter, dictionary.cat_index[top_category], best, diff))
            print("[%3d]    Diff from uniform: %.3f" % (counter, new_loss))
            print("[%3d]    Friends suggested: %d" % (counter, changes))
            print("[%3d]    Intersects Top5: %d Top10: %d Top15: %d" % (counter, top5_int, top10_int, top15_int))
            avg_new_loss[name] += new_loss
            avg_changes[name] += changes
            avg_diff[name] += diff

avg_old_loss /= counter
avg_diff_base /= counter
for flatten in flattens:
    name = flatten.__class__.__name__
    avg_new_loss[name] /= counter
    avg_changes[name] /= counter
    avg_diff[name] /= counter
    top5_prec[name] /= counter * 5
    top10_prec[name] /= counter * 10
    top15_prec[name] /= counter * 15

print("Final evaluation: ")
print(" Avg. old loss: %.2f" % avg_old_loss)
print(" Avg. old avg diff: %.2f" % avg_diff_base)
for flatten in flattens:
    name = flatten.__class__.__name__
    print(" [%s] Avg. new loss: %.2f" % (name, avg_new_loss[name]))
    print(" [%s] Avg. new friends: %.2f" % (name, avg_changes[name]))
    print(" [%s] Avg. diff: %.2f" % (name, avg_diff[name]))
    print(" [%s] Top  5 precision: %.2f" % (name, top5_prec[name]))
    print(" [%s] Top 10 precision: %.2f" % (name, top10_prec[name]))
    print(" [%s] Top 15 precision: %.2f" % (name, top15_prec[name]))
