# SecureVdetector
SecureVdetector utilizes docker containers to check the legitimacy
of files and check its effects on a specific operating system.

It utilizes the *docker api* along with basic linux packages in order
to measure 3 consequences of executing the file:
1) Amount of memory and CPU consumption
2) File I/O operations (increase in storage)
3) Network usage

## Basic Usage
```python
from secureVdetector import fileTester

# Check results from running a forkbomb on Ubuntu
testFile = fileTester.TestFile('testViruses/forkbomb.sh')
```

### Example output given a **[forkbomb](testViruses/forkbomb.sh)** as input
```output
# Both memory and cpu are consumed to their max potential
Max Memory Usage is 100.0%, Max CPU Usage is 100%

# Increase in FS is due to deb installs
Increase in Size of Filesystem: 3.66 MB

# Forkbomb does not affect network
Max Network Usage is 0 KB
```