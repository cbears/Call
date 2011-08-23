import sys
import pjsua
import time
import os

import scipy
import scipy.weave
import numpy

# Change these values such that they match your installation of pjsua. You
# probably will need to recompile PJSUA with -fPIC, and you will probably
# want to grab the correct values form a working C Makefile
support_code = """ 
#include <pjlib.h>
#include <pjmedia.h>
"""
libraries="""pjsua-x86_64-unknown-linux-gnu pjsip-ua-x86_64-unknown-linux-gnu pjsip-simple-x86_64-unknown-linux-gnu pjsip-x86_64-unknown-linux-gnu pjmedia-codec-x86_64-unknown-linux-gnu pjmedia-x86_64-unknown-linux-gnu pjmedia-audiodev-x86_64-unknown-linux-gnu pjnath-x86_64-unknown-linux-gnu pjlib-util-x86_64-unknown-linux-gnu resample-x86_64-unknown-linux-gnu milenage-x86_64-unknown-linux-gnu srtp-x86_64-unknown-linux-gnu gsmcodec-x86_64-unknown-linux-gnu speex-x86_64-unknown-linux-gnu ilbccodec-x86_64-unknown-linux-gnu g7221codec-x86_64-unknown-linux-gnu portaudio-x86_64-unknown-linux-gnu  pj-x86_64-unknown-linux-gnu m uuid nsl rt pthread  asound crypto ssl""".split()
library_dirs="""/home/bear/pjproject-1.10/pjlib/lib /home/bear/pjproject-1.10/pjlib-util/lib /home/bear/pjproject-1.10/pjnath/lib /home/bear/pjproject-1.10/pjmedia/lib /home/bear/pjproject-1.10/pjsip/lib /home/bear/pjproject-1.10/third_party/lib""".split()


# Logging callback
def log_cb(level, str, len):
  print str,

incomming_calls = []
active_calls    = []

# Callback to receive events from account
class answerPhoneCB(pjsua.AccountCallback):

  def __init__(self, account=None):
    pjsua.AccountCallback.__init__(self, account)

  # Notification on incoming call
  def on_incoming_call(self, call):
    global incomming_calls
    print "Got a connection from: ", call.info().remote_uri, call

    call_cb = AnswerLoopCB( call )
    call.set_callback(call_cb)
    incomming_calls.append(call)
    
# Callback to receive events from Call
class AnswerLoopCB(pjsua.CallCallback):

  def __init__(self, call=None):
    pjsua.CallCallback.__init__(self, call)
    self.curcall = call
    self.r=None
    self.r2=None
    self.pj=None

  def on_state(self):
    print "Call: URI=%s STATE=%s (%s)" % ( self.call.info().remote_uri, 
      self.call.info().state_text, self.curcall )
    
    if self.call.info().state == pjsua.CallState.DISCONNECTED:
      if hasattr(self, "time"):
        print "Call duration: ", time.time() - self.time
      print "Disconnected", self.call.info().conf_slot
        

  # Notification when call's media state has changed.
  def on_media_state(self):
    self.time = time.time()
    print "Call started: ", self.time
    pj = pjsua.Lib.instance()
    self.pj = 0
    self.counter=0
    call_slot = self.call.info().conf_slot
    if self.call.info().media_state == pjsua.MediaState.ACTIVE:
      self.counter+=1

      hello=-1
      try: 
        hello= pj.create_player("/home/bear/hello.wav", False)
        print "Created hello player", hello
      except Exception, e:
        print "Error playing greeting", e

      try: 
        if hello != -1:
          pj.conf_connect( pj.player_get_slot(hello), call_slot )
          print "Connected hello player"
        pj.conf_connect(call_slot, 0)
        # pj.conf_connect(0 , call_slot)

      except Exception, e:
        print "An error occured.", e
      print "Finished ACTIVE state", self.curcall, call_slot
    else:
      print "CHANGED STATE: ", self.call.info().media_state, self.curcall, call_slot


import pdb

def handler(type, value, tb):
  #pdb.pm()
  lib.destroy()
  sys.exit(1)

params = os.getenv("SIPHOST"), os.getenv("SIPUSER"), os.getenv("SIPPASS")

for i in params:
  if not i:
    print "Must specify SIPHOST, SIPUSER, & SIPPASS", params
    sys.exit(1)

lib = pjsua.Lib()

mediaConf = pjsua.MediaConfig()
mediaConf.snd_clock_rate = 44100
#mediaConf.clock_rate = 22050
#mediaConf.channel_count=1
#mediaConf.snd_auto_close_time=900
#mediaConf.enable_ice=1

try:
  code=""" pj_thread_sleep(10); """
  cap_size=""" return pjmedia_mem_capture_get_size   ( port ); """   
  lib.init(log_cfg = pjsua.LogConfig(level=3, callback=log_cb), media_cfg = mediaConf)
  transport = lib.create_transport(pjsua.TransportType.UDP, pjsua.TransportConfig(0))
  
  # Start the library
  lib.start()

  sys.excepthook = handler

  print "Using", params

  acc = lib.create_account(pjsua.AccountConfig( *params ), 
                           True, cb=answerPhoneCB())

  my_sip_uri = "sip:" + transport.info().host +":"+ str(transport.info().port)

  # Menu loop
  while True:
    if incomming_calls:
      call_to_answer=incomming_calls.pop()
      call_to_answer.answer()
      active_calls.append(call_to_answer)
    

  # Shutdown the library
  transport = None
  acc.delete()
  acc = None
  lib.destroy()
  lib = None

except pjsua.Error, e:
  print "Exception: " + str(e)
  lib.destroy()
  lib = None
except Exception, e:
  print "Non pjsua error", e

