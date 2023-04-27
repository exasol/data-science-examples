import os
import argparse

import numpy as np
import pandas as pd
import tensorflow as tf

from tensorflow.keras import layers


def main():
    """Main function of the script."""

    # input and output arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--train_data", type=str, help="path to input train data")
    parser.add_argument("--validation_data", type=str, help="path to input validation data")
    parser.add_argument("--test_data", type=str, help="path to input test data")
    parser.add_argument("--learning_rate", required=False, default=0.1, type=float)
    args = parser.parse_args()

    print(" ".join(f"{k}={v}" for k, v in vars(args).items()))

    train_df_no_scale = pd.read_csv(args.train_data,
                                    header=0)
    val_df_no_scale = pd.read_csv(args.validation_data, header=0)
    test_df_no_scale = pd.read_csv(args.test_data, header=0)

    train_df = (train_df_no_scale - train_df_no_scale.mean()) / train_df_no_scale.std()
    val_df = (val_df_no_scale - val_df_no_scale.mean()) / val_df_no_scale.std()
    test_df = (test_df_no_scale - test_df_no_scale.mean()) / test_df_no_scale.std()
    train_df['CLASS_POS'] = train_df_no_scale['CLASS_POS']
    val_df['CLASS_POS'] = val_df_no_scale['CLASS_POS']
    test_df['CLASS_POS'] = test_df_no_scale['CLASS_POS']

    train_df = remove_nans(train_df)
    val_df = remove_nans(val_df)

    train_df = oversample(train_df)
    val_df = oversample(val_df)

    initial_bias, class_weight = get_weight_bias(train_df)

    get_class_balance(val_df)
    get_class_balance(test_df)

    batch_size = 256
    train_ds = df_to_dataset(train_df, batch_size=batch_size)
    val_ds = df_to_dataset(val_df, shuffle=False, batch_size=batch_size)
    test_ds = df_to_dataset(test_df, shuffle=False, batch_size=batch_size)

    attribute_number = 42
    inputs = tf.keras.Input(shape=(attribute_number,))

    output_bias = tf.keras.initializers.Constant(initial_bias / 2)

    x = tf.keras.layers.Dense(40, activation="relu")(inputs)
    x = tf.keras.layers.Dense(50, activation="relu")(x)
    x = tf.keras.layers.Dense(20, activation="relu")(x)
    x = tf.keras.layers.Dropout(0.075)(x)
    output = tf.keras.layers.Dense(1, activation='sigmoid', bias_initializer=output_bias)(x)

    model = tf.keras.Model(inputs, output)

    optimizer_A = tf.keras.optimizers.Adam(learning_rate=args.learning_rate, name='Adam')

    model.compile(optimizer=optimizer_A,
                  loss=tf.keras.losses.BinaryCrossentropy(from_logits=False),
                  metrics=["accuracy",
                           tf.keras.metrics.FalsePositives(), tf.keras.metrics.TruePositives(),
                           tf.keras.metrics.TrueNegatives(), tf.keras.metrics.FalseNegatives()])

    model.fit(train_ds, epochs=20, validation_data=val_ds, class_weight=class_weight)
    loss, accuracy, fp, tp, tn, fn = model.evaluate(test_ds)
    print("Accuracy", accuracy)
    print(f"tp {tp}, fp {fp}, tn {tn}, fn {fn}")
    os.makedirs("./outputs/model", exist_ok=True)

    # files saved in the "./outputs" folder are automatically uploaded into run history
    # this is workaround for https://github.com/tensorflow/tensorflow/issues/33913 and will be fixed once we move to >tf2.1
    tf.saved_model.save(model, "./outputs/model/")


def oversample(df):
    cols = df.columns
    pos_features = df[df['CLASS_POS'] == 1]
    neg_features = df[df['CLASS_POS'] == 0]

    ids = np.arange(len(pos_features))
    choices = np.random.choice(ids, len(neg_features))

    res_pos_features = pos_features.iloc[choices]
    np_df = np.concatenate([res_pos_features, neg_features], axis=0)

    order = np.arange(len(np_df))
    np.random.shuffle(order)
    np_df_shuf = np_df[order]

    df = pd.DataFrame(np_df_shuf, columns=cols)
    return df


def remove_nans(dataframe):
    df = dataframe.copy()
    df = df.dropna(axis=0, thresh=35).reset_index(drop=True)
    df = df.fillna(method="ffill", axis=1, inplace=False, limit=None)
    return df


def get_class_balance(df):
    neg, pos = np.bincount(df['CLASS_POS'])
    total = neg + pos
    print('train:\n    Total: {}\n    Positive: {} ({:.2f}% of total)\n'.format(
        total, pos, 100 * pos / total))
    return neg, pos, total


def get_weight_bias(df):
    neg, pos, total = get_class_balance(df)

    initial_bias = np.log([pos / neg])

    weight_for_0 = (1 / neg) * (total / 2)
    weight_for_1 = (1 / pos) * (total / 2)

    class_weight = {0: weight_for_0, 1: weight_for_1}
    print(f"initial bias {initial_bias}")
    print('Weight for class 0: {:.2f}'.format(weight_for_0))
    print('Weight for class 1: {:.2f}'.format(weight_for_1))
    return initial_bias, class_weight


# Next, create a utility function that converts each training, validation, and test set DataFrame into a tf.data.Dataset, then shuffles and batches the data.
# todo batching by azml? or you would use the tf.data API
def df_to_dataset(dataframe, shuffle=True, batch_size=32):
    df = dataframe.copy()
    labels = df.pop('CLASS_POS')

    ds = tf.data.Dataset.from_tensor_slices((df, labels))
    if shuffle:
        ds = ds.shuffle(buffer_size=len(dataframe))
    ds = ds.batch(batch_size)
    ds = ds.prefetch(batch_size)
    return ds


if __name__ == "__main__":
    main()

