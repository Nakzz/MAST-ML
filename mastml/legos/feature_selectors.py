"""
A collection of classes for selecting features
All classes here assume dataframe input and guarantee dataframe output.
(So no numpy arrays.)
"""
from sklearn.feature_selection import GenericUnivariateSelect, SelectPercentile, SelectKBest, SelectFpr, SelectFdr, SelectFwe, VarianceThreshold
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.decomposition import PCA
from . import util_legos, lego_utils
# list of sklearn feature selectors: http://scikit-learn.org/stable/modules/classes.html#module-sklearn.feature_selection
import pandas as pd


class PassThrough(BaseEstimator, TransformerMixin):
    " Keep specific features and pass them on to the other side "
    def __init__(self, features):
        if not isinstance(features, list):
            features = [features]
        self.features = features
    def fit(self, df, y=None):
        for feature in self.features:
            if feature not in df.columns:
                raise Exception(f"Specified feature '{feature}' to PassThrough not present in data file.")
    def transform(self, df):
        return df[self.features]

name_to_constructor = {
    'GenericUnivariateSelect': GenericUnivariateSelect,
    'SelectPercentile': SelectPercentile,
    'SelectKBest': SelectKBest,
    'SelectFpr': SelectFpr,
    'SelectFdr': SelectFdr,
    'SelectFwe': SelectFwe,
    'VarianceThreshold': VarianceThreshold,
}

# Modify all sklearn transform methods to return dataframes:
for constructor in name_to_constructor.values():
    constructor.old_transform = constructor.transform
    constructor.transform = lego_utils.dataframify_selector(constructor.transform)

# Mess with PCA stuff:
old_transform = PCA.transform
def new_transform(self, df):
    arr = old_transform(self, df)
    labels = ['pca_'+str(i) for i in range(arr.shape[1])]
    return pd.DataFrame(arr, columns=labels)
PCA.transform = new_transform

# Custom selectors don't need to be dataframified
name_to_constructor.update({
    'PassThrough': PassThrough,
    'DoNothing': util_legos.DoNothing,
    'PCA': PCA,
})
