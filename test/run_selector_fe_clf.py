import numpy as np
import pandas as pd
from sklearn.datasets import load_digits
from sklearn.model_selection import ShuffleSplit

from autopipeline.estimator.base import AutoPipelineEstimator
from autopipeline.hdl.hdl_constructor import HDL_Constructor
from autopipeline.tuner.smac_tuner import SmacPipelineTuner

digits = load_digits()
data = digits.data
target = digits.target
columns = [str(i) for i in range(data.shape[1])] + ["target"]
df = pd.DataFrame(np.hstack([data,target[:,None]]), columns=columns)
df["target"]=df["target"].astype("int")
ss = ShuffleSplit(n_splits=1, random_state=0, test_size=0.25)
train_ix, test_ix = next(ss.split(df))
df_train = df.iloc[train_ix, :]
df_test = df.iloc[test_ix, :]

tuner = SmacPipelineTuner(
    random_state=42,
    initial_runs=5,
    runcount_limit=12,
)
auto_pipeline = AutoPipelineEstimator(tuner,HDL_Constructor(
    DAG_descriptions={
        "num->num": [
            "select.from_model_clf"
        ],
        "num->target": [
            "lightgbm"
        ]
    }
))
column_descriptions = {
    "target": "target"
}
auto_pipeline.fit(
    X=df_train, X_test=df_test, column_descriptions=column_descriptions, n_jobs=1
)
