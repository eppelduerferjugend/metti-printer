
import threading, time, requests, hashlib, os
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

    # Print each action
    for action in job['document']['actions']:
      if action['type'] == 'text':
        self.render_text(p, action)
      elif action['type'] == 'cut':
        self.render_cut(p, action)
      elif action['type'] == 'image':
        self.render_image(p, action)

    return p.output

  def render_text(self, p, text_action):
    p.set(align='left')
    p.text(text_action['text'])

  def render_cut(self, p, cut_action):
    p.cut()

  def render_image(self, p, image_action):
    image_url = image_action['imageUrl'].encode('utf-8')

    # Create local image path based on a hash of the image url
    image_url_hash = hashlib.sha1(image_url).hexdigest()
    local_image_path = os.path.join('tmp', image_url_hash)

    # Download image, if necessary
    if not os.path.exists(local_image_path):
      try:
        image_response = requests.get(image_url)
        if image_response.status_code != 200:
          raise Exception('Received unexpected HTTP status code {}'.format(str(image_response.status_code)))
        if not os.path.exists('tmp'):
          os.makedirs('tmp')
        with open(local_image_path, 'wb') as image_file:
          image_file.write(image_response.content)
      except Exception as err:
        print('Rendering image action failed: {}'.format(str(err)))
        # Skip printing the image, if it cannot be accessed
        return

    # Print image
    p.image(local_image_path, center=True)

  def stop(self):
    print('[Printer] Stopping printer thread.')
    self.stop_flag.set()
