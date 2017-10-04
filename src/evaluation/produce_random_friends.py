from time import time

from flatten.flatten import *
from flatten.joint_flatten import JointFlatten
from flatten.user2cat import Dictionary, User2Cat
import random
import numpy as np

from utils import data

"""
Suggests friends to follow to produce clear k categories
"""

# Load a dictionary with categorical data
watch = time()
dictionary = Dictionary.restore_from_data_folder('../data')
print("Done in %.2f seconds" % (time() - watch))

# Pick category
category_whitelist = [32, 33, 47, 24, 23]
category = random.choice(category_whitelist) #random.randint(0, dictionary.index.shape[1]-1)
scores = dictionary.index[:, category]

# Initialise user2cat
user2cat = User2Cat(dictionary)

# Initialise flattens
flattens = [
    JointFlatten(user2cat)
]

# Pick some friends with prob > 0.5 over this category
candidates = np.random.choice(np.nonzero(scores > 0.5)[0], 30, replace=False)

user = User.get_user(-241, "Target user", "target")
for candidate in candidates:
    key = dictionary.dictionary[candidate]
    user.friends.add(User(-hash(key), screen_name=key))

categories = user2cat.categorize(user)
top_category, best, diff = data.best_score_diff(categories, Flatten._get_top_categories(categories, 2))
old_loss = data.compute_error(categories)

print("Chosen category: %s" % dictionary.cat_index[category])
print("Top category: %s (p:%.2f, d:%.2f) " % (dictionary.cat_index[top_category], best, diff))
print("Follow choices: [\"%s\"]" % '", "'.join([ele.screen_name for ele in user.friends]))
print("Initial score: %.3f" % old_loss)


# Counterpick friends to equalize
results = []
for flatten in flattens:
    updated_user, changes = flatten.update(user)
    results.append((user2cat.categorize(updated_user), updated_user, changes, flatten.__class__.__name__))

# Evaluation
for updated_categories, updated_user, changes, name in results:
    new_loss = data.compute_error(updated_categories)
    top_category, best, diff = data.best_score_diff(updated_categories, Flatten._get_top_categories(updated_categories, 2))
    print("%s" % name)
    print("    Top category: %s (p:%.2f, d:%.2f) " % (dictionary.cat_index[top_category], best, diff))
    print("    Projected score: %.3f" % new_loss)
    print("    Friends suggested: %d" % changes)
    print("    Complete list: [\"%s\"]" % '", "'.join([ele.screen_name for ele in updated_user.friends]))

