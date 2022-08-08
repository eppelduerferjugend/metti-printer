
import threading, time, textwrap
import state
from escpos import printer
import datetime

class Printer_Thread(threading.Thread):

  def __init__(self, vendorId, productId, profile, timeout=1000, width=43):
    threading.Thread.__init__(self)
    self.profile = profile
    self.width = width
    self.printer = printer.Usb(vendorId, productId, profile=profile, timeout=timeout)
    self.printer.line_spacing(50)
    self.stop_flag = threading.Event()

  def run(self):
    print('[Printer] Printer thread started.')

    # Loop through the order queue until the stop flag is raised
    while not self.stop_flag.is_set():
      if state.printer_index < len(state.order_queue):

        # Retrieve next order from queue
        order = state.order_queue[state.printer_index]

        try:
          # Try to render and print order
          print('[Printer] Rendering receipt for order id {}.'.format(order['id']))
          receipt = self.render_order(order)

          print('[Printer] Printing receipt for order id {}.'.format(order['id']))
          self.printer._raw(receipt)

          # Printing cooldown to prevent jibberish
          time.sleep(1)

          # Mark order as completed
          state.printer_index += 1

        except Exception as err:
          # Wait after error (printer unavailable, paper empty, etc)
          print('[Printer] Error while printing: {}'.format(str(err)))
          time.sleep(1)

      else:
        # Loop until an order is available
        time.sleep(1)
        continue

  def render_order(self, order):
    """ Renders a single order on a receipt """

    # Magic wrapping numbers
    count_width = 7
    price_width = 10
    name_width = self.width - count_width - price_width
    name_wrapper = textwrap.TextWrapper(width=name_width)

    # Calculate order price
    order_price = 0
    for item in order['items']:
      order_price += item['quantity'] * item['product']['unitPrice']

    p = printer.Dummy(profile=self.profile)

    # Header image
    p.image('assets/header.png')
    p.text('\n')

    # Table
    p.set(align='center', double_width=True, double_height=True)
    p.text('Dësch {}\n'.format(order['table']['name']))

    # Date time and number
    p.set(align='center', double_width=False, double_height=False)
    created_at = datetime.datetime.fromisoformat(order['createdAt'].replace('Z', '+00:00'))
    p.text('\n{} {}\n\n'.format(created_at.strftime('%d.%m.%Y %H:%M'), order['number']))

    # Item list
    p.set(align='left')
    p.text('┌────┬─{}─┬───────┐\n'.format(name_width * '─'))
    for index, item in enumerate(order['items']):
      # Wrap item name in name column
      name_lines = name_wrapper.wrap(text=item['product']['name'])

      i = 0
      while i < len(name_lines):
        # Quantity
        if i == 0:
          p.text('│ {:2} │ '.format(item['quantity']))
        else:
          p.text('│    │ ')

        # Wrapped text
        price_padding = name_width - len(name_lines[i])
        p.text('{}{}'.format(name_lines[i], ' ' * price_padding))

        if i == 0:
          if item['product']['unitPrice'] != 0:
            p.text(' │ {:5.2f} │\n'.format(item['product']['unitPrice'] / 100))
          else:
            p.text(' │ ╌╌╌╌╌ │\n')
        else:
          p.text(' │       │\n')

        i += 1

      if index < len(order['items']) - 1:
        p.text('├────┼─{}─┼───────┤\n'.format(name_width * '─'))
      else:
        p.text('╞════╧═{}═╧═══════╡\n'.format(name_width * '═'))

    # Total
    padding = self.width - 10 - 10
    p.text('│ Total {}{:10.2f} │\n'.format(padding * ' ', order_price / 100))
    p.text('└──────{}─────────┘\n'.format(name_width * '─'))

    # Details
    p.set(align='left')
    p.text('\n')
    if order['note']:
      p.text('Kommentar: {}\n'.format(order['note']))
    p.text('Service: {}\n'.format(order['assignee']['name']))

    # Cut here
    p.cut()

    return p.output

  def stop(self):
    print('[Printer] Stopping printer thread.')
    self.stop_flag.set()
