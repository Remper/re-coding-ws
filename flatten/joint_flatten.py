from time import time

from flatten.flatten import Flatten
import tensorflow as tf
import numpy as np

from utils import data


class JointFlatten(Flatten):
    def __init__(self, user2cat):
        super().__init__(user2cat)

        print("Defining model")
        watch = time()
        self._define_model(user2cat.dictionary.index)
        print("Done defining model in %.2f seconds" % (time() - watch))

    def _propose(self, user, categories):
        old_friends = np.full(self.user2cat.dictionary.index.shape[0], False, dtype=np.bool)
        for friend in user.friends:
            if friend.screen_name in self.user2cat.dictionary.dictionary:
                old_friends[self.user2cat.dictionary.dictionary[friend.screen_name]] = True

        new_friends = self._optimise(old_friends)
        for index in np.nonzero(new_friends)[0]:
            user.friends.add(self._resolve_friend(index))

        return True

    def _define_model(self, dictionary):
        mask_size = dictionary.shape[0]

        # Loading dictionary as constant
        self._F = tf.constant(dictionary, dtype=tf.float32)

        # Current list of friends
        self._bin_old_friends = tf.placeholder(dtype=tf.bool, shape=(mask_size, ))
        old_friends = tf.select(self._bin_old_friends, *self._pos_zero_like(self._bin_old_friends))

        learning_rate = 0.1
        with tf.variable_scope('optimisation_params') as vs:
            w = tf.get_variable('w', shape=(mask_size, ),
                                initializer=tf.constant_initializer(learning_rate),
                                trainable=True)
        tf.summary.histogram('weights', w)

        # New list of friends
        self._new_friends = self._binarize(w)

        # Total list of friends
        with tf.name_scope('friends_combination') as comb:
            raw_total_friends = tf.add(old_friends, self._new_friends, name='raw_total_friends')
            total_friends = tf.clip_by_value(raw_total_friends, 0, 1, name='total_friends')

        # Saving objective tensor
        self._J = self._objective(old_friends, total_friends, 0.1)

        optimizer = tf.train.GradientDescentOptimizer(learning_rate=learning_rate)
        self._global_step = tf.Variable(0, name='global_step', trainable=False)

        # Compute gradiends up to binarization
        friends_grad, = tf.gradients(self._J, self._new_friends)
        # Filtering out friends that shouldn't change
        tf.summary.histogram('friends_grad', friends_grad)
        # Gradient for the binarized weights should be the same as for the weights themselves
        # Applying gradient
        self._min_op = optimizer.apply_gradients([(friends_grad, w)], global_step=self._global_step)

    def _objective(self, old_friends, total_friends, alpha):

        with tf.name_scope('categories') as scope:
            categories = self._categories(total_friends)
            n = tf.constant(categories.get_shape()[0].value, dtype=tf.float32, name='num_categories')
            tf.summary.histogram('categories_unclipped', categories)
            tf.summary.scalar('categories_unclipped_contrib', - tf.reduce_mean(tf.log(categories)))
            categories = tf.clip_by_value(categories, 1e-7, 1)
            tf.summary.histogram('categories_clipped', categories)

        with tf.name_scope('objective') as scope:
            amount_total_friends = tf.reduce_sum(total_friends, name='amount_total_friends')
            amount_old_friends = tf.reduce_sum(old_friends, name='amount_old_friends')
            tf.summary.scalar('amount_total_friends', amount_total_friends)
            fr_obj = alpha * (amount_total_friends - amount_old_friends)
            D =  - tf.log(n) - tf.reduce_mean(tf.log(categories)) - tf.log(n)
            J = D + fr_obj
        tf.summary.scalar('D', D)
        tf.summary.scalar('fr_obj', fr_obj)
        tf.summary.scalar('J', J)

        return J

    def _categories(self, friends):
        return tf.matmul(tf.reshape(friends, [1, -1]), self._F) / tf.reduce_sum(friends)

    def _optimise(self, friends):
        with tf.Session() as session:
            print("Initialising model")
            watch = time()
            session.run(tf.global_variables_initializer())
            print("Done initialising model in %.2f seconds" % (time() - watch))

            merged = tf.summary.merge_all()
            summary_writer = tf.summary.FileWriter('log', graph=session.graph)
            J = session.run(self._J, feed_dict={self._bin_old_friends: friends})
            old_J = J + 100.0
            step = 0
            while old_J - J > 0.01 or step < 10000:
                old_J = J
                for idx in range(0, 5):
                    _, J, summary, step = session.run([self._min_op, self._J, merged, self._global_step],
                                                                   feed_dict={self._bin_old_friends: friends})

                if step % 1000 == 0:
                    print("iter: %d loss: %.2f" % (step, J))

                # Write summaries
                summary_writer.add_summary(summary, global_step=step)

            print("Total iterations: %d" % step)
            new_friends = session.run(self._new_friends)

        return new_friends

    def _pos_zero_like(self, tensor):
        return (tf.constant(1, dtype=tf.float32, shape=tensor.get_shape()),
                tf.constant(0, dtype=tf.float32, shape=tensor.get_shape()))

    def _binarize(self, tensor):
        return tf.select(tensor > 0, *self._pos_zero_like(tensor))
        #return tensor > 0

