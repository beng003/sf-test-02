import csv


def write_id_to_csv(count):
    with open("id_{}.csv".format(str(count)), "w") as f:
        writer = csv.writer(f)
        writer.writerow(["id"])
        for v in range(count):
            writer.writerow([str(v)])

write_id_to_csv(3)
# 单机版，sf.utils.testing.cluster_def 建立SPU。请注意它只能在单机模式下使用，因为它使用了 127.0.0.1 作为默认ip。
import secretflow as sf

sf.shutdown()
sf.init(['alice', 'bob', 'carol'], num_cpus=8, log_to_driver=False)

# 虚拟化三个逻辑设备
alice, bob = sf.PYU('alice'), sf.PYU('bob')
spu = sf.SPU(sf.utils.testing.cluster_def(['alice', 'bob']))

# 求交
input_path = {alice: 'id_count.csv', bob: 'id_count.csv'}
output_path = {alice: '.data/alice_psi.csv', bob: '.data/bob_psi.csv'}
spu.psi_csv('id', input_path, output_path, 'alice', protocol="ECDH_PSI_2PC")
#spu.psi_csv('id', input_path, output_path, 'alice', protocol="KKRT_PSI_2PC")
#spu.psi_csv('id', input_path, output_path, 'alice', protocol="BC22_PSI_2PC")
