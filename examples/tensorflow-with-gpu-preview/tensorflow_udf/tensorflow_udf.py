import os
import subprocess
import urllib.parse

import requests
import tensorflow as tf
import yaml
from tensorflow.python.keras.engine.training import Model
from tensorflow.python.keras.layers import Dense, Concatenate

from column_encoder import ColumnEncoder
from dataset_utils import DatasetUtils
from utils import Utils


class TensorflowUDF():
    CONNECTION_NAME = "tensorflow_config"

    def create_table_network(self, preprocessed_keras_inputs):
        concat = Concatenate()(list(preprocessed_keras_inputs))
        net = Dense(100, activation='relu')(concat)
        net = Dense(100, activation='relu')(net)
        return net

    def read_config(self,exa):
        config_file_url = exa.get_connection(self.CONNECTION_NAME).address
        url_data = urllib.parse.urlparse(config_file_url)
        config_file = urllib.parse.unquote(url_data.path)
        with open(config_file) as file:
            config = yaml.load(file, yaml.Loader)
        with open(config_file) as file:
            print(file.read())
        return config

    def run(self, ctx, exa, train:bool):
        session_config = tf.ConfigProto(
            allow_soft_placement=True,
            log_device_placement=False)
        session = tf.Session(config=session_config)
        tf.keras.backend.set_session(session)

        config = self.read_config(exa)
        batch_size = config["batch_size"]
        epochs = config["epochs"]
        steps_per_epoch = ctx.size() // batch_size
        use_cache = config["use_cache"]
        load_path = None
        if "model_load_bucketfs_path" in config:
            load_path = config["model_load_bucketfs_path"]
        save_url = None
        if "model_save_bucketfs_url" in config:
            save_url = config["model_save_bucketfs_url"]
        save_path = config["model_temporary_save_path"]
        dataset = DatasetUtils().create_generator_dataset(
            ctx, epochs, batch_size, use_cache, exa.meta.input_columns)

        with tf.device(config["device"]):
            input_columns, keras_inputs, preprocessed_keras_inputs = \
                ColumnEncoder().generate_inputs(
                    exa.meta.input_columns, config["columns"])
            table_network = self.create_table_network(preprocessed_keras_inputs)
            output_columns, keras_outputs, losses, loss_weights, output_metrics = \
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

            saver = tf.train.Saver(max_to_keep=1,save_relative_paths=True)
            print("load_path",load_path,flush=True)
            if load_path is not None and load_path != "":
                initial_epoch = Utils().restore_model_and_get_inital_epoch(session, saver, load_path+"/checkpoints/tmp/save")
            else:
                initial_epoch = 0
            callbacks = Utils().create_callbacks(session, saver, save_path)

            model = Model(inputs=keras_inputs, outputs=keras_outputs)
            profile = config["profile"]
            profile_model_options = Utils().add_profiler(callbacks, profile, session, save_path)
            print(output_metrics, flush=True)
            model.compile(optimizer='rmsprop', loss=losses, loss_weights=loss_weights, metrics=output_metrics,
                          **profile_model_options)
            print(model.summary(),flush=True)

            if train:
                print("Starting training",flush=True)
                history = model.fit(dataset_iterator, steps_per_epoch=steps_per_epoch,
                                    epochs=initial_epoch + epochs, verbose=2, callbacks=callbacks,
                                    initial_epoch=initial_epoch )
                ctx.emit(str(history.history))
                print("save_url", save_url,flush=True)
                if save_url != "" and save_url is not None:
                    tarfile = f"/tmp/save"
                    os.makedirs(tarfile,exist_ok=True)
                    self.tar_save(save_path, tarfile)
                    self.upload_save(save_url, tarfile)

            else:
                print("Starting prediction",flush=True)
                for i in range(steps_per_epoch):
                    print(f"Predicting Batch {i}/steps_per_epoch",flush=True)
                    output = model.predict(dataset_iterator, steps=1)
                    ctx.emit(output)

    def upload_save(self, save_url, tarfile):
        print("Upload save", flush=True)
        with open(f"{tarfile}/metrics.tar", "rb") as f:
            requests.put(f"{save_url}/metrics.tar", data=f)
        with open(f"{tarfile}/checkpoints.tar", "rb") as f:
            requests.put(f"{save_url}/checkpoints.tar", data=f)

    def tar_save(self, save_path, tarfile):
        print("Tar save",flush=True)
        try:
            subprocess.check_output(f"tar -czf {tarfile}/metrics.tar {save_path}/metrics", shell=True)
            subprocess.check_output(f"tar -czf {tarfile}/checkpoints.tar {save_path}/checkpoints", shell=True)
        except subprocess.CalledProcessError as e:
            print(e)
            print(e.output, flush=True)
