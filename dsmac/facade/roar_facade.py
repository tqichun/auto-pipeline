import logging
import typing

import numpy as np

from dsmac.configspace import Configuration
from dsmac.epm.random_epm import RandomEPM
from dsmac.facade.smac_ac_facade import SMAC4AC
from dsmac.initial_design.initial_design import InitialDesign
from dsmac.intensification.intensification import Intensifier
from dsmac.optimizer.ei_optimization import RandomSearch
from dsmac.runhistory.runhistory import RunHistory
from dsmac.runhistory.runhistory2epm import RunHistory2EPM4Cost
from dsmac.stats.stats import Stats
from dsmac.scenario.scenario import Scenario
from dsmac.tae.execute_ta_run import ExecuteTARun

__author__ = "Marius Lindauer"
__copyright__ = "Copyright 2016, ML4AAD"
__license__ = "3-clause BSD"


class ROAR(SMAC4AC):
    """
    Facade to use ROAR mode

    Attributes
    ----------
    logger

    See Also
    --------
    :class:`~dsmac.facade.smac_facade.SMAC`

    """

    def __init__(self,
                 scenario: Scenario,
                 tae_runner: ExecuteTARun=None,
                 runhistory: RunHistory=None,
                 intensifier: Intensifier=None,
                 initial_design: InitialDesign=None,
                 initial_configurations: typing.List[Configuration]=None,
                 stats: Stats=None,
                 rng: np.random.RandomState=None,
                 run_id: int=1):
        """
        Constructor

        Parameters
        ----------
        scenario: smac.scenario.scenario.Scenario
            Scenario object
        tae_runner: smac.tae.execute_ta_run.ExecuteTARun or callable
            Callable or implementation of
            :class:`~dsmac.tae.execute_ta_run.ExecuteTARun`. In case a
            callable is passed it will be wrapped by
            :class:`~dsmac.tae.execute_func.ExecuteTAFuncDict`.
            If not set, it will be initialized with the
            :class:`~dsmac.tae.execute_ta_run_old.ExecuteTARunOld`.
        runhistory: RunHistory
            Runhistory to store all algorithm runs
        intensifier: Intensifier
            intensification object to issue a racing to decide the current incumbent
        initial_design: InitialDesign
            initial sampling design
        initial_configurations: typing.List[Configuration]
            list of initial configurations for initial design --
            cannot be used together with initial_design
        stats: Stats
            optional stats object
        rng: np.random.RandomState
            Random number generator
        run_id: int, (default: 1)
            Run ID will be used as subfolder for output_dir.

        """
        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

        scenario.acq_opt_challengers = 1

        # use SMAC facade
        super().__init__(
            scenario=scenario,
            tae_runner=tae_runner,
            runhistory=runhistory,
            intensifier=intensifier,
            runhistory2epm=RunHistory2EPM4Cost,
            initial_design=initial_design,
            initial_configurations=initial_configurations,
            run_id=run_id,
            acquisition_function_optimizer=RandomSearch,
            model=RandomEPM,
            rng=rng,
            stats=stats
        )
