
# metti-printer

## Deployment

Install [python-escpos](https://github.com/python-escpos/python-escpos) from GitHub.

```bash
sudo apt-get install python3 python3-pip libopenjp2-7

# Run with the same user the script is run
pip3 install requests
pip3 install git+https://github.com/python-escpos/python-escpos.git
```

Configure `src/constants.py`:

```bash
cp src/constants.py.example src/constants.py
```

To grant permission to the printer via USB without being root, add the file `/etc/udev/rules.d/10-crew.rules` with the following content:

```text
SUBSYSTEM !="usb_device", ACTION !="add", GOTO="datalogger_rules_end"
SYSFS{idVendor} =="VENDOR_ID", SYSFS{idProduct} =="PRODUCT_ID", SYMLINK+="datalogger"
MODE="0666", OWNER="crew", GROUP="root"
LABEL="datalogger_rules_end"
```

In it, replace `VENDOR_ID` by the vendor id and `PRODUCT_ID` by the product id of the USB device that can be determined by running `lsusb` and identifying the USB printer.

## See also

- [Getting a USB receipt printer working on Linux](https://mike42.me/blog/2015-03-getting-a-usb-receipt-printer-working-on-linux)
