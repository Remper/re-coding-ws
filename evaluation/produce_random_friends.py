from time import time
from flatten.user2cat import Dictionary

"""
Suggests friends to follow to produce clear k categories
"""

# Load a dictionary with categorical data
watch = time()
dictionary = Dictionary.restore_from_data_folder('data')
print("Done in %.2f seconds" % (time() - watch))

# Pick category, pick some friends with prob > 0.5 over this category, then counterpick friends to equalize
