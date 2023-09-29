import os
import logging
import json
import numpy
import joblib
import mlflow


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
    method and return the result back.
    raw_data:   The json input received by the endpoint. needs to include a "data" field with a table that holds the 42
                features of each item to be classified
                these correspond to the following column names from the IDA tables:
                    ['AA_000', 'AG_005', 'AH_000', 'AL_000', 'AM_0', 'AN_000', 'AO_000', 'AP_000', 'AQ_000',
                    'AZ_004', 'BA_002', 'BB_000', 'BC_000', 'BD_000', 'BE_000',
                    'BF_000', 'BG_000', 'BH_000', 'BI_000', 'BJ_000', 'BS_000', 'BT_000', 'BU_000', 'BV_000',
                    'BX_000', 'BY_000', 'BZ_000', 'CA_000', 'CB_000', 'CC_000', 'CI_000', 'CN_004', 'CQ_000',
                    'CS_001', 'DD_000', 'DE_000', 'DN_000', 'DS_000', 'DU_000', 'DV_000', 'EB_000', 'EE_005']
    """
    logging.error(json.loads(raw_data))
    json_in = json.loads(raw_data)
    data = json_in["data"]

    data = numpy.array(data)
    response = model.predict(data)
    return {"result": str(response)}


