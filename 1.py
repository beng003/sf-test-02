import secretflow as sf
sf.shutdown()
sf.init(parties=['alice', 'bob'], address='local')
alice = sf.PYU('alice')
bob = sf.PYU('bob')
a = alice(lambda x : x + 1)(2)
print(alice(lambda x : x + 1)(2))
print(bob(lambda x : x - 1)(2))