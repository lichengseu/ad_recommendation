from configparser import ConfigParser

cp = ConfigParser()
cp.read("config/path.cfg")
print(cp.get("raw_data", "ad"))
cp.read("config/parameter.cfg")
print(type(cp.get("advertisers", "threshold")))

