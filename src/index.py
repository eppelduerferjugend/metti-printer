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

def service_fetch_pending_jobs(printer_name):
  """ Fetch pending printer jobs for the given printer name """
  try:
    response = requests.request(
      'GET',
      constants.service_root + '/printers/' + printer_name + '/jobs',
      headers={"Authorization": "Bearer " + constants.service_auth_token}
    )

    if response.status_code == 200:
      return response.json()

  except Exception as err:
    print('Fetching pending jobs failed: {}'.format(str(err)))

  return []

def service_complete_job(printer_name, job_id):
  """ Mark the given job id as completed """
  print('Mark job {} as completed.'.format(job_id))

  try:
    response = requests.request(
      'PUT',
      constants.service_root + '/printers/' + printer_name + '/jobs/' + str(job_id),
      headers={"Authorization": "Bearer " + constants.service_auth_token},
      json={ 'state': 'completed' })
    if response.status_code != 200:
      raise Exception("Non ok status code received: " + str(response.status_code))
    return response.status_code == 200

  except Exception as err:
    print('Marking job as completed failed: {}'.format(str(err)))
    return False

def main():
  # Register shutdown handlers
  signal.signal(signal.SIGTERM, shutdown_handler)
  signal.signal(signal.SIGINT, shutdown_handler)

  # Initial state
  state.job_queue = []
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
      # Mark printed jobs as completed
      while state.completion_index < state.printer_index:
        if service_complete_job(constants.printer_name, state.job_queue[state.completion_index]['id']):
          state.completion_index += 1
        else:
          # Try again in next polling tick
          break

      # Retrieve jobs that are in progress
      active_jobs = state.job_queue[state.completion_index:]
      active_job_ids = list(map(lambda job: job['id'], active_jobs))

      # Check for new jobs
      jobs = service_fetch_pending_jobs(constants.printer_name)

      for job in jobs:
        # Append job to queue if it is not in the print queue
        # If the job has been completed and reopened in the past
        # it gets added again to the printing queue
        if not job['id'] in active_job_ids:
          print('Found new incomplete job id {}.'.format(job['id']))
          state.job_queue.append(job)
        else:
          print('Ignore job id {} as it is currently being printed.'.format(job['id']))

      time.sleep(constants.polling_interval)

  except ServiceExit as e:
    printer_thread.stop()

# Main call
if __name__ == '__main__':
  main()
