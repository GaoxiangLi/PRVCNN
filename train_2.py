import tensorflow as tf
import numpy as np
import inference_2
from sklearn.metrics import r2_score
import matplotlib.pyplot as plt
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
LEARNING_RATE_BASE = 0.001
LEARNING_RATE_DECAY = 0.99
BATCH_SIZE = 25
REGULARIZATION_RATE = 0.01
TRAINING_STEPS = 50000
MOVING_AVERAGE_DECAY = 0.99
NUM_EXAMPLE = 308


def train():
    x = tf.placeholder(tf.float32, [None, 1024], name='x-input')
    y_ = tf.placeholder(tf.float32, [None, 1], name='y-input')

    regularizer = tf.contrib.layers.l2_regularizer(REGULARIZATION_RATE)
    # y = inference_2.inference(x, regularizer)
    y = inference_2.inference2(x, regularizer)

    global_step = tf.Variable(0, trainable=False)
    variable_averages = tf.train.ExponentialMovingAverage(MOVING_AVERAGE_DECAY, global_step)
    variables_averages_op = variable_averages.apply(tf.trainable_variables())
    mse = tf.reduce_mean(tf.square(y_ - y))
    mse_mean = tf.reduce_mean(mse)
    loss = mse_mean + tf.add_n(tf.get_collection('losses'))

    learning_rate = tf.train.exponential_decay(

        LEARNING_RATE_BASE,
        global_step,
        NUM_EXAMPLE / BATCH_SIZE, LEARNING_RATE_DECAY,
        staircase=True)

    train_op = tf.train.AdamOptimizer(learning_rate).minimize(loss, global_step=global_step)
    with tf.control_dependencies([train_op, variables_averages_op]):
        train_op = tf.no_op(name='train')

    # features = np.load('C:/Users/Shawn/PycharmProjects/tensorflow_practice/data/X.npy')
    features = np.load('./X.npy')
    labels = np.load('./Y.npy')
    features = features.reshape([NUM_EXAMPLE, -1])
    labels = labels.reshape([NUM_EXAMPLE, -1])

    with tf.Session() as sess:
        tf.global_variables_initializer().run()
        # acc_list, cost_list = [], []
        pred_list = []
        true_list = []
        for i in range(TRAINING_STEPS):
            xs = features[i % NUM_EXAMPLE]
            xs = xs[0:1024]
            ys = labels[i % NUM_EXAMPLE]
            for j in range(BATCH_SIZE - 1):
                xs = np.append(xs, features[(i + j) % NUM_EXAMPLE, 0:1024])
                ys = np.append(ys, labels[(i + j) % NUM_EXAMPLE])
            xs = np.reshape(xs, [-1, 1024])
            ys = np.reshape(ys, [-1, 1])
            _, y_pred, y_true, loss_value = sess.run([train_op, y, y_, mse_mean],
                                                     feed_dict={x: xs, y_: ys})
            acc = r2_score(y_true, y_pred)
            # acc_list.append(acc)
            # cost_list.append(loss_value)
            if i % 100 == 0:
                print(
                    "After %d training step(s), mse loss mean on training batch is %g. R2 is %g" % (i, loss_value, acc))
        for i in range(NUM_EXAMPLE):
            xs = features[i]
            xs = xs[0:1024]
            ys = labels[i]
            xs = np.reshape(xs, [-1, 1024])
            ys = np.reshape(ys, [-1, 1])
            y1, y2 = sess.run([y, y_], feed_dict={x: xs,
                                                  y_: ys})
            y1 = y1[0]
            y2 = y2[0]
            pred_list.append(y1)
            true_list.append(y2)
        r2 = r2_score(true_list, pred_list)
        print("Test r2 is:", r2)
    # fig = plt.figure()
    # x = range(0, TRAINING_STEPS)
    # ax = plt.subplot()
    # ax.scatter(x, acc_list, alpha=0.5)
    # plt.xlabel('step')
    # plt.ylabel('R2')
    # plt.show()


def main(argv=None):
    train()


if __name__ == '__main__':
    main()
