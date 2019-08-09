
# metti-printer

## Install

Install [python-escpos](https://github.com/python-escpos/python-escpos) from GitHub.

```bash
pip3 install requests
pip3 install git+https://github.com/python-escpos/python-escpos.git
```

Configure `src/constants.py`:

```bash
cp src/constants.py.example src/constants.py
```

## Run

```bash
PYTHONIOENCODING=utf-8 python3 src/index.py
```

## See also

- [Getting a USB receipt printer working on Linux](https://mike42.me/blog/2015-03-getting-a-usb-receipt-printer-working-on-linux)
