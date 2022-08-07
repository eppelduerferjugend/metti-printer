
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
    count_width = 5
    price_width = 8
    name_width = self.width - count_width - price_width
    name_wrapper = textwrap.TextWrapper(width=name_width)

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
    p.text('\n{} #{}\n\n'.format(created_at.strftime('%d.%m.%Y %H:%M'), order['number']))

    # Item list
    p.set(align='left')
    for item in order['items']:
      # Item count
      p.text('{:2}x  '.format(item['quantity']))

      # Wrap item name in name column
      name_lines = name_wrapper.wrap(text=item['product']['name'])

      # First name line
      p.text(name_lines[0])

      # Following name lines with left padding
      i = 1
      while i < len(name_lines):
        p.text('\n{}{}'.format(' ' * count_width, name_lines[i]))
        i += 1

      # Price tag with left padding
      if item['product']['unitPrice'] != 0:
        price_padding = name_width - len(name_lines[-1])
        p.text('{}{:7.2f}'.format(' ' * price_padding, item['product']['unitPrice'] / 100))

      p.text('\n')


    # Comment
    p.set(align='left')
    p.text('\n')
    if order['note']:
      p.text('Kommentar: {}\n\n'.format(order['note']))

    # Calculate order price
    order_price = 0
    for item in order['items']:
      order_price += item['quantity'] * item['product']['unitPrice']

    # Details
    p.text('Total: {:4.2f}\n'.format(order_price / 100))
    p.text('Service: {}\n'.format(order['assignee']['name']))

    # Cut here
    p.cut()

    return p.output

  def stop(self):
    print('[Printer] Stopping printer thread.')
    self.stop_flag.set()
