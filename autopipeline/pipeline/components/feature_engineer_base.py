import numpy as np

from autopipeline.pipeline.components.base import AutoPLComponent
from autopipeline.pipeline.components.utils import stack_Xs
from autopipeline.pipeline.dataframe import GenericDataFrame
from autopipeline.utils.data import densify


class AutoPLFeatureEngineerAlgorithm(AutoPLComponent):
    need_y = False

    def fit_transform(self, X_train=None, y_train=None, X_valid=None, y_valid=None, X_test=None, y_test=None,
                      ):
        return self.fit(X_train, y_train, X_valid, y_valid, X_test, y_test).transform(X_train, X_valid, X_test, y_train)

    def transform(self, X_train=None, X_valid=None, X_test=None, y_train=None):
        return self.pred_or_trans(X_train, X_valid, X_test, y_train)

    def _transform_proc(self, X):
        if X is None:
            return None
        else:
            return self.estimator.transform(X)

    def _transform(self, X_: np.ndarray, X: GenericDataFrame):
        if X_ is None:
            return None
        X_ = self.before_trans_X(X_)
        X_ = self._transform_proc(X_)
        X_ = densify(X_)  # todo: 改为判断的形式？
        return X.replace_feat_grp(self.in_feat_grp, X_, self.out_feat_grp)

    def _pred_or_trans(self, X_train_, X_valid_=None, X_test_=None, X_train=None, X_valid=None, X_test=None,
                       y_train=None):
        X_train = self._transform(X_train_, X_train)
        X_valid = self._transform(X_valid_, X_valid)
        X_test = self._transform(X_test_, X_test)
        return {
            "X_train": X_train,
            "y_train": y_train,
            "X_valid": X_valid,
            "X_test": X_test,
        }

    def before_trans_X(self, X):
        return X

    def prepare_X_to_fit(self, X_train, X_valid=None, X_test=None):
        if not self.need_y:
            return stack_Xs(X_train, X_valid, X_test)
        else:
            return X_train
