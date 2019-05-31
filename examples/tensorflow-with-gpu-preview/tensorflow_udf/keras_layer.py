import tensorflow
import tensorflow_hub as tfhub
from tensorflow.python.keras.engine import InputSpec
from tensorflow.python.layers.base import Layer


class TFHubTextLayer(Layer):
    """                                                                                                            
    Layer that encapsulates the following:                                                                         
    - Take full text level input                                                                                   
    - Return TFHub model's output according to provided input and output signature                                 

    # Input Shape                                                                                                  
        1D string tensor with shape `(batch_size)`                                                                 
    # Output Shape                                                                                                 
        Determined by the output_key                                                                               
    """

    def __init__(self, output_key, module_uri, max_strlen=10000, **kwargs):
        self._name = "TFHubTextLayer"
        super(TFHubTextLayer, self).__init__(**kwargs)
        self.input_spec = InputSpec(
            ndim=2, dtype=tensorflow.string)

        self.output_key = output_key
        # lol fucking tensorflow hub can't handle unicode URIs                                                     
        self.module_uri = str(module_uri)
        self.max_strlen = max_strlen

    def get_config(self):
        config = {
            'output_key': self.output_key,
            'module_uri': self.module_uri,
            'max_strlen': self.max_strlen,
        }
        base_config = super(TFHubTextLayer, self).get_config()
        config.update(base_config)
        return config

    def build(self, input_shape):
        self.embedder = tfhub.Module(self.module_uri, trainable=self.trainable)
        self.embedder_spec = tfhub.load_module_spec(self.module_uri)
        variables_ = [v for v in tensorflow.trainable_variables() if v in self.embedder.variables]
        self.trainable_weights.extend(variables_)
        self.weights.extend(variables_)
        self.trainable_variables.extend(variables_)
        super(TFHubTextLayer, self).build(input_shape)

    def call(self, str_inp):
        # we're basically always going to let TFHub modules do space                                               
        # tokenization for us                                                                                      

        # blech, it's not really possible to actually define a Keras input w/a shape of ndim 1
        str_inp_squeezed = tensorflow.squeeze(str_inp, axis=1)

        # let's apply the max strlen to prevent OOM hopefully                                                  
        str_inp_cutoff = tensorflow.strings.substr(str_inp_squeezed, 0, self.max_strlen)

        return self.embedder(str_inp_cutoff, as_dict=True)[self.output_key]

    def compute_output_shape(self, input_shape):
        output_shape_spec = map(int, self.embedder_spec.get_output_info_dict[self.output_key].get_shape()._dims)
        # change this to be whatever the batch size is                                                             
        output_shape_spec[0] = input_shape[0]
        return output_shape_spec   