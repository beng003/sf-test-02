import secretflow as sf

# Check the version of your SecretFlow
print("The version of SecretFlow: {}".format(sf.__version__))

# In case you have a running secretflow runtime already.
sf.shutdown()

sf.init(['alice', 'bob'], address='local')
alice = sf.PYU("alice")
bob = sf.PYU("bob")
print("Alice and Bob are ready to go!")


spu_device = sf.SPU(sf.utils.testing.cluster_def(parties=['alice', 'bob']))
print("*****************************************************Alice SPU")

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


alice_add_bob_data_pyu = alice_add_bob_data.to(bob)
print("*****************************************************Alice得到数据")

bob.dump(
    alice_add_bob_data_pyu,
    "/home/beng003/python_project/sf-test/data/alice_add_bob_data.txt",
)
print("***********************************************数据存储完成")

# alice_add_bob_data_m = sf.reveal(alice_add_bob_data_pyu)
# print("*****************************************************Alice解密数据")
# print(alice_add_bob_data_m)

sf.shutdown()
