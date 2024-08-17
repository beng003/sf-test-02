from secretflow.stats import BiClassificationEval, ScoreCard
from secretflow.stats import prediction_bias_eval
from secretflow.stats.biclassification_eval import BiClassificationEval
from secretflow.ml.boost.ss_xgb_v import Xgb
from secretflow.ml.linear.ss_sgd import SSRegression
import jax.numpy as jnp
from secretflow.stats.core.utils import equal_range
from secretflow.stats import psi_eval
from secretflow.data.split import train_test_split
from secretflow.stats.ss_vif_v import VIF
from secretflow.stats.ss_pearsonr_v import PearsonR
from secretflow.preprocessing import StandardScaler
from secretflow.preprocessing.encoder import OneHotEncoder
from secretflow.preprocessing.binning.vert_bin_substitution import VertBinSubstitution
from secretflow.preprocessing.binning.vert_woe_binning import VertWoeBinning
from secretflow.stats.table_statistics import table_statistics
from secretflow.data.vertical import read_csv as v_read_csv
import numpy as np
import pandas as pd
import spu
import secretflow as sf

# alice.py
import sys
import os

# 动态添加项目根目录到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.process_utils import kill_port_process
import secretflow as sf

sf.shutdown()

pyu_port = 16307
spu_port = 11666

cluster_config = {
    "parties": {
        "alice": {
            # replace with alice's real address.
            "address": "ecm-01:" + str(pyu_port),
            "listen_addr": "0.0.0.0:" + str(pyu_port),
        },
        "bob": {
            # replace with bob's real address.
            "address": "ecm-02:" + str(pyu_port),
            "listen_addr": "0.0.0.0:" + str(pyu_port),
        },
    },
    "self_party": "bob",
}

kill_port_process(pyu_port)
kill_port_process(spu_port)

tls_config = {
    "ca_cert": "/home/beng003/certificate/alice_ca.crt",
    "cert": "/home/beng003/certificate/bob_server_cert.crt",
    "key": "/home/beng003/certificate/bob_server_key.key",
}


sf.init(address="ecm-02:6379", cluster_config=cluster_config, tls_config=tls_config)
# sf.init(address="ecm-02:6379", cluster_config=cluster_config)

alice = sf.PYU("alice")
bob = sf.PYU("bob")

import spu

cluster_def = {
    "nodes": [
        {
            "party": "alice",
            # The address for other peers.
            "address": "ecm-01:" + str(spu_port),
            # The listen address of this node.
            # Optional. Address will be used if listen_address is empty.
            "listen_address": "",
        },
        {
            "party": "bob",
            "address": "ecm-02:" + str(spu_port),
            "listen_address": "",
        },
    ],
    "runtime_config": {
        "protocol": spu.spu_pb2.SEMI2K,
        "field": spu.spu_pb2.FM128,
        "sigmoid_mode": spu.spu_pb2.RuntimeConfig.SIGMOID_REAL,
    },
}

# link_desc = {
#     "connect_retry_times": 20,
#     "connect_retry_interval_ms": 5000,
#     "recv_timeout_ms": 25000,
#     "http_max_payload_size": 1048576,
#     "http_timeout_ms": 10000,
#     "throttle_window_size": 1024,
# }

link_desc = {
    "recv_timeout_ms": 36000,
}

t_spu = sf.SPU(cluster_def=cluster_def, link_desc=link_desc)


print("Reading data...")
alice_path = "/home/beng003/data/v_alice.csv"
bob_path = "/home/beng003/data/v_bob.csv"
vdf = v_read_csv(
    {alice: alice_path, bob: bob_path},
    spu=t_spu,
    keys="uid",
    drop_keys="uid",
    psi_protocl="ECDH_PSI_2PC",
)
print("Data read successfully!")


pd.set_option("display.max_rows", None)
data_stats = table_statistics(vdf)
print(data_stats)
pd.reset_option("display.max_rows")

vdf["education"] = vdf["education"].replace(
    {"tertiary": 3, "secondary": 2, "primary": 1, "unknown": np.NaN}
)

vdf["default"] = vdf["default"].replace({"no": 0, "yes": 1, "unknown": np.NaN})

vdf["housing"] = vdf["housing"].replace({"no": 0, "yes": 1, "unknown": np.NaN})

vdf["loan"] = vdf["loan"].replace({"no": 0, "yes": 1, "unknown": np.NaN})

vdf["month"] = vdf["month"].replace(
    {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    }
)

vdf["y"] = vdf["y"].replace(
    {
        "no": 0,
        "yes": 1,
    }
)

print(sf.reveal(vdf.partitions[alice].data))
print(sf.reveal(vdf.partitions[bob].data))


vdf["education"] = vdf["education"].fillna(vdf["education"].mode())
vdf["default"] = vdf["default"].fillna(vdf["default"].mode())
vdf["housing"] = vdf["housing"].fillna(vdf["housing"].mode())
vdf["loan"] = vdf["loan"].fillna(vdf["loan"].mode())

print(sf.reveal(vdf.partitions[alice].data))
print(sf.reveal(vdf.partitions[bob].data))


binning = VertWoeBinning(t_spu)
bin_rules = binning.binning(
    vdf,
    binning_method="chimerge",
    bin_num=4,
    bin_names={alice: [], bob: ["duration"]},
    label_name="y",
)

woe_sub = VertBinSubstitution()
vdf, _ = woe_sub.substitution(vdf, bin_rules)

print(sf.reveal(vdf.partitions[alice].data))
print(sf.reveal(vdf.partitions[bob].data))


encoder = OneHotEncoder()
# for vif and correlation only
vdf_hat = vdf.drop(columns=["job", "marital", "contact", "month", "day", "poutcome"])

tranformed_df = encoder.fit_transform(vdf["job"])
vdf[tranformed_df.columns] = tranformed_df

tranformed_df = encoder.fit_transform(vdf["marital"])
vdf[tranformed_df.columns] = tranformed_df

tranformed_df = encoder.fit_transform(vdf["contact"])
vdf[tranformed_df.columns] = tranformed_df

tranformed_df = encoder.fit_transform(vdf["month"])
vdf[tranformed_df.columns] = tranformed_df

tranformed_df = encoder.fit_transform(vdf["day"])
vdf[tranformed_df.columns] = tranformed_df

tranformed_df = encoder.fit_transform(vdf["poutcome"])
vdf[tranformed_df.columns] = tranformed_df

vdf = vdf.drop(columns=["job", "marital", "contact", "month", "day", "poutcome"])

print(sf.reveal(vdf.partitions[alice].data))
print(sf.reveal(vdf.partitions[bob].data))


X = vdf.drop(columns=["y"])
y = vdf["y"]
scaler = StandardScaler()
X = scaler.fit_transform(X)
vdf[X.columns] = X
print(sf.reveal(vdf.partitions[alice].data))
print(sf.reveal(vdf.partitions[bob].data))


pd.set_option("display.max_rows", None)
data_stats = table_statistics(vdf)

pd.reset_option("display.max_rows")


pearson_r_calculator = PearsonR(t_spu)
corr_matrix = pearson_r_calculator.pearsonr(vdf_hat)


np.set_printoptions(formatter={"float": lambda x: "{0:0.3f}".format(x)})


vif_calculator = VIF(t_spu)
vif_results = vif_calculator.vif(vdf_hat)
print(vdf_hat.columns)
print(vif_results)


random_state = 1234

train_vdf, test_vdf = train_test_split(vdf, train_size=0.8, random_state=random_state)

train_x = train_vdf.drop(columns=["y"])
train_y = train_vdf["y"]

test_x = test_vdf.drop(columns=["y"])
test_y = test_vdf["y"]

stats_df = table_statistics(train_x["balance"])

min_val, max_val = stats_df["min"], stats_df["max"]


split_points = equal_range(jnp.array([min_val, max_val]), 3)
balance_psi_score = psi_eval(train_x["balance"], test_x["balance"], split_points)


lr_model = SSRegression(t_spu)
lr_model.fit(
    x=train_x,
    y=train_y,
    epochs=3,
    learning_rate=0.1,
    batch_size=1024,
    sig_type="t1",
    reg_type="logistic",
    penalty="l2",
    l2_norm=0.5,
)


xgb = Xgb(t_spu)
params = {
    "num_boost_round": 3,
    "max_depth": 5,
    "sketch_eps": 0.25,
    "objective": "logistic",
    "reg_lambda": 0.2,
    "subsample": 1,
    "colsample_by_tree": 1,
    "base_score": 0.5,
}
xgb_model = xgb.train(params=params, dtrain=train_x, label=train_y)

lr_y_hat = lr_model.predict(x=test_x, batch_size=1024, to_pyu=bob)

xgb_y_hat = xgb_model.predict(dtrain=test_x, to_pyu=bob)


biclassification_evaluator = BiClassificationEval(
    y_true=test_y, y_score=lr_y_hat, bucket_size=20
)
lr_report = sf.reveal(biclassification_evaluator.get_all_reports())

print(f"positive_samples: {lr_report.summary_report.positive_samples}")
print(f"negative_samples: {lr_report.summary_report.negative_samples}")
print(f"total_samples: {lr_report.summary_report.total_samples}")
print(f"auc: {lr_report.summary_report.auc}")
print(f"ks: {lr_report.summary_report.ks}")
print(f"f1_score: {lr_report.summary_report.f1_score}")

biclassification_evaluator = BiClassificationEval(
    y_true=test_y, y_score=xgb_y_hat, bucket_size=20
)
xgb_report = sf.reveal(biclassification_evaluator.get_all_reports())

print(f"positive_samples: {xgb_report.summary_report.positive_samples}")
print(f"negative_samples: {xgb_report.summary_report.negative_samples}")
print(f"total_samples: {xgb_report.summary_report.total_samples}")
print(f"auc: {xgb_report.summary_report.auc}")
print(f"ks: {xgb_report.summary_report.ks}")
print(f"f1_score: {xgb_report.summary_report.f1_score}")


prediction_bias = prediction_bias_eval(
    test_y, lr_y_hat, bucket_num=4, absolute=True, bucket_method="equal_width"
)

sf.reveal(prediction_bias)

xgb_pva_score = prediction_bias_eval(
    test_y, xgb_y_hat, bucket_num=4, absolute=True, bucket_method="equal_width"
)

sf.reveal(xgb_pva_score)


sc = ScoreCard(20, 600, 20)
score = sc.transform(xgb_y_hat)

print("The version of SecretFlow: {}".format(sf.__version__))  # (1)
sf.shutdown()
print("The version of SecretFlow: {}".format(sf.__version__))  # (1)
