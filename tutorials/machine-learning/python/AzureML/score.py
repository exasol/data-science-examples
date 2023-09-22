import os
import logging
import json
import numpy
import joblib
import mlflow
import pandas as pd


def init():
    """
    This function is called when the container is initialized/started, typically after create/update of the deployment.
    You can write the logic here to perform init operations like caching the model in memory
    """
    global model
    # AZUREML_MODEL_DIR is an environment variable created during deployment.
    # It is the path to the model folder (./azureml-models/$MODEL_NAME/$VERSION)
    model_path = os.path.join(
        os.getenv("AZUREML_MODEL_DIR"), "sklearn_model_sklearn_save/"
    )
    # deserialize the model file back into a sklearn model
    model = mlflow.sklearn.load_model(model_path)
    logging.info("Init complete")


def run(raw_data):
    """
    This function is called for every invocation of the endpoint to perform the actual scoring/prediction.
    In the example we extract the data from the json input and call the scikit-learn model's predict()
    method and return the result back
    """
    logging.error(json.loads(raw_data))
    json_in = json.loads(raw_data)
    logging.error(type(json_in))
    data = json_in["data"]

    data = numpy.array(data)
    data = data.reshape(1, -1)
    response = model.predict(data)
    return {"result": str(response[0])}
