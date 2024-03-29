## Python Tutorials
This section contains tutorials with the Python Programming Language. We are going to provide examples for different frameworks, tasks and use cases.

### AzureML:
[AzureML](https://azure.microsoft.com/de-de/products/machine-learning) is a Microsoft service for the Machine 
learning lifecycle in Azure.

This tutorial will show you:

* [A general introduction to the topic](AzureML/Introduction.ipynb), we recommend you start here
* [How to connect AzureML to Exasol](AzureML/ConnectAzureMLtoExasol.ipynb)
* [How to Train a model using data from Exasol](AzureML/TrainModelInAzureML.ipynb)
* [How to Invoke the trained model from an Exasol UDF](AzureML/InvokeModelFromExasolDBwithUDF.ipynb)


### Frameworks:

* [Scikit-learn](scikit-learn):

  [Scikit-learn](https://scikit-learn.org/stable/) is a free software machine learning library for the Python
  programming language. It features various classification, regression and clustering algorithms including support
  vector machines, random forests, gradient boosting, k-means and DBSCAN, and is designed to interoperate with the
  Python numerical and scientific libraries NumPy and SciPy. Its scalability of the training is typically limited.
  Out-of-core learning is not for all algorithms available, such that the usage of these algorithms is limited by the
  available main memory. Scikit-learn supports parallel execution through python multi-processing and linear algebra
  libraries. Distributed training and GPU acceleration is not out of the box available. You can find more details about
  scalability [here](https://scikit-learn.org/stable/modules/computing.html).

* [AWS Sagemaker](sagemaker)

  [AWS Sagemaker](https://aws.amazon.com/de/sagemaker/) is an AWS cloud service for machine learning. In contains
  hosted [Jupyter notebooks](https://jupyter.org/) but also
  a [SDK for machine learning](https://sagemaker.readthedocs.io/en/stable/).

  This tutorial will show you:

  * [How to connect from a SageMaker Notebook to Exasol](sagemaker/ConnectSagemakerToExasol.ipynb)
  * [How to load example dataset](sagemaker/LoadExampleDataIntoExasol.ipynb)
  * [How to train a Sagemaker model with data from Exasol](sagemaker/TrainSagemakerModelWithExasolData.ipynb)
  * [How to use a Sagemaker model from inside of Exasol](sagemaker/UseSagemakerModelFromExasol.ipynb)

### Prerequisites:

For general prerequisites, please refer to [Prerequisites](../README.md). However, these tutorials typically need a specific flavor of the [Script Language Container](https://github.com/exasol/script-languages) which has the required dependencies installed. For these purposes, we provide the python3-ds-* flavors which already contain the dependencies for the frameworks used in these tutorials. Prepackaged releases for this flavor can be found on the [release page](https://github.com/exasol/script-languages/releases).
