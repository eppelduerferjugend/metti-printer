
import threading, time
import state
from escpos import printer
from datetime import datetime

class Printer_Thread(threading.Thread):

  def __init__(self, vendorId, productId, profile, timeout=1000):
    threading.Thread.__init__(self)
    self.profile = profile
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
    p = printer.Dummy(profile=self.profile)

    # Header image
    p.image('assets/header.png')
    p.text('\n')

    # Table
    p.set(align='center', double_width=True, double_height=True)
    p.text('Dësch {}\n'.format(order['table']))

    # Date, time and number
    p.set(align='center', double_width=False, double_height=False)
    order_date = datetime.fromtimestamp(order['created_at_u'])
    order_date_formatted = order_date.strftime('%d.%m.%Y %H:%M:%S')
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
    p.text('Total: {:3.2f}€\n'.format(order['order_price']))
    p.text('Service: {}\n'.format(order['waiter']))

    # Cut here
    p.cut()

    return p.output

  def stop(self):
    print('[Printer] Stopping printer thread.')
    self.stop_flag.set()
