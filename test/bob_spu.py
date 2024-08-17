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


link_desc = {
    "recv_timeout_ms": 6000,
}

spu_device = sf.SPU(cluster_def=cluster_def, link_desc=link_desc)
alice_data_pyu = alice.load("/home/beng003/python_project/sf-test/data/alice_data.txt")
alice_data_spu = alice_data_pyu.to(spu_device)
bob_data_pyu = bob.load("/home/beng003/python_project/sf-test/data/bob_data.txt")
bob_data_spu = bob_data_pyu.to(spu_device)


print("数据读取完成")


def apply_operator(a, b):
    return a + b


alice_add_bob_data = spu_device(apply_operator)(alice_data_spu, bob_data_spu)
print("计算完成")
print(alice_add_bob_data)

alice_add_bob_data_m = sf.reveal(alice_add_bob_data)
print(alice_add_bob_data_m)

sf.shutdown()
