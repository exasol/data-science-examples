# SageMaker Extension Tutorial

## 1. Introduction
This tutorial walks you through the setup of the Exasol SageMaker-Extension 
project and presents an  use-case of how this extension can be used in Exasol.

The Exasol Sagemaker Extension enables you to develop an end-to-end machine 
learning project on data stored in Exasol using the AWS SageMaker Autopilot service.

The use-case handles a publicly available real-world dataset provided by a heavy 
truck manufacturer (see (Use Case)[#use-case]). With the 
provided extension, a machine learning model is developed which allows 
predicting  whether the truck failures are related to a particular component.

### 1.1 AWS Sagemaker Autopilot Service
AWS SageMaker is an AWS public cloud service in which users can build and deploy 
machine learning models. SageMaker provides a number of levels of abstraction to 
users while developing machine learning models. At one of the its highest level 
of abstraction, SageMaker enables users to use an Automated machine learning 
(AutoML) service, called Autopilot in AWS, that automatizes the process of 
applying machine learning  to real world problems.

Autopilot covers a  complete pipeline of developing an end-to end machine learning 
project, from raw data to a deployable model. It is able to automatically build, 
train and tune a number of machine learning models by inspecting your data set. 
In this way, the following tasks, which are repeatedly applied by ML-experts 
in machine learning projects, are automated:
- Pre-process and clean the data.
- Perform feature engineering and select the most appropriate ones
- Determine the most appropriate ML algorithm.
- Tune and optimize hyper-parameters of model.
- Post-process machine learning models.

The Exasol Sagemaker Extension takes these advantages of AWS Autopilot and enables 
users to easily create an effective and efficient machine learning models 
without expert knowledge.

### 1.2 Exasol SageMaker Extension

The Exasol Sagemaker Extension provides a Python library together with Exasol 
Scripts and UDFs that train Machine Learning Models on data stored in Exasol 
using AWS SageMaker Autopilot service.

The extension basically exports a given Exasol table into AWS S3, and then 
triggers Machine Learning training using the AWS Autopilot service with the 
specified parameters. In addition, the training status can be polled using 
the auxiliary scripts provided within the scope of the project. In order to 
perform prediction on a trained Autopilot model, one of the methods is to 
deploy the model to the real-time AWS endpoint. This extension provides Lua 
scripts for creating/deleting real-time endpoint and creates a model-specific 
UDF script for making real-time predictions.

![SME Overview](./images/sme_overview.png)

## 2. Setup the Extension

### 2.1 Installation

In order to use the Exasol SageMaker Extension, it is necessary to install the python package of the Extension 
, upload the given SageMaker-Extension Container into 
BucketFS and then activate the uploaded container in Exasol. These pre-packaged
releases are available in the [Releases](https://github.com/exasol/sagemaker-extension/releases) 
of the Github repository. 

Before starting the installation, let's define the variables required for the 
installation (Please note that you need to change variables below to use your 
own Exasol Database):
```buildoutcfg
DATABASE_HOST="127.0.0. 1"
DATABASE_PORT=9563
DATABASE_USER="sys"
DATABASE_PASSWORD="exasol"
BUCKETFS_PORT=6666
BUCKETFS_USER="w"
BUCKETFS_PASSWORD="write"
BUCKETFS_NAME="bfsdefault"
BUCKET_NAME="default"
PATH_IN_BUCKET="container"
CONTAINER_NAME="exasol_sagemaker_extension_container-release"
CONTAINER_FILE="exasol_sagemaker_extension_container-release.tar.gz"
```

- The sagemaker-extension python package ****provides a command line tool to 
deploy the Lua and UDF scripts to the database.**** It is installed as follows 
(Please check [the latest release](https://github.com/exasol/sagemaker-extension/releases/latest)):
    ```buildoutcfg
    pip install https://github.com/exasol/sagemaker-extension/releases/download/<version>/exasol_sagemaker_extension-<version>-py3-none-any.whl
    ```

- The required libraries and dependencies of the Exasol SageMaker Extension are 
distributed into Exasol by uploading the pre-built Exasol SageMaker-Extension Language 
Container to the BucketFS. You can upload it with any http(s) client that can send 
files via HTTP-Put requests. For more details please check 
[Access Files in BucketFS](https://docs.exasol.com/database_concepts/bucketfs/file_access.htm). 
The following example uploads the pre-built SageMaker-Extension Container to BucketFS with the curl command, a http(s) client:
    ```buildoutcfg
    curl -vX PUT -T \ 
        "<CONTAINER_FILE>" 
        "http://w:<BUCKETFS_WRITE_PASS>@$bucketfs_host:<BUCKETFS_PASS>/<BUCKETFS_NAME>/<PATH_IN_BUCKET><CONTAINER_FILE>"
    ```

- You need to activate the uploaded container  for your session or the whole system through 
adjusting parameter `SCRIPT_LANGUAGES`.  Please, keep in mind that 
the name of the language alias is assumed to be `PYTHON_SME` in the 
SageMaker-Extension. For more details, please check 
[Adding New Packages to Existing Script Languages](https://docs.exasol.com/database_concepts/udf_scripts/adding_new_packages_script_languages.htm).
The following example query activates the container session-wide:
    ```buildoutcfg
    ALTER SESSION SET SCRIPT_LANGUAGES=\
    'PYTHON_SME=localzmq+protobuf:///<BUCKETFS_NAME>/<BUCKET_NAME>/<PATH_IN_BUCKET><CONTAINER_NAME>/?\
            lang=python#buckets/<BUCKETFS_NAME>/<BUCKET_NAME>/<PATH_IN_BUCKET><CONTAINER_NAME>/\
            exaudf/exaudfclient_py3 PYTHON3=builtin_python3 PYTHON=builtin_python R=builtin_r JAVA=builtin_java'

    ```

### 2.2 Deployment

The installed SageMaker-extension python package provides a command line tool, enabling 
you to deploy all necessary Lua and UDF scripts into the specified 
`DATABASE_SCHEMA` of Exasol Database. The command line is run as follows: 

```buildoutcfg
python -m exasol_sagemaker_extension.deployment.deploy_cli \
    --host <DATABASE_HOST> \ 
    --port <DATABASE_PORT> \
    --user <DATABASE_USER> \
    --pass <DATABASE_PASSWORD> \
    --schema <DATABASE_SCHEMA>
```

After running this deployment command, you should be able to find the 
Lua and UDF scripts listed below in the specified schema:

- Lua Scripts:
  - _SME_TRAIN_WITH_SAGEMAKER_AUTOPILOT_
  - _SME_POLL_SAGEMAKER_AUTOPILOT_JOB_STATUS_
  - _SME_DEPLOY_SAGEMAKER_AUTOPILOT_ENDPOINT_
  - _SME_DELETE_SAGEMAKER_AUTOPILOT_ENDPOINT_
- UDF Scripts:
  - _SME_AUTOPILOT_TRAINING_UDF_
  - _SME_AUTOPILOT_JOB_STATUS_POLLING_UDF_
  - _SME_AUTOPILOT_ENDPOINT_DEPLOYMENT_UDF_
  - _SME_AUTOPILOT_ENDPOINT_DELETION_UDF_


### 2.3 Create Connection to AWS

The Exasol SageMaker Extension needs to connect to AWS SageMaker and your AWS S3 bucket. 
For that, it needs AWS credentials that has AWS Sagemaker Execution permissions. 
The required credentials are AWS Access Key (Please check how to 
[create an access key pair](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html#Using_CreateAccessKey)).


In order for the SageMaker-Extension to use the Access Key, you need to create 
an Exasol `CONNECTION` object which securely stores your keys. For more information, 
please check [Create Connection in Exasol](https://docs.exasol.com/sql/create_connection.htm?Highlight=connection):  


Before creating the connection object, let's define the variables for the AWS connection (Please note, that you need to use your own credentials for below variables.)
```buildoutcfg
AWS_BUCKET="ida_dataset_bucket"
AWS_REGION="eu-central-1"
AWS_KEY_ID="*****"
AWS_ACCESS_KEY="*****"
```

The Exasol `CONNECTION` object object is created as follows: 
  ```buildoutcfg
  CREATE OR REPLACE  CONNECTION <CONNECTION_NAME>
      TO 'https://<AWS_BUCKET>.s3.<AWS_REGION>.amazonaws.com/''
      USER '<AWS_KEY_ID>'
      IDENTIFIED BY '<AWS_ACCESS_KEY>'
  ```  



## 3. Use Case
The dataset, provided by Scania CV AB, consists of real data .
...


### 3.1 Train Model
### 3.2 Poll Training
### 3.3 Deploy Endpoint
### 3.4 Predict via Endpoint
### 3.5 Cleanup



