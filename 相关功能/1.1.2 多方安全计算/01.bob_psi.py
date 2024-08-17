# bob.py
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

# aggr = SecureAggregator(alice, [alice, bob])


import spu

cluster_def = {
    "nodes": [
        {
            "party": "alice",
            # The address for other peers.
            "address": "ecm-01:" + str(spu_port),
            # The listen address of this node.
            # Optional. Address will be used if listen_address is empty.
            "listen_address": "0.0.0.0:" + str(spu_port),
        },
        {
            "party": "bob",
            "address": "ecm-02:" + str(spu_port),
            "listen_address": "0.0.0.0:" + str(spu_port),
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
    "recv_timeout_ms": 6000,
}

print("*****************************************************Bob SPU")
spu_device = sf.SPU(cluster_def=cluster_def, link_desc=link_desc)

print("*****************************************************Bob PSI")
input_path = {
    alice: "/home/beng003/python_project/sf-test/data/v_alice.csv",
    bob: "/home/beng003/python_project/sf-test/data/v_bob.csv",
}
output_path = {
    alice: "/home/beng003/python_project/sf-test/data/alice_psi.csv",
    bob: "/home/beng003/python_project/sf-test/data/bob_psi.csv",
}
spu_device.psi_csv("uid", input_path, output_path, "alice")

# from secretflow.data.vertical import read_csv as v_read_csv

# vdf = v_read_csv(input_path, spu=spu_device, keys="uid", drop_keys="uid")
# print("*****************************************************Bob PSI")
# vdf.to_csv(output_path, index=False)

sf.shutdown()
