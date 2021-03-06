from typing import Dict

import numpy as np

from autopipeline.evaluation.train_evaluator import TrainEvaluator
from autopipeline.hdl.smac import _encode
from autopipeline.hdl2phps.smac_hdl2phps import SmacHDL2PHPS
from autopipeline.manager.xy_data_manager import XYDataManager
from autopipeline.metrics import Scorer
from autopipeline.php2dhp.smac_php2dhp import SmacPHP2DHP
from autopipeline.tuner.base import PipelineTuner
from autopipeline.utils.pipeline import concat_pipeline
from dsmac.facade.smac_hpo_facade import SMAC4HPO
from dsmac.scenario.scenario import Scenario


class SmacPipelineTuner(PipelineTuner):
    def __init__(
            self,
            runcount_limit: int = 50,
            initial_runs: int = 20,
            random_state: int = 42,
            evaluator: TrainEvaluator = None,
    ):
        super(SmacPipelineTuner, self).__init__(
            runcount_limit,
            initial_runs,
            random_state,
            evaluator,
        )

        self.evaluator.set_php2model(self.php2model)


    def run(
            self,
            datamanager: XYDataManager,
            metric: Scorer,
            all_scoring_functions: bool,
            splitter,
            initial_configs
    ):
        if hasattr(splitter, "random_state"):
            setattr(splitter, "random_state", self.random_state)
        self.set_task(datamanager.task)
        self.evaluator.init_data(
            datamanager,
            metric,
            all_scoring_functions,
            splitter,
        )
        # todo: metalearn

        self.scenario = Scenario(
            {
                "run_obj": "quality",
                "runcount-limit": self.runcount_limit,
                "cs": self.phps,  # configuration space
                "deterministic": "true",
                "output_dir": self.resource_manager.smac_output_dir,
            },
            initial_runs=self.initial_runs,
            db_type=self.resource_manager.db_type,
            db_args=self.resource_manager.rh_db_args,
            db_kwargs=self.resource_manager.rh_db_kwargs,
        )
        # todo 将 file_system 传入，或者给file_system添加 runtime 参数
        smac = SMAC4HPO(
            scenario=self.scenario,
            rng=np.random.RandomState(self.random_state),
            tae_runner=self.evaluator,
            initial_configurations=initial_configs
        )
        smac.solver.start_()
        for i in range(self.runcount_limit):
            smac.solver.run_()
            should_continue = self.evaluator.resource_manager.delete_models()
            if not should_continue:
                print("info:exit")
                break

    def php2model(self, php):
        php2dhp = SmacPHP2DHP()
        dhp = php2dhp(php)
        preprocessor = self.create_preprocessor(dhp)
        estimator = self.create_estimator(dhp)
        pipeline = concat_pipeline(preprocessor, estimator)
        print(pipeline, pipeline[-1].hyperparams)
        return dhp, pipeline

    def hdl2phps(self, hdl: Dict):
        hdl2phps = SmacHDL2PHPS()
        hdl2phps.set_task(self.task)
        return hdl2phps(hdl)
