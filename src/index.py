#!/usr/bin/env python3

import time, signal, requests
import state, constants
from printer import Printer_Thread

class ServiceExit(Exception):
    """
    Custom exception which is used to trigger the clean exit
    of all running threads and the main program.
    """
    pass

def shutdown_handler(signum, frame):
  """ Raise an exception to gracefully end the process """
  print('Caught signal {}'.format(signum))
  raise ServiceExit

def service_complete_order(order_id):
  """ Mark the given order id as completed """
  print('Mark order {} as completed.'.format(order_id))

  try:
    response = requests.request(
      'PUT',
      constants.service_root + '/api/v1/orders/' + str(order_id),
      auth=constants.service_auth,
      json={ 'state': 'Completed' })

    return response.status_code == 200

  except Exception as err:
    print('Marking orders failed: {}'.format(str(err)))
    return False

def service_fetch_pending_orders(store_id):
  """ Fetch pending orders for the given store id """
  try:
    response = requests.request(
      'GET',
      constants.service_root + '/api/v1/orders?state=Pending&storeId=' + str(store_id),
      auth=constants.service_auth)

    if response.status_code == 200:
      return response.json()

  except Exception as err:
    print('Fetching pending orders failed: {}'.format(str(err)))

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
      while state.completion_index < state.printer_index:
        if service_complete_order(state.order_queue[state.completion_index]['id']):
          state.completion_index += 1
        else:
          # Try again in next polling tick
          break

      # Check for new orders
      orders = service_fetch_pending_orders(constants.store_id)

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
