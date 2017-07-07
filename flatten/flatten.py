import numpy as np
import random
from flatten.user2cat import User


class Flatten:
    """
    Takes the list of followees and proposes an updated one
    """

    def __init__(self, user2cat):
        self.user2cat = user2cat

    @staticmethod
    def _get_top_categories(categories):
        return np.argsort(categories)[-15:][::-1]

    def get_random_alignable_friend(self, user):
        choice_list = list(self.user2cat.gold)
        while True:
            key = random.choice(choice_list)
            if user.has_friend(key):
                continue

            entity_id = self.user2cat.gold[key]
            if entity_id not in self.user2cat.dictionary.dictionary:
                continue

            return User(-hash(key), screen_name=key)

    def compute_category_similarity(self, top_categories, updated_user):
        categories = self.user2cat.categorize(updated_user)
        new_top_categories = Flatten._get_top_categories(categories)
        intersection = np.intersect1d(top_categories, new_top_categories)
        return len(intersection)

    def update(self, user):
        # Retrieving the list of categories
        categories = self.user2cat.categorize(user)

        # Creating the new user that will accommodate new friends
        updated_user = User(user.id, user.name, user.screen_name)
        updated_user.friends = list(user.friends)

        # Randomly adding new followers until the top 15 categories are phased out
        top_categories = Flatten._get_top_categories(categories)
        changes = 0
        while self.compute_category_similarity(top_categories, updated_user) > 0 and changes < 100:
            updated_user.add_friend(self.get_random_alignable_friend(updated_user))
            changes += 1

        return updated_user, changes
