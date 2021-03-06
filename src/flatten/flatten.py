import numpy as np
import random
from flatten.user2cat import User
from utils.data import compute_error


class Flatten:
    """
    Takes the list of followees and proposes an updated one
    """

    def __init__(self, user2cat, changes=100):
        self.user2cat = user2cat
        self.changes = changes

    def __str__(self):
        return "%s(%d)" % (self.__class__.__name__, self.changes)

    @staticmethod
    def _get_top_categories(categories, n=15):
        return np.argsort(categories)[-n:][::-1]

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
        while changes < self.changes:
            stop = self._propose(updated_user, current_categories)
            delta = len(updated_user.friends) - amount_friends
            amount_friends = len(updated_user.friends)
            changes += delta
            if delta == 0 or (stop is not None and stop):
                break

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

    def __init__(self, user2cat, changes=100, alpha=0.01):
        super().__init__(user2cat, changes)
        self.alpha = alpha

    def __str__(self):
        return "%s(%d, %f)" % (self.__class__.__name__, self.changes, self.alpha)

    def _get_best_friend_scores(self, user):
        # Get the unnormalised sum of categories
        raw_categories, num_friends = self.user2cat.compute_raw_sum(user)

        # Getting all possible variations of the new friend list
        raw_categories = self.user2cat.dictionary.index + raw_categories
        num_friends += 1

        # Normalizing using the new total
        raw_categories /= num_friends

        # Computing KL-divergence row-wise
        raw_categories = compute_error(raw_categories)

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
        if best_cur_score < best_total_score - self.alpha:
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