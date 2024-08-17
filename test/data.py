import pickle

# 创建一个示例字典
data = 11

# 将对象序列化并保存到文件
with open('/home/beng003/python_project/sf-test/data/alice_data.txt', 'wb') as f:
    pickle.dump(data, f)

print("数据已序列化并保存到文件。")

# 从文件中加载并反序列化对象
with open('/home/beng003/python_project/sf-test/data/alice_data.txt', 'rb') as f:
    v_alice = pickle.load(f)  # 使用二进制读取模式加载序列化对象

print("从文件中加载的数据：")
print(v_alice)


# 创建一个示例字典
data = 22

# 将对象序列化并保存到文件
with open('/home/beng003/python_project/sf-test/data/bob_data.txt', 'wb') as f:
    pickle.dump(data, f)

print("数据已序列化并保存到文件。")

# 从文件中加载并反序列化对象
with open('/home/beng003/python_project/sf-test/data/bob_data.txt', 'rb') as f:
    v_bob = pickle.load(f)  # 使用二进制读取模式加载序列化对象

print("从文件中加载的数据：")
print(v_bob)

# 从文件中加载并反序列化对象
with open("/home/beng003/python_project/sf-test/data/alice_add_bob_data.txt", 'rb') as f:
    v_bob = pickle.load(f)  # 使用二进制读取模式加载序列化对象

print("从文件中加载的数据：")
print(v_bob)