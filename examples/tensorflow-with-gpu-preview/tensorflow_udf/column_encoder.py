import os
from typing import Dict, Tuple, List

import numpy as np
import tensorflow as tf
from tensorflow.python.keras import metrics
from tensorflow.python.keras import Input
from tensorflow.python.keras.layers import Dense

from identity_feature_column import identity_column
from keras_layer import TFHubTextLayer


class ColumnEncoder:

    def create_categorical_column_with_hash_bucket(self, column, column_config):
        hash_bucket_size = column_config["hash_bucket_size"]
        embedding_dimensions = column_config["embedding_dimensions"]
        feature_column = tf.feature_column.categorical_column_with_hash_bucket(
            key=column.name, hash_bucket_size=hash_bucket_size,
            dtype=tf.dtypes.as_dtype(np.dtype(column.type))
        )
        return hash_bucket_size, embedding_dimensions, feature_column

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
        keras_input = Input(name=column.name, shape=[1], dtype=tf.string)
        hub_layer = TFHubTextLayer("default", column_config["module_url"], trainable=True)(keras_input)
        feature_column = identity_column(column.name)
        return feature_column, keras_input, hub_layer

    def generate_categorical_input(self, column, column_config: Dict):
        hash_bucket_size, embedding_dimensions, feature_column = \
            self.create_categorical_column_with_hash_bucket(column, column_config)
        embedding_feature_column = \
            tf.feature_column.embedding_column(
                feature_column, dimension=embedding_dimensions)
        keras_input = Input(name=column.name, shape=[embedding_dimensions])
        return embedding_feature_column, keras_input, keras_input

    def generate_numeric_input(self, column, column_config: Dict):
        feature_column = self.get_numeric_column(column, column_config)
        keras_input = Input(name=column.name, shape=[1])
        return feature_column, keras_input, keras_input

    def generate_categorical_output(self, column, net, column_config: Dict):
        hash_bucket_size, embedding_dimensions, feature_column = \
            self.create_categorical_column_with_hash_bucket(column, column_config)
        indicator_feature_column = tf.feature_column.indicator_column(feature_column)
        keras_output = Dense(hash_bucket_size, activation='relu', name="output_" + column.name)(net)
        loss = ("output_%s" % column.name, 'categorical_crossentropy', 1)
        output_metrics = ("output_%s" % column.name, [metrics.CategoricalAccuracy,
                                                      metrics.Precision, metrics.Recall])
        return indicator_feature_column, keras_output, loss, output_metrics

    def generate_numeric_output(self, column, net, column_config: Dict):
        feature_column = self.get_numeric_column(column, column_config)
        keras_output = Dense(1, name="output_" + column.name)(net)
        loss = ("output_%s" % column.name, 'mean_squared_error', 1)
        output_metrics = ("output_%s" % column.name, [metrics.mae])
        return feature_column, keras_output, loss, output_metrics

    def generate_input_feature_columns(self, input_columns, config: Dict):
        for column in input_columns:
            if column.name in config:
                column_config = config[column.name]
                if column_config["type"] == "categorical" and \
                        (column.type == int or column.type == str):
                    yield self.generate_categorical_input(column, column_config)
                elif column_config["type"] == "float" and column.type == float:
                    yield self.generate_numeric_input(column, column_config)
                elif column_config["type"] == "string" and column.type == str:
                    yield self.generate_string_inputs(column, column_config)
                else:
                    raise Exception(f"Unsupported Type for column {column.name}")

    def generate_output_feature_columns(self, output_columns, net: tf.keras.Model, config: Dict):
        for column in output_columns:
            if column.name in config:
                column_config = config[column.name]
                if column_config["type"] == "categorical" and \
                        (column.type == int or column.type == int):
                    yield self.generate_categorical_output(column, net, column_config)
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
        input_feature_columns = list(self.generate_input_feature_columns(input_columns, inputs))
        input_columns, keras_inputs, preprocessed_keras_inputs = zip(*input_feature_columns)
        return input_columns, keras_inputs, preprocessed_keras_inputs

    def generate_outputs(self, input_columns, net, config: Dict) -> \
            Tuple[List, List, Dict, Dict, Dict]:
        outputs = config["output"]
        output_columns = [column
                          for column in input_columns
                          if column.name in outputs]
        output_feature_columns = list(self.generate_output_feature_columns(output_columns, net, outputs))
        output_columns, keras_outputs, losses, output_metrics = zip(*output_feature_columns)
        loss_weights = {name: weight for name, loss, weight in losses}
        losses = {name: loss for name, loss, weight in losses}
        output_metrics = {name: metrics for name, metrics in output_metrics}
        return output_columns, keras_outputs, losses, loss_weights, output_metrics
