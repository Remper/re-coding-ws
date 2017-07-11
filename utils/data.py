from flatten.user2cat import User
from utils.queries import SMT_API_RECODE_FRIENDS

from urllib import request
from urllib.error import HTTPError
from urllib.parse import urlencode
from time import sleep
import json
import numpy as np


def load_wiki_data():
    print("Loading category information")
    data = {}
    with open('data/en_resolved.tsv', 'r') as reader:
        counter = 0
        for line in reader:
            row = line.rstrip().split("\t")
            categories = {}
            for idx in range(1, len(row), 2):
                categories[row[idx]] = float(row[idx + 1])
            data[row[0]] = categories
            counter += 1
            if counter % 100000 == 0:
                print("Processed %.1fm pages" % (float(counter) / 1000000))
    print("Done (%d)" % counter)
    return data


def best_score_diff(categories, scores):
    best_score = categories[scores[0]]
    return scores[0], best_score, best_score - categories[scores[1]]


def load_gold_data():
    print("Loading gold standard")
    data = {}
    with open('data/gold.csv', 'r') as reader:
        counter = 0
        for line in reader:
            counter += 1
            if counter == 0:
                continue
            row = line.rstrip().split(",")
            data[row[1]] = row[0]
            if counter % 10000 == 0:
                print("Processed %.0fk alignments" % (float(counter) / 1000))
    print("Done (%d)" % counter)
    return data


def user_from_alignments(row):
    return User.get_user(int(row[1]), row[3], row[2])


def get_friends(uid):
    url = SMT_API_RECODE_FRIENDS + '?' + urlencode({'uid': uid})

    try:
        with request.urlopen(url) as raw:
            users = json.loads(raw.read().decode('utf-8'))['data']
    except HTTPError as e:
        print("I guess we have to wait:", e)
        sleep(60)
        users = get_friends(uid)

    return users


def resolve_friends(user):
    for raw_friend in get_friends(user.id):
        friend = User.get_user(raw_friend['id'], raw_friend['name'], raw_friend['screenName'])
        user.friends.add(friend)


def cross_entropy(y_true, y_pred, eps=1e-7):
    y_pred = np.clip(y_pred, eps, 1)
    return - np.sum(y_true * np.log2(y_pred), axis=len(y_pred.shape) - 1)


def kl_divergence(y_true, y_pred, eps=1e-7):
    y_pred = np.clip(y_pred, eps, 1)
    y_true = np.clip(y_true, eps, 1)
    return - np.sum(y_true * np.log2(y_pred), axis=len(y_pred.shape) - 1) \
           + np.sum(y_true * np.log2(y_true), axis=len(y_pred.shape) - 1)


def kl_divergence_scalar(y_pred, eps=1e-7):
    y_pred = np.clip(y_pred, eps, 1)
    last_dim = len(y_pred.shape)-1
    num_categories = y_pred.shape[last_dim]
    true_prob = 1.0 / num_categories
    return - np.sum(np.multiply(true_prob, np.log2(y_pred)), axis=last_dim) - np.log2(num_categories)


def compute_error(categories):
    return kl_divergence_scalar(categories)