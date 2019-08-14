#!/usr/bin/env python3

import threading, time, signal, requests
import state, constants
from printer import Printer_Thread

class ServiceExit(Exception):
    """
    Custom exception which is used to trigger the clean exit
    of all running threads and the main program.
    """
    pass

def shutdown_handler(signum, frame):
  """ Raises an exception to gracefully end the process. """
  print('Caught signal {}'.format(signum))
  raise ServiceExit

def complete_orders(orders):
  """ Marks the given order objects as completed. """
  order_ids = list(map(lambda order: order['id'], orders))
  print('Mark orders {} as completed.'.format(', '.join(map(str, order_ids))))

  try:
    response = requests.request(
      'POST',
      constants.service_root + '/order/complete',
      auth=constants.service_auth,
      json=order_ids)

    return response.status_code == 200

  except Exception as err:
    print('Marking orders failed: {}'.format(str(err)))
    return False

def fetch_incomplete_orders(destination):
  """ Fetches incomplete orders for the given destination from the service. """
  try:
    response = requests.request(
      'GET',
      constants.service_root + '/order/incomplete/' + str(destination),
      auth=constants.service_auth)

    if response.status_code == 200:
      return response.json()

  except Exception as err:
    print('Fetching incomplete orders failed: {}'.format(str(err)))

  return []

def main():
  # Register shutdown handlers
  signal.signal(signal.SIGTERM, shutdown_handler)
  signal.signal(signal.SIGINT, shutdown_handler)

  # Initial state
  state.order_queue = []
  state.printer_index = 0
  state.completion_index = 0

  try:
    # Start the printing thread
    printer_thread = Printer_Thread(
      constants.printer_vendor_id,
      constants.printer_product_id,
      constants.printer_profile,
      constants.printer_timeout,
      constants.printer_width)
    printer_thread.start()

    # Daemon loop
    while True:

      # Mark printed orders as completed
      printer_index = state.printer_index
      if state.completion_index < printer_index:
        printed_orders = state.order_queue[state.completion_index:printer_index]
        if complete_orders(printed_orders):
          state.completion_index = printer_index
        else:
          time.sleep(2)
          continue

      # Check for new orders
      orders = fetch_incomplete_orders(constants.destination)

      # Retrieve orders that are in progress
      active_orders = state.order_queue[state.completion_index:]
      active_order_ids = list(map(lambda order: order['id'], active_orders))

      for order in orders:
        # Append order to queue if it is not in the print queue
        # If the order has been completed and reopened in the past
        # it gets added again to the printing queue
        if not order['id'] in active_order_ids:
          print('Found new incomplete order id {}.'.format(order['id']))
          state.order_queue.append(order)
        else:
          print('Ignore order id {} as it is currently being printed.'.format(order['id']))

      time.sleep(constants.polling_interval)

  except ServiceExit as e:
    printer_thread.stop()

# Main call
if __name__ == '__main__':
  main()
