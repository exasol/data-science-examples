# Data Science with Exasol
This repository contains a collection of examples and tutorials for Data Science and Machine Learning with Exasol. In those examples and tutorials you learn how to explore and prepare your data and build, train and deploy your model with and within Exasol.

**Currently, this repository is under development and we will add more and more examples and tutorials in the future.**

## What's inside:

* [Tutorials](tutorials): Tutorials show a complete workflow on a realistic use case and data. 
* [Examples](examples): Examples only show how to integrate a specific technology, but not a whole data science workflow with it.

## Prerequisites:

In general, you need:
  * Exasol, in particular with user-defined functions (UDFs). In most cases Version 6.0 and above with [Script Langauge Container](https://github.com/exasol/script-languages) support is required. We provide a [Community Edition](https://www.exasol.com/portal/display/DOC/EXASOL+Community+Edition+Quick+Start+Guide) or [Docker images](https://github.com/exasol/docker-db). 
  * Many examples or tutorials are provided as [Jupyter](https://jupyter.org/) Notebooks. We recommend to install a Jupyter server with access to the Database and the BucketFS (Documentation can be found in the [Exasol User Manual](https://www.exasol.com/portal/display/DOC/User+Manual+6.1.0) in Section 3.6.4). 
  * Furthermore, many examples heavily use [pyexasol](https://github.com/badoo/pyexasol) to communicate with the Database. We recommend to install it on your Jupyter server.

Specific prerequisites are stated in each tutorial.
