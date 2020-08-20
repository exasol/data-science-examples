import os
from typing import Dict, Tuple, List

import numpy as np
import tensorflow as tf
import requests
from tensorflow.python.keras import metrics
from tensorflow.python.keras import Input
from tensorflow.python.keras.layers import Dense
from keras import backend as K

from identity_feature_column import identity_column
from keras_layer import TFHubTextLayer

from categorical_vocabluary_post_processing import Vocabluary_Postprocess

# currently if you change the output of a feature column or add a feature column type, you have to change the
# OutputPostprocessor as well to get the desired result

class ColumnEncoder:

    def create_categorical_column_with_hash_bucket(self, column, column_config):
        print(column)
        hash_bucket_size = column_config["hash_bucket_size"]
        embedding_dimensions = column_config["embedding_dimensions"]
        feature_column = tf.feature_column.categorical_column_with_hash_bucket(             # output_id = Hash(input_feature_string) % bucket_size
            key=column.name, hash_bucket_size=hash_bucket_size,
            dtype=tf.dtypes.as_dtype(np.dtype(column.type))
        )
        return hash_bucket_size, embedding_dimensions, feature_column

    def create_categorical_column_with_vocabulary_file(self, column, column_config):
        print("vocab column", column)
        vocab_file_path = column_config["vocab_path"]
        local_vocab_file = vocab_file_path
        if vocab_file_path.startswith("http"):
            local_vocab_file = "save/" + column.name
            res = requests.get(f"{vocab_file_path}")
            with open(local_vocab_file, 'w+') as file:
                file.write(res.text)

        embedding_dimensions = column_config["embedding_dimensions"]
        feature_column = tf.feature_column.categorical_column_with_vocabulary_file(             # do we even have "out of vocab" values? should not, cause we generate the vocab?
            key=column.name, vocabulary_file=local_vocab_file, vocabulary_size=None,            # what if the vocab is static and we get new data?
            num_oov_buckets=0, default_value=None,                                              # if vocab size needed, probably best if returned by udf o.Ä
            dtype=tf.dtypes.as_dtype(np.dtype(column.type))
        )
        num_vocab_buckets = feature_column.num_buckets
        return num_vocab_buckets, embedding_dimensions, feature_column

    def min_max_scaling(self, x, min_value, max_value):
        return (x - min_value) / (max_value - min_value)

    def get_numeric_column(self, column, column_config: Dict):
        min_value = column_config["min_value"]
        max_value = column_config["max_value"]
        feature_column = tf.feature_column.numeric_column(
            key=column.name,
            normalizer_fn=lambda x:
            self.min_max_scaling(x, min_value, max_value))
        return feature_column

    def generate_string_inputs(self, column, column_config: Dict):
        os.environ["TFHUB_DOWNLOAD_PROGRESS"] = "1"
        keras_input = Input(name=column.name, shape=[1], dtype=tf.string)           # is used to instantiate a Keras tensor.
        hub_layer = TFHubTextLayer("default", column_config["module_url"], trainable=True)(keras_input)
        feature_column = identity_column(column.name)
        return feature_column, keras_input, hub_layer

    def generate_categorical_input(self, column, column_config: Dict):
        if column_config["method"] == "hash":
            bucket_size, embedding_dimensions, feature_column = \
                self.create_categorical_column_with_hash_bucket(column, column_config["parameters"])
        elif column_config["method"] == "vocabulary":
            bucket_size, embedding_dimensions, feature_column = \
                self.create_categorical_column_with_vocabulary_file(column, column_config["parameters"])
        else:
            raise Exception(f"Unsupported method for column {column.name}")
        embedding_feature_column = \
            tf.feature_column.embedding_column(
                feature_column, dimension=embedding_dimensions)
        keras_input = Input(name=column.name, shape=[embedding_dimensions])
        return embedding_feature_column, keras_input, keras_input

    def generate_numeric_input(self, column, column_config: Dict):
        feature_column = self.get_numeric_column(column, column_config)
        keras_input = Input(name=column.name, shape=[1])
        return feature_column, keras_input, keras_input

    def categorical_output_post_processing(self, column, keras_output, batchsize):
        table = tf.contrib.lookup.index_to_string_table_from_file(
            vocabulary_file="save/" + column.name)
        layer = Vocabluary_Postprocess(table, batchsize, column, name="Vocabluary_Postprocess_" + column.name)
        keras_max_category, keras_max_prob = layer(keras_output)
        return keras_max_category, keras_max_prob

    def generate_categorical_output_vocab(self, column, net, column_config: Dict, batchsize):
        vocab_size, embedding_dimensions, feature_column = \
            self.create_categorical_column_with_vocabulary_file(column, column_config["parameters"])
        indicator_feature_column = tf.feature_column.indicator_column(feature_column)
        keras_output = Dense(vocab_size, activation='relu', name="output_" + column.name)(net)

        keras_max_category, keras_max_prob = self.categorical_output_post_processing(column, keras_output, batchsize)
        loss = ("output_%s" % column.name, 'categorical_crossentropy', 1)
        output_metrics = ("output_%s" % column.name, "categorical_accuracy")
        return indicator_feature_column, (keras_output, keras_max_category, keras_max_prob), loss, output_metrics

    def generate_numeric_output(self, column, net, column_config: Dict):
        feature_column = self.get_numeric_column(column, column_config)
        keras_output = Dense(1, name="output_" + column.name)(net)
        loss = ("output_%s" % column.name, 'mean_squared_error', 1)
        output_metrics = ("output_%s" % column.name, 'mae')
        return feature_column, keras_output, loss, output_metrics

    def generate_input_feature_columns(self, input_columns, config: Dict):
        for column in input_columns:
            if column.name in config:
                column_config = config[column.name]
                if column_config["type"] == "categorical" and \
                        (column.type == int or column.type == str):                     # is this distinction still needed?
                    yield self.generate_categorical_input(column, column_config)
                elif column_config["type"] == "float" and column.type == float:
                    yield self.generate_numeric_input(column, column_config)
                elif column_config["type"] == "string" and column.type == str:
                    yield self.generate_string_inputs(column, column_config)
                else:
                    raise Exception(f"Unsupported Type for column {column.name}")

    def generate_output_feature_columns(self, output_columns, net: tf.keras.Model, config: Dict, batchsize):
        for column in output_columns:
            if column.name in config:
                column_config = config[column.name]
                if column_config["type"] == "categorical" and column_config["method"] == "vocabulary":
                    yield self.generate_categorical_output_vocab(column, net, column_config, batchsize)
                elif column_config["type"] == "float" and column.type == float:
                    yield self.generate_numeric_output(column, net, column_config)
                else:
                    raise Exception("Unsupported Type")

    def generate_inputs(self, input_columns, config: Dict):
        inputs = config["input"]
        input_columns = \
            [column
             for column in input_columns
             if column.name in inputs]
        inputs = config["input"]
        input_feature_columns = list(self.generate_input_feature_columns(input_columns, inputs))
        input_columns, keras_inputs, preprocessed_keras_inputs = zip(*input_feature_columns)
        [print(i) for i in input_columns]
        return input_columns, keras_inputs, preprocessed_keras_inputs

    def flatten(self, x):
        for i in x:
            if isinstance(i, Tuple):
                for j in i:
                    yield j
            else:
                yield i

    def generate_outputs(self, input_columns, net, config: Dict, batchsize) -> \
            Tuple[List, List, Dict, Dict, Dict]:
        outputs = config["output"]
        output_columns = [column
                          for column in input_columns
                          if column.name in outputs]
        output_feature_columns = list(self.generate_output_feature_columns(output_columns, net, outputs, batchsize))
        output_columns, keras_outputs, losses, output_metrics = zip(*output_feature_columns)
        keras_outputs = list(self.flatten(keras_outputs))
        loss_weights = {name: weight for name, loss, weight in losses}
        losses = {name: loss for name, loss, weight in losses}
        output_metrics = {name: metrics for name, metrics in output_metrics}
        return output_columns, keras_outputs, losses, loss_weights, output_metrics