from mltsp import run_in_docker_container as ridc
from mltsp import cfg
from mltsp import build_model
import numpy.testing as npt
import os
import pandas as pd
import shutil
import numpy as np
from sklearn.externals import joblib
try:
    import cPickle as pickle
except ImportError:
    import pickle


def featurize_setup():
    fpaths = []
    fnames = ["asas_training_subset_classes_with_metadata.dat",
              "asas_training_subset.tar.gz", "testfeature1.py"]
    for fname in fnames:
        fpaths.append(os.path.join(os.path.dirname(__file__),
                                   os.path.join("data", fname)))
    for fpath in fpaths:
        shutil.copy(fpath, cfg.UPLOAD_FOLDER)


def featurize_teardown():
    fpaths = [os.path.join(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                           "testfeature1.py")]
    fnames = ["asas_training_subset_classes_with_metadata.dat",
              "asas_training_subset.tar.gz", "testfeature1.py"]
    for fname in fnames:
        fpaths.append(os.path.join(cfg.UPLOAD_FOLDER, fname))
    for fpath in fpaths:
        if os.path.exists(fpath):
            os.remove(fpath)


def test_featurize_in_docker_container():
    """Test main featurize in docker container function"""
    featurize_setup()
    shutil.copy(
        os.path.join(os.path.dirname(__file__),
                     "data/testfeature1.py"),
        cfg.CUSTOM_FEATURE_SCRIPT_FOLDER)
    ridc.featurize_in_docker_container(
        headerfile_path=os.path.join(
            cfg.UPLOAD_FOLDER,
            "asas_training_subset_classes_with_metadata.dat"),
        zipfile_path=os.path.join(cfg.UPLOAD_FOLDER,
                                  "asas_training_subset.tar.gz"),
        features_to_use=["std_err", "freq1_harmonics_freq_0"],
        featureset_key="test", is_test=True, already_featurized=False,
        custom_script_path=os.path.join(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                                        "testfeature1.py"))
    assert(os.path.exists(os.path.join(cfg.FEATURES_FOLDER,
                                       "test_features.csv")))
    assert(os.path.exists(os.path.join(cfg.FEATURES_FOLDER,
                                       "test_classes.npy")))
    assert(os.path.exists(os.path.join(os.path.join(cfg.MLTSP_PACKAGE_PATH,
                                                    "Flask/static/data"),
                                       "test_features_with_classes.csv")))
    os.remove(os.path.join(cfg.FEATURES_FOLDER, "test_classes.npy"))
    df = pd.io.parsers.read_csv(os.path.join(cfg.FEATURES_FOLDER,
                                       "test_features.csv"))
    cols = df.columns
    values = df.values
    os.remove(os.path.join(cfg.FEATURES_FOLDER, "test_features.csv"))
    os.remove(os.path.join(os.path.join(cfg.MLTSP_PACKAGE_PATH,
                                        "Flask/static/data"),
                           "test_features_with_classes.csv"))
    assert("std_err" in cols)
    assert("freq1_harmonics_freq_0" in cols)
    featurize_teardown()


def test_build_model_in_docker_container():
    """Test build model in docker container"""
    shutil.copy(os.path.join(os.path.join(os.path.dirname(__file__), "data"),
                             "test_classes.npy"),
                os.path.join(cfg.FEATURES_FOLDER, "TEMP_TEST01_classes.npy"))
    shutil.copy(os.path.join(os.path.join(os.path.dirname(__file__), "data"),
                             "test_features.csv"),
                os.path.join(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))

    ridc.build_model_in_docker_container("TEMP_TEST01", "TEMP_TEST01", "RF")

    assert os.path.exists(os.path.join(cfg.MODELS_FOLDER, "TEMP_TEST01_RF.pkl"))
    model = joblib.load(os.path.join(cfg.MODELS_FOLDER, "TEMP_TEST01_RF.pkl"))
    assert hasattr(model, "predict_proba")
    os.remove(os.path.join(cfg.MODELS_FOLDER, "TEMP_TEST01_RF.pkl"))
    os.remove(os.path.join(cfg.FEATURES_FOLDER, "TEMP_TEST01_classes.npy"))
    os.remove(os.path.join(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))


def generate_model():
    shutil.copy(os.path.join(os.path.join(os.path.dirname(__file__), "data"),
                             "test_classes.npy"),
                os.path.join(cfg.FEATURES_FOLDER, "TEMP_TEST01_classes.npy"))
    shutil.copy(os.path.join(os.path.join(os.path.dirname(__file__), "data"),
                             "test_features.csv"),
                os.path.join(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    build_model.build_model("TEMP_TEST01", "TEMP_TEST01")
    assert os.path.exists(os.path.join(cfg.MODELS_FOLDER,
                                       "TEMP_TEST01_RF.pkl"))


def test_predict_in_docker_container():
    """Test predict in docker container"""
    generate_model()

    shutil.copy(os.path.join(os.path.dirname(__file__),
                             "data/dotastro_215153.dat"),
                os.path.join(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"))
    shutil.copy(os.path.join(os.path.dirname(__file__),
                             "data/TESTRUN_215153_metadata.dat"),
                cfg.UPLOAD_FOLDER)
    shutil.copy(os.path.join(os.path.dirname(__file__),
                             "data/testfeature1.py"),
                os.path.join(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                             "TESTRUN_CF.py"))

    pred_results_dict = ridc.predict_in_docker_container(
        os.path.join(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"),
        "TEMP_TEST01", "RF", "TEMP_TEST01", "TEMP_TEST01",
        metadata_file=os.path.join(cfg.UPLOAD_FOLDER,
                                   "TESTRUN_215153_metadata.dat"),
        custom_features_script=os.path.join(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                                            "TESTRUN_CF.py"))

    npt.assert_equal(
        len(pred_results_dict["TESTRUN_215153.dat"]["pred_results_list"]),
        3)

    os.remove(os.path.join(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"))
    os.remove(os.path.join(cfg.UPLOAD_FOLDER, "TESTRUN_215153_metadata.dat"))
    os.remove(os.path.join(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    os.remove(os.path.join(cfg.FEATURES_FOLDER, "TEMP_TEST01_classes.npy"))
    os.remove(os.path.join(cfg.MODELS_FOLDER, "TEMP_TEST01_RF.pkl"))
    os.remove(os.path.join(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER, "TESTRUN_CF.py"))
