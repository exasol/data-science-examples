from stopwatch import Stopwatch
from udf.mock.udf_test_mock import *

import numpy as np
import pathlib
import yaml

from udf.tensorflow.tensorflow_udf import TensorflowUDF

def main():
    NUMBER_OF_FLOAT_COLUMNS = 1
    NUMBER_OF_STRING_COLUMNS = 2
    NUMBER_OF_INTEGER_COLUMNS = 2
    executor = TestExecutor()
    tensorflow_config_yaml = "tensorflow_config.yaml"
    meta = MockMetaData([Column("f_float_%s" % i, float, "DOUBLE") for i in range(NUMBER_OF_FLOAT_COLUMNS)] +
                        [Column("f_int_%s" % i, int, "INTEGER") for i in range(NUMBER_OF_INTEGER_COLUMNS)] +
                        [Column("f_text_%s" % i, str, "VARCHAR(10000)") for i in range(NUMBER_OF_STRING_COLUMNS)],
                        {TensorflowUDF.CONNECTION_NAME: Connection(
                            pathlib.Path(tensorflow_config_yaml).absolute().as_uri())})
    with open(tensorflow_config_yaml) as file:
        config = yaml.load(file, yaml.Loader)
    sw = Stopwatch()
    NUMBER_OF_VALUES = 10
    NUMBER_OF_BATCHES = 100
    strings = np.array(["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "zero"])
    outputs = executor.run([
        [np.sin((j + i) % NUMBER_OF_VALUES) for i in range(NUMBER_OF_FLOAT_COLUMNS)] +
        [(j + i) % NUMBER_OF_VALUES for i in range(NUMBER_OF_INTEGER_COLUMNS)] +
        [" ".join(strings[(np.arange(100) + j + i) % len(strings)].tolist())
         for i in range(NUMBER_OF_STRING_COLUMNS)]
        for j in range(NUMBER_OF_BATCHES * config["batch_size"])],
        meta, TensorflowUDF().run)
    sw.stop()
    print(sw)
    for i in outputs:
        print(i)


if __name__ == '__main__':
    main()
