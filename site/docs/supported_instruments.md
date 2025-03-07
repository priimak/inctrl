Supported Instruments
=====================

Below is a table indicating which instruments does InCtrl library supports.
There are two important things to note. First of allthat drivers are developed based
on the documentation which usually applies to the whole family of instruments and
hence it is implied that all instruments in that family are supported. That is
expressed as regex expression in the "_Supported models_" column. At the same time
drivers are tested on the very particular instrument model (that is in
the "_Tested on model_" column). Hence, ultimately we can guarantee support only
for those instruments that were tested against.

Also, important to note that supported means that all the API calls/functions are
supported. That does not mean that all functionality available on the given instrument
is exposed through this API. 100% support refers to support of what is only defined
in the _InCtrl_ API.

| Type         | Make    | Tested on model | Supported models |
|--------------|---------|-----------------|------------------|
| Oscilloscope | Siglent | SDS804X HD      | ^SDS8.*$         |