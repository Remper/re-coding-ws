import numpy as np
from os import path


class Dictionary:
    """
    Parses DBpedia -> categories file and stores the results into memory
    """
    def __init__(self, index, cat_index, dictionary):
        self.index = index
        self.cat_index = cat_index
        self.dictionary = dictionary

    @staticmethod
    def restore_from_data_folder(folder):
        cat_index = []
        index = []
        dictionary = {}

        cat_dict = {}
        with open(path.join(folder, 'taxonomy.tsv'), 'r') as reader:
            for line in reader:
                cat = line.rstrip()
                cat_dict[cat] = len(cat_index)
                cat_index.append(cat)

        with open(path.join(folder, 'en_resolved_final.tsv'), 'r') as reader:
            counter = 0
            for line in reader:
                row = line.rstrip().split("\t")

                categories = np.zeros(len(cat_index), dtype=np.float16)
                for idx in range(1, len(row), 2):
                    categories[cat_dict[row[idx]]] = float(row[idx+1])

                dictionary[row[0]] = len(index)
                dictionary[len(index)] = row[0]
                index.append(categories)

                counter += 1
                if counter % 500000 == 0:
                    print("Processed %.1fm pages" % (float(counter) / 1000000))
        print("Done (%d)" % counter)

        print("Stacking")
        index = np.stack(index)
        print("Done")
        return Dictionary(index, cat_index, dictionary)


class User:
    """
    Simple user representation
    """
    def __init__(self, id, name=None, screen_name=None):
        self.id = id
        self.friends = set()
        self.name = "unknown"
        self.screen_name = "unknown"
        if name is not None:
            self.name = name
        if screen_name is not None:
            self.screen_name = screen_name

    def __repr__(self):
        return "User(%s)" % self.screen_name

    def __eq__(self, other):
        if isinstance(other, User):
            return (self.id == other.id) or (self.screen_name == other.screen_name)
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.__repr__())

    user_rep = {}

    @staticmethod
    def get_user(id, name=None, screen_name=None):
        if isinstance(id, User):
            return id

        if id not in User.user_rep:
            User.user_rep[id] = User(id, name, screen_name)
        return User.user_rep[id]


class User2Cat:
    """
    Takes the user and transforms it to the set of categories
    """
    def __init__(self, dictionary):
        self.dictionary = dictionary

    def categorize(self, user):
        # Computing raw sum
        categories, num_friends = self.compute_raw_sum(user)
        if num_friends == 0:
            return categories

        # Normalising
        categories /= num_friends

        return categories

    def compute_raw_sum(self, user):
        # Retrieving category list from dictionary
        categorized_friends = []
        for friend in user.friends:
            if friend.screen_name in self.dictionary.dictionary:
                idx = self.dictionary.dictionary[friend.screen_name]
                friend_cats = self.dictionary.index[idx]
                categorized_friends.append(friend_cats)

        if len(categorized_friends) == 0:
            return np.zeros(self.dictionary.index.shape[1]), 0

        categories = np.sum(categorized_friends, axis=0)

        return categories, len(categorized_friends)

    def lookup(self, user):
        pass