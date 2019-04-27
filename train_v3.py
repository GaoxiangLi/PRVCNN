import tensorflow as tf
import numpy as np
import inference_v3
from sklearn.metrics import r2_score
import matplotlib.pyplot as plt
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
LEARNING_RATE_BASE = 0.001
LEARNING_RATE_DECAY = 0.99
BATCH_SIZE = 25
REGULARIZATION_RATE = 0.01
TRAINING_STEPS = 20000
MOVING_AVERAGE_DECAY = 0.99
NUM_EXAMPLE = 308


def train():
    x = tf.placeholder(tf.float32, [None, 1156], name='x-input')
    y_ = tf.placeholder(tf.float32, [None, 1], name='y-input')
    drop_rate = tf.placeholder(tf.float32, name='drop_rate')
    y = inference_v3.inference2(x, drop_rate)

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

    features = np.load('./X.npy')
    labels = np.load('./Y.npy')
    features = features.reshape([NUM_EXAMPLE, -1])
    labels = labels.reshape([NUM_EXAMPLE, -1])

    with tf.Session() as sess:
        tf.global_variables_initializer().run()

        # sub sample 80% training 20% test
        training_feature = []
        training_label = []
        test_feature = []
        test_label = []
        # subsample and padding
        for i in range(NUM_EXAMPLE):
            if i % 8 == 0 or i % 9 == 0:
                test_feature = np.append(test_feature, np.pad(features[i], (34, 35), 'constant'))
                test_label = np.append(test_label, labels[i])
            else:
                training_feature = np.append(training_feature, np.pad(features[i], (34, 35), 'constant'))
                training_label = np.append(training_label, labels[i])

        training_feature = np.reshape(training_feature, [-1, 1156])
        test_feature = np.reshape(test_feature, [-1, 1156])

        # training
        TRAINING_EXAMPLE = len(training_feature)
        for i in range(TRAINING_STEPS):
            xs = training_feature[i % TRAINING_EXAMPLE]
            ys = training_label[i % TRAINING_EXAMPLE]
            # Batch
            for j in range(BATCH_SIZE - 1):
                xs = np.append(xs, training_feature[(i + j) % TRAINING_EXAMPLE])
                ys = np.append(ys, training_label[(i + j) % TRAINING_EXAMPLE])
            xs = np.reshape(xs, [-1, 1156])
            ys = np.reshape(ys, [-1, 1])
            _, y_pred, y_true, loss_value = sess.run([train_op, y, y_, mse_mean],
                                                     feed_dict={x: xs, y_: ys, drop_rate: 0.5})
            acc = r2_score(y_true, y_pred)
            # r2_score for training
            if i % 100 == 0:
                print(
                    "After %d training step(s), mse loss mean on training batch is %g. R2 is %g" % (i, loss_value, acc))
            # testing
            if i % 1000 == 0 and i > 1:
                pred_list = []
                true_list = []
                TEST_EXAMPLE = len(test_feature)
                for i in range(TEST_EXAMPLE):
                    xs = test_feature[i]
                    ys = test_label[i]
                    xs = np.reshape(xs, [-1, 1156])
                    ys = np.reshape(ys, [-1, 1])
                    y_pred, y_true = sess.run([y, y_],
                                              feed_dict={x: xs, y_: ys, drop_rate: 1})
                    # print("Test y1 is:", y_true)
                    # print("Pred y2 is:", y_pred)
                    y_pred = y_pred[0]
                    y_true = y_true[0]
                    pred_list.append(y_pred)
                    true_list.append(y_true)
                r2 = r2_score(true_list, pred_list)
                print("After test, R2 is %g" % (r2))
        # Validation
        pred_list = []
        true_list = []
        TEST_EXAMPLE = len(test_feature)
        for i in range(TEST_EXAMPLE):
            xs = test_feature[i]
            ys = test_label[i]
            xs = np.reshape(xs, [-1, 1156])
            ys = np.reshape(ys, [-1, 1])
            _, y_pred, y_true, loss_value = sess.run([train_op, y, y_, mse_mean],
                                                     feed_dict={x: xs, y_: ys,drop_rate: 1})
            print("Test y1 is:", y_true)
            print("Pred y2 is:", y_pred)
            y_pred = y_pred[0]
            y_true = y_true[0]
            pred_list.append(y_pred)
            true_list.append(y_true)
        r2 = r2_score(true_list, pred_list)
        print("After test, R2 is", r2)


def main(argv=None):
    train()


if __name__ == '__main__':
    main()
