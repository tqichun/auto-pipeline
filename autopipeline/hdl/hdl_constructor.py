from copy import deepcopy
from typing import Union, Tuple, List

from autopipeline.constants import Task
from autopipeline.hdl.utils import get_hdl_db, get_default_hdl_db
from autopipeline.manager.xy_data_manager import XYDataManager
from autopipeline.utils.data import add_prefix_in_dict_keys


class HDL_Constructor():
    def __init__(
            self,
            hdl_db_path=None,
            DAG_descriptions=None
    ):
        if DAG_descriptions is None:
            DAG_descriptions = {
                "nan->{highR=highR_nan,lowR=lowR_nan}": "operate.split.nan",
                "highR_nan->lowR_nan": [
                    "operate.drop",
                    {"_name": "operate.merge", "__rely_model": "boost_model"}
                ],
                "lowR_nan->{cat_name=cat_nan,num_name=num_nan}": "operate.split.cat_num",
                "num_nan->num": [
                    "impute.fill_num",
                    {"_name": "impute.fill_abnormal", "__rely_model": "boost_model"}
                ],
                "cat_nan->cat": [
                    "impute.fill_cat",
                    {"_name": "impute.fill_abnormal", "__rely_model": "boost_model"}
                ],
                "cat->{highR=highR_cat,lowR=lowR_cat}": "operate.split.cat",
                "highR_cat->num": [
                    "operate.drop",
                    "encode.label"
                ],
                "lowR_cat->num": [
                    "encode.one_hot",
                    "encode.label"
                ],
                "num->target": [
                    # "decision_tree", "libsvm_svc",
                    "k_nearest_neighbors",
                    "catboost",
                    "lightgbm"
                ]
            }
        self.DAG_describe = DAG_descriptions
        if hdl_db_path:
            hdl_db = get_hdl_db(hdl_db_path)
        else:
            hdl_db = get_default_hdl_db()
        self.hdl_db = hdl_db
        self.params = {
            "hdl_db_path": hdl_db_path,
            "DAG_describe": DAG_descriptions,
        }

    def set_task(self, task: Task):
        self._task = task

    def set_random_state(self, random_state):
        self._random_state = random_state

    @property
    def random_state(self):
        if not hasattr(self, "_random_state"):
            return 10
        else:
            return self._random_state

    @property
    def task(self):
        if not hasattr(self, "_task"):
            raise NotImplementedError()
        return self._task

    def set_data_manager(self, data_manager: XYDataManager):
        self._data_manager = data_manager
        self._task = data_manager.task

    @property
    def data_manager(self):
        if not hasattr(self, "_data_manager"):
            raise NotImplementedError()
        return self._data_manager

    def parse_item(self, value: Union[dict, str]) -> Tuple[str, dict, bool]:
        if isinstance(value, dict):
            packages = value.pop("_name")
            if "_vanilla" in value:
                is_vanilla = value.pop("_vanilla")
            else:
                is_vanilla = False
            addition_dict = value
        elif isinstance(value, str):
            packages = value
            addition_dict = {}
            is_vanilla = False
        elif value is None:
            packages = "None"
            addition_dict = {}
            is_vanilla = False
        else:
            raise TypeError
        return packages, addition_dict, is_vanilla

    def purify_DAG_describe(self):
        DAG_describe = {}
        for k, v in self.DAG_describe.items():
            DAG_describe[k.replace(" ", "").replace("\n", "").replace("\t", "")] = v
        self.DAG_describe = DAG_describe

    def _get_params_in_dict(self, dict_: dict, package: str) -> dict:
        ans = deepcopy(dict_)
        for path in package.split("."):
            ans = ans.get(path, {})
        return ans

    def get_params_in_dict(self, hdl_db: dict, packages: str, phase: str, mainTask):
        assert phase in ("preprocessing", "estimator")
        packages: list = packages.split("|")
        params_list: List[dict] = [self._get_params_in_dict(hdl_db["preprocessing"], package) for package in
                                   packages[:-1]]
        last_phase_key = "preprocessing" if phase == "preprocessing" else mainTask
        params_list += [self._get_params_in_dict(hdl_db[last_phase_key], packages[-1])]
        if len(params_list) == 0:
            raise AttributeError
        elif len(params_list) == 1:
            return params_list[0]
        else:
            result = {}
            for params, package in zip(params_list, packages):
                result.update(add_prefix_in_dict_keys(params, package + "."))
            return result

    def run(self):
        # make sure:
        # set_task
        target_key = ""
        self.purify_DAG_describe()
        for key in self.DAG_describe.keys():
            if key.split("->")[-1] == "target":
                target_key = key
        estimator_values = self.DAG_describe.pop(target_key)
        if not isinstance(estimator_values, (list, tuple)):
            estimator_values = [estimator_values]
        preprocessing_dict = {}
        mainTask = self.task.mainTask
        preprocessing_package = "autopipeline.pipeline.components.preprocessing"
        hdl_db = get_default_hdl_db()
        # 遍历DAG_describe，构造preprocessing
        for i, (key, values) in enumerate(self.DAG_describe.items()):
            if not isinstance(values, (list, tuple)):
                values = [values]
            formed_key = f"{i}{key}(choice)"
            sub_dict = {}
            for value in values:
                packages, addition_dict, is_vanilla = self.parse_item(value)
                addition_dict.update({"random_state": self.random_state})  # fixme
                params = {} if is_vanilla else self.get_params_in_dict(hdl_db, packages, "preprocessing", mainTask)
                sub_dict[packages] = params
                sub_dict[packages].update(addition_dict)
            preprocessing_dict[formed_key] = sub_dict
        # 构造estimator
        estimator_dict = {}
        for estimator_value in estimator_values:
            packages, addition_dict, is_vanilla = self.parse_item(estimator_value)
            params = {} if is_vanilla else self.get_params_in_dict(hdl_db, packages, "estimator", mainTask)
            estimator_dict[packages] = params
            estimator_dict[packages].update(addition_dict)
        final_dict = {
            "preprocessing": preprocessing_dict,
            "estimator(choice)": estimator_dict
        }
        self.hdl = final_dict

    def get_hdl(self):
        # 获取hdl
        return self.hdl
