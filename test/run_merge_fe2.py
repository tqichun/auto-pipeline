import pandas as pd
from sklearn.model_selection import ShuffleSplit

from autopipeline.estimator.base import AutoPipelineEstimator
from autopipeline.hdl.hdl_constructor import HDL_Constructor
from autopipeline.tuner.smac_tuner import SmacPipelineTuner

df = pd.read_csv("../examples/classification/train_classification.csv")
ss = ShuffleSplit(n_splits=1, random_state=0, test_size=0.25)
train_ix, test_ix = next(ss.split(df))
df_train = df.iloc[train_ix, :]
df_test = df.iloc[test_ix, :]

tuner = SmacPipelineTuner(
    random_state=42,
    initial_runs=5,
    runcount_limit=12,
)
hdl_constructor=HDL_Constructor(
    DAG_descriptions={
                "nan->imp": "impute.fill_abnormal",
                "imp->{cat_name=cat,num_name=num}": "operate.split.cat_num",
                "cat->num":  "encode.cat_boost|scale.standardize",
                "num->target": "reduce.pca|lightgbm"
            }
)
auto_pipeline = AutoPipelineEstimator(tuner,hdl_constructor)
column_descriptions = {
    "id": "PassengerId",
    "target": "Survived",
    "ignore": "Name"
}

auto_pipeline.fit(
    X=df_train, X_test=df_test, column_descriptions=column_descriptions, n_jobs=1
)
