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


sf.shutdown()
