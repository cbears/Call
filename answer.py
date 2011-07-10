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


# Callback to receive events from account
class answerPhoneCB(pjsua.AccountCallback):

  def __init__(self, account=None):
    pjsua.AccountCallback.__init__(self, account)

  # Notification on incoming call
  def on_incoming_call(self, call):
    print "Got a connection from: ", call.info().remote_uri, call

    call_cb = AnswerLoopCB( call )
    call.set_callback(call_cb)
    call.answer() # Answer call




    
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
      print "Call duration: ", time.time() - self.time
      if self.pj:
        self.pj.recorder_destroy(self.r)
        self.pj.recorder_destroy(self.r2)
        self.pj = None
        print "Disconnected", self.call.info().conf_slot
        

  # Notification when call's media state has changed.
  def on_media_state(self):
    self.time = time.time()
    print "Call started: ", self.time
    pj = pjsua.Lib.instance()
    self.pj = pj
    self.counter=0
    call_slot = self.call.info().conf_slot

    """ Initialize Memory based recorder """

    conversation = numpy.zeros ( 14745600, dtype=numpy.uint16 ) # 15m @ 16khz

    mcode = """
pj_caching_pool cp;
pjmedia_endpt *med_endpt;
pj_pool_t *pool;
pjmedia_port *mem_port;
int port;


pj_caching_pool_init(&cp, &pj_pool_factory_default_policy, 0);
if ( pjmedia_endpt_create(&cp.factory, NULL, 1, &med_endpt) != PJ_SUCCESS )
  return py::object(-1);

pool = pj_pool_create( &cp.factory, "mrec", 4000, 4000, NULL  );
port = pjmedia_mem_capture_create  (   pool, conversation, 14745600*2, 8000, 1, 80, 16, 0, &mem_port );

return py::object(port);
"""

    try: 
      scipy.weave.inline(mcode, ['conversation'], support_code=support_code, 
                       libraries=libraries, library_dirs=library_dirs, 
                       extra_link_args=["-fPIC"] ) 
    except Exception, e:
      print "pjmedia_mem_capture_create error", e

    if self.call.info().media_state == pjsua.MediaState.ACTIVE:
      self.counter+=1

      hello=-1
      try: 
        hello= pj.create_player("/home/bear/hello.wav", False)
        print "Created hello player", hello
      except Exception, e:
        print "Error playing greeting", e

      recorder=-1
      try:
        recorder = pj.create_recorder("/tmp/conversation%d-%d.wav" % 
          (call_slot, self.counter))
        recorder2 = pj.create_recorder("/tmp/conver%d-%d.wav" % 
          (call_slot, self.counter))
        self.r = recorder
        self.r2 = recorder2
      except Exception, e:
        print "Error recording Conversation"
        
      try: 
        if hello != -1:
          pj.conf_connect( pj.player_get_slot(hello), call_slot )
        pj.conf_connect(call_slot, 0)
        pj.conf_connect(0 , call_slot)

        if recorder != -1:
          pj.conf_connect( call_slot, pj.recorder_get_slot(recorder))
          pj.conf_connect( 0, pj.recorder_get_slot(recorder2))
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
#mediaConf.snd_clock_rate = 44100
#mediaConf.clock_rate = 22050
#mediaConf.channel_count=1
#mediaConf.snd_auto_close_time=900
mediaConf.enable_ice=1

try:
  code=""" pj_thread_sleep(1000); """
  scipy.weave.inline(code, support_code=support_code, libraries=libraries,
                     library_dirs=library_dirs, extra_link_args=["-fPIC"])
  lib.init(log_cfg = pjsua.LogConfig(level=0, callback=log_cb), media_cfg = mediaConf)
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
    time.sleep(1)
    

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

