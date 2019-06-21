import pathlib

import tensorflow as tf
from tensorflow.python import keras
from tensorflow.python.profiler import option_builder
from tensorflow.python.profiler.model_analyzer import Profiler


class Utils:

    def save_graph(self, epoch, logs,
                   session: tf.Session,
                   saver: tf.train.Saver, checkpoint_path: str,
                   save_summary_writer: tf.summary.FileWriter):
        save_summary_writer.add_graph(session.graph)
        saver.save(session, save_path=f"{checkpoint_path}/{epoch}")

    def create_callbacks(self, session: tf.Session,
                         saver: tf.train.Saver,
                         save_path: str):
        checkpoint_path = self.get_checkpoint_path(save_path)
        save_summary_writer = tf.summary.FileWriter(checkpoint_path)
        save_callback = keras.callbacks.LambdaCallback(
            on_epoch_end=lambda epoch, logs: self.save_graph(epoch, logs, session, saver, checkpoint_path,
                                                             save_summary_writer))
        log_callback = \
            keras.callbacks.TensorBoard(
                log_dir=f'{save_path}/metrics', histogram_freq=0, batch_size=32,
                write_graph=True,
                write_grads=False,
                write_images=False, embeddings_freq=0,
                embeddings_layer_names=None,
                embeddings_metadata=None, embeddings_data=None,
                update_freq='epoch')
        callbacks = [log_callback, save_callback]
        return callbacks

    def get_checkpoint_path(self, save_path):
        checkpoint_path = f"{save_path}/checkpoints"
        return checkpoint_path

    def restore_model_and_get_inital_epoch(
            self, session: tf.Session,
            saver: tf.train.Saver,
            load_path: str):
        print("load_path", load_path, flush=True)
        checkpoint_path = self.get_checkpoint_path(load_path)
        print("checkpoint_path",checkpoint_path, flush=True)
        latest_checkpoint = tf.train.latest_checkpoint(checkpoint_path)
        print("latest_checkpoint", latest_checkpoint, flush=True)
        if latest_checkpoint is not None:
            saver.restore(session, latest_checkpoint)
            return int(pathlib.Path(latest_checkpoint).name)
        else:
            return 0

    def add_profile(self, epoch, logs,
                    run_metadata: tf.RunMetadata,
                    profiler: tf.profiler.Profiler,
                    profile_writer: tf.summary.FileWriter,
                    save_path: str):
        timeline_path = f"{save_path}/timeline"
        pathlib.Path(timeline_path).mkdir(exist_ok=True, parents=True)
        profiler.add_step(epoch, run_meta=run_metadata)
        opts = (option_builder.ProfileOptionBuilder(
            option_builder.ProfileOptionBuilder.time_and_memory())
                .with_step(epoch)
                .with_timeline_output(f"{timeline_path}/step").build())
        profiler.profile_graph(options=opts)
        profile_writer.add_run_metadata(run_metadata, f"step{epoch}")

    def add_profiler(self, callbacks, profile: bool, session: tf.Session, save_path: str):
        if profile:
            profiler = Profiler(session.graph)
            options = tf.RunOptions(trace_level=tf.RunOptions.FULL_TRACE)
            run_metadata = tf.RunMetadata()
            profile_writer = tf.summary.FileWriter(f"{save_path}/profile")
            profile_writer.add_graph(session.graph)
            profiler_callback = keras.callbacks.LambdaCallback(
                on_epoch_end=lambda batch, logs: self.add_profile(batch, logs, run_metadata,
                                                                  profiler, profile_writer, save_path))
            callbacks.append(profiler_callback)
            additional_options = dict(options=options, run_metadata=run_metadata)
        else:
            additional_options = dict()
        return additional_options
