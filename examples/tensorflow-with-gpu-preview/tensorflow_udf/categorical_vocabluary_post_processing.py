from tensorflow import layers
from keras import backend as K
import tensorflow as tf


# gets best category and probability from the output of a vocabulary layer

class Vocabluary_Postprocess(layers.Layer):
    def __init__(self, table, batchsize, column, **kwargs):
        super(Vocabluary_Postprocess, self).__init__(**kwargs)
        self.table = table
        self.batchsize = batchsize
        self.column = column

    def add_index(self, argmax):
        # adds indexing 0 .. batchsize to the result of argmax
        # the index is needed so gather_nd selects the right values
        indexes = tf.range(self.batchsize, dtype="int64")
        argmax_and_indexes = K.stack([indexes, argmax])
        argmax_with_indexes = K.transpose(argmax_and_indexes)
        return argmax_with_indexes

    def call(self, input):
        argmax = K.argmax(input)
        argmax_with_indexes = self.add_index(argmax)
        out_max_prob = tf.gather_nd(input, argmax_with_indexes, name="gather")

        max_category = self.table.lookup(argmax)
        if self.column.type == int:
            cast = tf.strings.to_number(max_category, out_type=tf.dtypes.int32)
            return cast, out_max_prob
        elif self.column.type == float:
            cast = tf.strings.to_number(max_category)
            return cast, out_max_prob
        else:
            return max_category, out_max_prob
