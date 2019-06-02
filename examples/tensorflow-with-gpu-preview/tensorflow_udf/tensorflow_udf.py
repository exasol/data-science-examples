import subprocess
import urllib.parse

import tensorflow as tf
import yaml
from tensorflow.python.keras.engine.training import Model
from tensorflow.python.keras.layers import Dense, Concatenate

from column_encoder import ColumnEncoder
from dataset_utils import DatasetUtils
from utils import Utils

import requests


class TensorflowUDF():
    CONNECTION_NAME = "tensorflow_config"

    def create_table_network(self, preprocessed_keras_inputs):
        concat = Concatenate()(list(preprocessed_keras_inputs))
        net = Dense(100, activation='relu')(concat)
        net = Dense(100, activation='relu')(net)
        return net

    def read_config(self):
        config_file_url = exa.meta.get_connection(self.CONNECTION_NAME).address
        url_data = urllib.parse.urlparse(config_file_url)
        config_file = urllib.parse.unquote(url_data.path)
        with open(config_file) as file:
            config = yaml.load(file, yaml.Loader)
        return config

    def run(self, ctx):
        session_config = tf.ConfigProto(
            allow_soft_placement=True,
            log_device_placement=False)
        session = tf.Session(config=session_config)
        tf.keras.backend.set_session(session)

        config = self.read_config()
        batch_size = config["batch_size"]
        epochs = config["epochs"]
        steps_per_epoch = ctx.size() // batch_size
        use_cache = config["use_cache"]
        train = config["train"]
        load_path = None
        if "model_bucketfs_load_path" in config:
            load_path = config["model_bucketfs_load_path"]
        save_url = config["model_save_bucketfs_url"]
        save_path = "save/save"
        dataset = DatasetUtils().create_generator_dataset(ctx, epochs, batch_size, use_cache)

        with tf.device(config["device"]):
            input_columns, keras_inputs, preprocessed_keras_inputs = \
                ColumnEncoder().generate_inputs(
                    exa.meta.input_columns, config["columns"])
            table_network = self.create_table_network(preprocessed_keras_inputs)
            output_columns, keras_outputs, losses, loss_weights = \
                ColumnEncoder().generate_outputs(
                    exa.meta.input_columns, table_network, config["columns"])
            session.run(tf.tables_initializer())

            dataset = DatasetUtils().create_dataset(dataset,
                                                    input_columns, output_columns,
                                                    batch_size, use_cache)

            session.run(tf.global_variables_initializer())
            session.run(tf.local_variables_initializer())

            dataset_iterator = dataset.make_initializable_iterator()
            session.run(dataset_iterator.initializer)

            saver = tf.train.Saver()
            if load_path is not None:
                initial_epoch = Utils().restore_model_and_get_inital_epoch(session, saver, load_path)
            else:
                initial_epoch = 0
            callbacks = Utils().create_callbacks(session, saver, save_path)

            model = Model(inputs=keras_inputs, outputs=keras_outputs)
            profile = config["profile"]
            profile_model_options = Utils().add_profiler(callbacks, profile, session)
            model.compile(optimizer='rmsprop', loss=losses, loss_weights=loss_weights,
                          **profile_model_options)
            print(model.summary())

            if train:
                history = model.fit(dataset_iterator, steps_per_epoch=steps_per_epoch,
                                    epochs=initial_epoch + epochs, verbose=2, callbacks=callbacks,
                                    initial_epoch=initial_epoch, )
                subprocess.check_output("tar -czf save.tar.gz save", shell=True)
                with open("save.tar.gz", "rb") as f:
                    requests.put(save_url, data=f)
                ctx.emit(str(history.history))
            else:
                for i in range(steps_per_epoch):
                    output = model.predict(dataset_iterator, steps=1)
                    ctx.emit(output)
