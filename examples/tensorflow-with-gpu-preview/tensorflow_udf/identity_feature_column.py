from tensorflow.python import tf_export, dtypes, collections, deprecation, math_ops, tensor_shape
from tensorflow.python.feature_column.feature_column_v2 import _check_shape, _check_default_value, \
    _assert_key_is_string, DenseColumn, _FEATURE_COLUMN_DEPRECATION_DATE, _FEATURE_COLUMN_DEPRECATION, \
    _check_config_keys
from tensorflow.python.keras import utils
from tensorflow.python.ops import parsing_ops
from tensorflow.python.framework import sparse_tensor as sparse_tensor_lib
from tensorflow.python.feature_column import feature_column as fc_old

@tf_export('feature_column.identity_column')
def identity_column(key,
                    shape=(1,),
                    dtype=dtypes.string, ):
    shape = _check_shape(shape, key)
    _assert_key_is_string(key)
    return IdentityColumn(
        key,
        shape=shape,
        dtype=dtype)


class IdentityColumn(
    DenseColumn,
    fc_old._DenseColumn,
    collections.namedtuple(
        'IdentityColumn',
        ('key', 'shape', 'dtype'))):
    """see `numeric_column`."""

    @property
    def _is_v2_column(self):
        return True

    @property
    def name(self):
        """See `FeatureColumn` base class."""
        return self.key

    @property
    @deprecation.deprecated(_FEATURE_COLUMN_DEPRECATION_DATE,
                            _FEATURE_COLUMN_DEPRECATION)
    def _parse_example_spec(self):
        return self.parse_example_spec

    @property
    def parse_example_spec(self):
        """See `FeatureColumn` base class."""
        return {
            self.key:
                parsing_ops.FixedLenFeature(self.shape, self.dtype,
                                            self.default_value)
        }

    def _transform_input_tensor(self, input_tensor):
        if isinstance(input_tensor, sparse_tensor_lib.SparseTensor):
            raise ValueError(
                'The corresponding Tensor of numerical column must be a Tensor. '
                'SparseTensor is not supported. key: {}'.format(self.key))
        return input_tensor

    @deprecation.deprecated(_FEATURE_COLUMN_DEPRECATION_DATE,
                            _FEATURE_COLUMN_DEPRECATION)
    def _transform_feature(self, inputs):
        input_tensor = inputs.get(self.key)
        return self._transform_input_tensor(input_tensor)

    def transform_feature(self, transformation_cache, state_manager):
        input_tensor = transformation_cache.get(self.key, state_manager)
        return self._transform_input_tensor(input_tensor)

    @property
    def variable_shape(self):
        """See `DenseColumn` base class."""
        return tensor_shape.TensorShape(self.shape)

    @property
    @deprecation.deprecated(_FEATURE_COLUMN_DEPRECATION_DATE,
                            _FEATURE_COLUMN_DEPRECATION)
    def _variable_shape(self):
        return self.variable_shape

    def get_dense_tensor(self, transformation_cache, state_manager):
        return transformation_cache.get(self, state_manager)

    @deprecation.deprecated(_FEATURE_COLUMN_DEPRECATION_DATE,
                            _FEATURE_COLUMN_DEPRECATION)
    def _get_dense_tensor(self, inputs, weight_collections=None, trainable=None):
        del weight_collections
        del trainable
        return inputs.get(self)

    @property
    def parents(self):
        """See 'FeatureColumn` base class."""
        return [self.key]

    def _get_config(self):
        """See 'FeatureColumn` base class."""
        config = dict(zip(self._fields, self))
        config['dtype'] = self.dtype.name
        return config

    @classmethod
    def _from_config(cls, config, custom_objects=None, columns_by_name=None):
        """See 'FeatureColumn` base class."""
        _check_config_keys(config, cls._fields)
        kwargs = config.copy()
        kwargs['dtype'] = dtypes.as_dtype(config['dtype'])
        return cls(**kwargs)
