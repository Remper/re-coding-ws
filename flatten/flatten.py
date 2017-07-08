import numpy as np
import random
from flatten.user2cat import User
from utils.data import compute_error


class Flatten:
    """
    Takes the list of followees and proposes an updated one
    """

    def __init__(self, user2cat):
        self.user2cat = user2cat

    @staticmethod
    def _get_top_categories(categories):
        return np.argsort(categories)[-15:][::-1]

    def compute_category_similarity(self, top_categories, current_categories):
        new_top_categories = Flatten._get_top_categories(current_categories)
        intersection = np.intersect1d(top_categories, new_top_categories)
        return len(intersection)

    def _resolve_friend(self, index):
        key = self.user2cat.dictionary.dictionary[index]
        return User(-hash(key), screen_name=key)

    def update(self, user):

        # Creating the new user that will accommodate new friends
        updated_user = User(user.id, user.name, user.screen_name)
        updated_user.friends = set(user.friends)
        amount_friends = len(updated_user.friends)

        # Retrieving the list of categories
        current_categories = self.user2cat.categorize(user)
        # Randomly adding new followers until the top 15 categories are phased out
        top_categories = Flatten._get_top_categories(current_categories)
        changes = 0
        while changes < 100:
            self._propose(updated_user, current_categories)
            delta = len(updated_user.friends) - amount_friends
            amount_friends = len(updated_user.friends)
            if delta == 0:
                break

            changes += delta
            current_categories = self.user2cat.categorize(updated_user)

        return updated_user, changes

    def _propose(self, user, categories):
        raise NotImplementedError("_propose function has to be defined")


class RandomFlatten(Flatten):
    """
    Proposes the updated list of followees by randomly adding new ones until old top categories a phased out
    """

    def _propose(self, user, categories):
        while True:
            friend = self._resolve_friend(random.randint(0, self.user2cat.dictionary.index.shape[0]-1))
            if friend not in user.friends:
                user.friends.add(friend)
                return


class GreedyFlatten(Flatten):
    """
    Proposes the updated list of followees by adding the best cross-entropy-reducing candidate one at the time
    """

    def _get_best_friend_scores(self, user):
        # Get the unnormalised sum of categories
        raw_categories, num_friends = self.user2cat.compute_raw_sum(user)
        expected_probability = 1.0 / len(raw_categories)

        # Getting all possible variations of the new friend list
        raw_categories = self.user2cat.dictionary.index + raw_categories
        num_friends += 1

        # Normalizing using the new total
        raw_categories /= num_friends

        # Computing cross entropy row-wise
        eps = 1e-7
        raw_categories = np.multiply(np.log2(np.clip(raw_categories, eps, 1 - eps)), expected_probability)
        raw_categories = -np.sum(raw_categories, axis=1)

        # Finding the best friend
        return raw_categories

    def _filter_scores(self, user, scores):
        # Find the best score filtering out invalid ones
        raw_indexes = np.argsort(scores)
        for index in raw_indexes:
            if self._resolve_friend(index) not in user.friends:
                return index

    def _propose(self, user, categories):
        self._propose_recursively(user, categories, compute_error(categories))

    def _propose_recursively(self, user, categories, best_total_score, deep=0):
        # Finding the best friend
        scores = self._get_best_friend_scores(user)
        index = self._filter_scores(user, scores)
        best_cur_score = scores[index]

        user.friends.add(self._resolve_friend(index))

        # Found the one that is better than baseline
        if best_cur_score < best_total_score - 0.1   :
            return True

        # Didn't found one
        if deep > 0:
            # Can't go deeper – failure
            user.friends.remove(self._resolve_friend(index))
            return False

        # Trying to go deeper and processing result
        result = self._propose_recursively(user, categories, best_total_score, deep+1)
        if not result:
            user.friends.remove(self._resolve_friend(index))
        return result


class OptFlatten(Flatten):
    """
    Proposes the updated list of followees via optimising a joint objective over the entire list of possible friends
    """

    def _propose(self, user, categories):
        pass

    def _should_continue(self, categories, changes, top_categories):
        pass