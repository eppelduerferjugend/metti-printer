
import threading, time
import state
from escpos import printer

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

    # Loop through the job queue until the stop flag is raised
    while not self.stop_flag.is_set():
      if state.printer_index < len(state.job_queue):

        # Retrieve next job from queue
        job = state.job_queue[state.printer_index]

        try:
          # Try to render and print job
          print('[Printer] Rendering job id {}.'.format(job['id']))
          receipt = self.render_job(job)

          print('[Printer] Printing job id {}.'.format(job['id']))
          self.printer._raw(receipt)

          # Printing cooldown to prevent jibberish
          time.sleep(1)

          # Mark job as completed
          state.printer_index += 1

        except Exception as err:
          # Wait after error (printer unavailable, paper empty, etc)
          print('[Printer] Error while printing: {}'.format(str(err)))
          time.sleep(1)

      else:
        # Loop until an job is available
        time.sleep(1)
        continue

  def render_job(self, job):
    """ Prepare a job on a dummy printer """

    p = printer.Dummy(profile=self.profile)

    # Header image
    p.set(align='center')
    p.image('assets/header.png')
    p.text('\n')

    # Content
    p.set(align='left')
    p.text(job['document']['text'])
    p.text('\n')

    # Cut here
    p.cut()

    return p.output

  def stop(self):
    print('[Printer] Stopping printer thread.')
    self.stop_flag.set()
