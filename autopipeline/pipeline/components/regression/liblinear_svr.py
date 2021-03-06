from autopipeline.pipeline.components.regression_base import AutoPLRegressionAlgorithm
from sklearn.preprocessing import StandardScaler

class LibLinear_SVR(AutoPLRegressionAlgorithm):
    class__ = "LinearSVR"
    module__ = "sklearn.svm"

    def before_fit_y(self, y):
        if y is None:
            return None
        self.scaler=StandardScaler(copy=True)
        return self.scaler.fit(y.reshape((-1,1))).ravel()

    def after_pred_y(self, y):
        return self.scaler.inverse_transform(y)
