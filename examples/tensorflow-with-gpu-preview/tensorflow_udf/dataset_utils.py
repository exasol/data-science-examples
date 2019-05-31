import numpy as np
import tensorflow as tf
from tensorflow.python.feature_column.feature_column import input_layer

from udf.mock.udf_test_mock import exa


class DatasetUtils:

    def generator(self, ctx, epochs: int, batch_size: int, use_cache: bool):
        steps_per_epoch = ctx.size() // batch_size
        for epoch in range(epochs):
            for batch in range(steps_per_epoch):
                df = ctx.get_dataframe(num_rows=batch_size)
                if df is not None:
                    to_dict = df.to_dict(orient="series")
                    yield to_dict
                else:
                    break
            if not use_cache:
                ctx.reset()

    def create_generator_dataset(self, ctx, epochs: int, batch_size: int, use_cache: bool):
        ds = tf.data.Dataset.from_generator(
            lambda: self.generator(ctx, epochs, batch_size, use_cache),
            {column.name: np.dtype(column.type) for column in exa.meta.input_columns},
            {column.name: tf.TensorShape([None]) for column in exa.meta.input_columns}
        )
        return ds

    def add_feature_columns_to_dataset(
            self, dataset: tf.data.Dataset, input_columns, output_columns):
        dataset = dataset.map(
            lambda x: (
                tuple(input_layer(x, column) for column in input_columns),
                tuple(input_layer(x, column) for column in output_columns)
            ), num_parallel_calls=4
        ).apply(tf.data.experimental.unbatch())
        return dataset

    def create_dataset(self, dataset: tf.data.Dataset,
                       input_columns, output_columns,
                       batch_size: int, use_cache: bool):
        dataset = self.add_feature_columns_to_dataset(dataset, input_columns, output_columns)
        if use_cache:
            dataset = dataset.cache("cache").repeat()
        dataset = dataset.shuffle(1000, reshuffle_each_iteration=True)
        dataset = dataset.batch(batch_size, drop_remainder=True)
        return dataset
