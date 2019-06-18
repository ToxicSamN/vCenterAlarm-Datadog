# pyucs

This is a custom ucs module that adds some functionality to the ucsmsdk.
The ucsmsdk module is a series of basic methods such as query_dn or query_classid. There isn't a whole lot of additional 
capabilities. So pyucs attempts to address some fo this such as providing a get_vnic or get_service_profile methods
that allows more targeted approaches. This module is still a work in progress but is a good start.
Again this is a custom module so there are some things that fit with only my environment such as the pyucs.credentials module
that relies upon my own credentialstore API.


## Installation
From GitHub repo
```
python setup.py install
```
From PyPi
```
pip install pyucs-samn
```

## Import the Module

```
from pyucs.ucs import Ucs
from pyucs.statsd.collector import StatsCollector
```


