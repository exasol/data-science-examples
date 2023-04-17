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
    parser.add_argument("--n_estimators", required=False, default=100, type=int)
    parser.add_argument("--learning_rate", required=False, default=0.1, type=float)
    parser.add_argument("--registered_model_name", type=str, help="model name")
    args = parser.parse_args()

    ###################
    # <prepare the data>
    ###################
    print(" ".join(f"{k}={v}" for k, v in vars(args).items()))

    train_df = pd.read_csv(args.train_data,
                           header=0)  # todo change to not read whole csv at once?(datafactory oder FileDataset)
    val_df = pd.read_csv(args.validation_data, header=0)
    test_df = pd.read_csv(args.test_data, header=0)

    batch_size = 256
    train_ds = df_to_dataset(train_df, batch_size=batch_size)
    val_ds = df_to_dataset(val_df, shuffle=False, batch_size=batch_size)
    test_ds = df_to_dataset(test_df, shuffle=False, batch_size=batch_size)

    train_ds.element_spec
    attribute_number = 170
    inputs = tf.keras.Input(shape=(attribute_number,))

    x = tf.keras.layers.Dense(32, activation="relu")(inputs)
    x = tf.keras.layers.Dropout(0.5)(x)
    output = tf.keras.layers.Dense(1)(x)

    model = tf.keras.Model(inputs, output)

    model.compile(optimizer='adam',
                  loss=tf.keras.losses.BinaryCrossentropy(from_logits=True),
                  metrics=["accuracy"])
    model.fit(train_ds, epochs=10, validation_data=val_ds)
    loss, accuracy = model.evaluate(test_ds)
    print("Accuracy", accuracy)

    ##########################
    # <save and register model>
    ##########################



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
