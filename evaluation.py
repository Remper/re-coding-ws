from flatten.user2cat import Dictionary, User2Cat
from flatten.flatten import Flatten
from time import time
from os import path
from utils import data
import numpy as np

SAMPLES = 100

# Load a dictionary with categorical data
watch = time()
dictionary = Dictionary.restore_from_data_folder('data')
print("Done in %.2f seconds" % (time() - watch))

# Load gold standard
watch = time()
gold = data.load_gold_data()
print("Done in %.2f seconds" % (time() - watch))

# Initialise user2cat
user2cat = User2Cat(dictionary, gold)

# Initialise flatten
flatten = Flatten(user2cat)

# Total evaluation values
avg_changes = 0.0
avg_old_loss = 0.0
avg_new_loss = 0.0

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

        # Flattening the distribution
        updated_user, changes = flatten.update(user)
        updated_categories = user2cat.categorize(updated_user)

        print("[%3d] Upd dist: %s for user %s (@%s)" % (counter, str(updated_categories), updated_user.name, updated_user.screen_name))

        # Evaluation
        old_loss = data.compute_error(categories)
        new_loss = data.compute_error(updated_categories)
        print("[%3d] Old diff from uniform: %.3f" % (counter, old_loss))
        print("[%3d] New diff from uniform: %.3f" % (counter, new_loss))
        print("[%3d] Friends suggested: %d" % (counter, changes))

        avg_changes += changes
        avg_old_loss += old_loss
        avg_new_loss += new_loss
avg_changes /= counter
avg_old_loss /= counter
avg_new_loss /= counter

print("Final evaluation: ")
print(" Avg. new friends: %.2f" % avg_changes)
print(" Avg. old loss: %.2f" % avg_old_loss)
print(" Avg. new loss: %.2f" % avg_new_loss)