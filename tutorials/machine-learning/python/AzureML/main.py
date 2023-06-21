import os
import argparse

import numpy as np
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import make_scorer
from sklearn.model_selection import ParameterGrid
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import confusion_matrix

import mlflow
import mlflow.sklearn


def main():
    """Main function of the script."""

    # input and output arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--train_data", type=str, help="path to input train data")
    parser.add_argument("--test_data", type=str, help="path to input test data")
    parser.add_argument("--learning_rate", required=False, default=0.1, type=float)
    args = parser.parse_args()
    print(" ".join(f"{k}={v}" for k, v in vars(args).items()))

    # read the data from the AzureML Blob Storage. This is a good way for the data used for this example,
    # but for your own data another approach might be better. Check here for more info:
    # https://learn.microsoft.com/en-us/azure/machine-learning/how-to-read-write-data-v2?view=azureml-api-2&tabs=cli
    train_df_no_scale = pd.read_csv(args.train_data, header=0)
    test_df_no_scale = pd.read_csv(args.test_data, header=0)

    train_data_and_labels = get_labels(train_df_no_scale, class_col_name='CLASS_POS')
    test_data_and_labels = get_labels(test_df_no_scale, class_col_name='CLASS_POS')

    # get transformer for data preparation:
    #   normalization, removing nans from dataset(important for back propagation),
    _, transformer = get_transformer(train_data_and_labels)

    # build classifier and find best training parameters
    clf, grid_search = build_et_classifier(train_data_and_labels, transformer)
    print(grid_search.best_params_['n_estimators'])
    print(grid_search.best_params_['max_depth'])
    print(str(grid_search.best_params_['class_weight']))

    # Train and evaluate the model.
    clf.fit(train_data_and_labels[1], train_data_and_labels[0].ravel())

    # Evaluate the trained classifier using test data. Output can be found in the logs of the AzureML job run.
    y_pred = test_eval(test_data_and_labels, clf)

    # Save the trained model and register it with AzureML Workspace
    mlflow.sklearn.log_model(
        sk_model=clf,
        registered_model_name="registered_model_name_sklearn",
        artifact_path="./outputs/model/sklearn_model_sklearn_save"
    )

# get class labels from dataset
def get_labels(df, class_col_name):
    y = df.loc[:, class_col_name]
    X_data = df.loc[:, df.columns != class_col_name]
    return [y, X_data]

# get transformer and train for data preprocessing
def get_transformer(data_and_labels):
    transformer = Pipeline([
        ('imputer', SimpleImputer(strategy="median")),
        ('scaler', StandardScaler())
    ])
    train_df_transformed = transformer.fit_transform(data_and_labels[1])
    return train_df_transformed, transformer


def build_et_classifier(data_and_labels, transformer):
    y = data_and_labels[0]
    X_data = data_and_labels[1]
    X_data = transformer.transform(X_data)

    # Create classifier
    clf = ExtraTreesClassifier(n_jobs=-1)

    # Specify parameter search grid
    # The grid size is kept small to reduce the computation time
    # Good values (known from offline grid search) are:
    # 'n_estimators': 61
    # 'max_depth': 10
    # 'class_weight': {{0: 1, 1: 89}}
    param_grid = [
        {'n_estimators': [30, 61],
         'max_depth': [5, 10],
         'class_weight': [{0: 1, 1: 30}, {0: 1, 1: 50}, {0: 1, 1: 89}]}
    ]

    ida_scorer = make_scorer(ida_score)

    # Search for optimal values in grid using 5-fold cross validation
    grid_search = GridSearchCV(clf, param_grid, cv=5, scoring=ida_scorer, n_jobs=-1)
    grid_search.fit(X_data, y.values.ravel())

    # Create new model with optimal parameter values
    clf = ExtraTreesClassifier(n_jobs=-1,
                               n_estimators=grid_search.best_params_['n_estimators'],
                               max_depth=grid_search.best_params_['max_depth'],
                               class_weight=grid_search.best_params_['class_weight'])

    # fuse the classifier and the transformer into one pipeline.
    # This guarantees the preprocessing stays the same for each use of the model.
    model = Pipeline([
        ('transform', transformer),
        ('clf', clf)
    ])

    return model, grid_search

# Evaluate the trained model
def test_eval(data_and_labels, clf):
    y = data_and_labels[0]
    X_data = data_and_labels[1]

    # Predict classes of test data
    y_pred = clf.predict(X_data)

    # Examine the results
    confusion_mat = confusion_matrix(y, y_pred)
    confusion_matrix_df = pd.DataFrame(confusion_mat,
                                       index=['actual neg', 'actual pos'],
                                       columns=['predicted neg', 'predicted pos'])

    print("Total Cost:", - ida_score(y, y_pred), "\n")
    print("Confusion Matrix:\n", confusion_matrix_df)


# Define scoring metric for grid search from problem description of the Scania Trucks dataset
def ida_score(y, y_pred):
    false_preds = y - y_pred
    num_false_pos = (false_preds < 0).sum()
    num_false_neg = (false_preds > 0).sum()
    return -(num_false_pos * 10 + num_false_neg * 500)


if __name__ == "__main__":
    main()
