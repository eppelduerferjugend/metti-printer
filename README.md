
# metti-printer

## Provisioning

Install [python-escpos](https://github.com/python-escpos/python-escpos) from GitHub.

We assume the repository to be placed at `/srv/metti-printer` on e.g. a Raspberry Pi.

```bash
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install python3 python3-pip python3-full libopenjp2-7 git

sudo mkdir /opt/python-venv
python3 -m venv /opt/python-venv/
/opt/python-venv/bin/pip3 install requests pyusb
/opt/python-venv/bin/pip3 pip3 install git+https://github.com/python-escpos/python-escpos.git
```

Configure `src/constants.py`:

```bash
cp src/constants.py.example src/constants.py
```

Sync changes from local repostory to the Raspberry Pi:

```bash
rsync -aP --delete . pi@hostname:/srv/metti-printer/
```

To grant permission to the printer via USB without being root, add the file `/etc/udev/rules.d/10-crew.rules` with the following content:

```text
SUBSYSTEM !="usb_device", ACTION !="add", GOTO="datalogger_rules_end"
SYSFS{idVendor} =="VENDOR_ID", SYSFS{idProduct} =="PRODUCT_ID", SYMLINK+="datalogger"
MODE="0666", OWNER="crew", GROUP="root"
LABEL="datalogger_rules_end"
```

In it, replace `VENDOR_ID` by the vendor id and `PRODUCT_ID` by the product id of the USB device that can be determined by running `lsusb` and identifying the USB printer.

To make the python printer server start at boot time as a daemon, install it as a service like so:

```bash
# Configure service
sudo ln -s /srv/metti-printer/provisioning/metti-printer.service /etc/systemd/system/metti-printer.service

# Enable service
sudo systemctl enable metti-printer
sudo systemctl daemon-reload

# (Re-)start service
sudo systemctl start metti-printer
sudo systemctl restart metti-printer

# Show service status
sudo systemctl status metti-printer

# Follow service logs
journalctl -u metti-printer.service -f
```

## See also

- [Getting a USB receipt printer working on Linux](https://mike42.me/blog/2015-03-getting-a-usb-receipt-printer-working-on-linux)
