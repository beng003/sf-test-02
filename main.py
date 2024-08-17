import secretflow as sf

sf.shutdown()
cluster_config ={
    'parties': {
        'alice': {
            # replace with alice's real address.
            'address': '211.87.232.46:6307',
            'listen_addr': '211.87.232.46:6407'
        },
        'bob': {
            # replace with bob's real address.
            'address': '211.87.232.47:6307',
            'listen_addr': '211.87.232.47:6407'
        },
    },
    'self_party': 'alice'
}
tls_config = {
	"ca_cert":"ca root cert of other parties",
	"cert":"server cert of alice in pem",
	"key":"server cert of alice in pem",
}
# sf.init(address='211.87.232.46:6207', cluster_config=cluster_config,tls_config=tls_config)
sf.init(address='211.87.232.46:6207', cluster_config=cluster_config)