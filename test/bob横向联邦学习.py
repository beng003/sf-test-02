# alice.py
import sys
import os

# 动态添加项目根目录到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.process_utils import kill_port_process
import secretflow as sf

# Check the version of your SecretFlow
print("The version of SecretFlow: {}".format(sf.__version__))

# In case you have a running secretflow runtime already.
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
alice, bob = sf.PYU("alice"), sf.PYU("bob")


from secretflow.data.horizontal import read_csv
from secretflow.security.aggregation import SecureAggregator
from secretflow.security.compare import SPUComparator
from secretflow.utils.simulation.datasets import load_dermatology

aggr = SecureAggregator(alice, [alice, bob])


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


comp = SPUComparator(t_spu)
data = load_dermatology(parts=[alice, bob], aggregator=aggr, comparator=comp)
data.fillna(value=0, inplace=True)

params = {
    # XGBoost parameter tutorial
    # https://xgboost.readthedocs.io/en/latest/parameter.html
    "max_depth": 4,  # max depth
    "eta": 0.3,  # learning rate
    "objective": "multi:softmax",  # objection function，support "binary:logistic","reg:logistic","multi:softmax","multi:softprob","reg:squarederror"
    "min_child_weight": 1,  # The minimum value of weight
    "lambda": 0.1,  # L2 regularization term on weights (xgb's lambda)
    "alpha": 0,  # L1 regularization term on weights (xgb's alpha)
    "max_bin": 10,  # Max num of binning
    "num_class": 6,  # Only required in multi-class classification
    "gamma": 0,  # Same to min_impurity_split,The minimux gain for a split
    "subsample": 1.0,  # Subsample rate by rows
    "colsample_bytree": 1.0,  # Feature selection rate by tree
    "colsample_bylevel": 1.0,  # Feature selection rate by level
    "eval_metric": "merror",  # supported eval metric：
    # 1. rmse
    # 2. rmsle
    # 3. mape
    # 4. logloss
    # 5. error
    # 6. error@t
    # 7. merror
    # 8. mlogloss
    # 9. auc
    # 10. aucpr
    # Special params in SFXgboost
    # Required
    "hess_key": "hess",  # Required, Mark hess columns, optionally choosing a column name that is not in the data set
    "grad_key": "grad",  # Required，Mark grad columns, optionally choosing a column name that is not in the data set
    "label_key": "class",  # Required，ark label columns, optionally choosing a column name that is not in the data set
}

print("Data loaded successfully")
from secretflow.ml.boost.homo_boost import SFXgboost

bst = SFXgboost(server=alice, clients=[alice, bob])
bst.train(data, data, params=params, num_boost_round=6)

sf.shutdown()

print(bst)
