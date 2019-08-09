
from datetime import datetime
from escpos import printer

# Constants
PRINTER_VENDOR_ID = 0x1a86
PRINTER_PRODUCT_ID = 0x7584
PRINTER_PROFILE = 'TM-T88IV'
PRINTER_TIMEOUT = 500 # in ms

# Dummy data
order = {
  'number': 23,
  'waiter': "Fränz",
  'table': "U2",
  'comment': "Vill onser Hemecht si och, ménger d'Stroos get si, Heck schlon fir et.",
  'created_at_u': 1565345524,
  'order_price': 25.5,
  'items': [
    {
      'name': "Coca-Cola Glas",
      'quantity': 4
    },
    {
      'name': "Fanta Glas",
      'quantity': 2
    },
    {
      'name': "Kaffi",
      'quantity': 1
    },
    {
      'name': "Schokelas Mousse vum Pit",
      'quantity': 3
    },
    {
      'name': "Luxlait Glace Schokela um Still",
      'quantity': 2
    }
  ]
}

# Create receipt printer instance
receiptPrinter = printer.Usb(
  PRINTER_VENDOR_ID,
  PRINTER_PRODUCT_ID,
  profile=PRINTER_PROFILE,
  timeout=PRINTER_TIMEOUT
)

# Create dummy printer instance to prepare the receipt
p = printer.Dummy(profile='TM-T88IV')

# Header image
p.image('assets/header.png')
p.text('\n')

# Table
p.set(align='center', double_width=True, double_height=True)
p.text('Dësch {}\n'.format(order['table']))

# Date, time and number
p.set(align='center', double_width=False, double_height=False)
order_date = datetime.fromtimestamp(order['created_at_u'])
order_date_formatted = order['created_at'].strftime('%d.%m.%Y %H:%M:%S')
p.text('\n{} #{}\n\n'.format(order_date_formatted, order['number']))

# Item list
p.set(align='left', double_width=False, double_height=False)

for item in order['items']:
  p.text('{:4}x {}\n'.format(item['quantity'], item['name']))

# Comment
p.text('\n')
if order['comment']:
  p.text('Kommentar: {}\n\n'.format(order['comment']))

# Details
p.text('Total: {:5.2f}€\n'.format(order['order_price']))
p.text('Service: {}\n'.format(order['waiter']))

# Cut here
p.cut()

# Print receipt
receiptPrinter._raw(p.output)
