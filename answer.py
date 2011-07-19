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
#include <pjsua-lib/pjsua.h>
#include <pjsua-lib/pjsua_internal.h>
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

    """ Initialize Memory based recorder """

    conversation = numpy.zeros ( 14745600, dtype=numpy.uint16 ) # 15m @ 16khz
    self.conversation = conversation


    mcode = """
pj_caching_pool cp;
pjmedia_endpt *med_endpt;
pj_pool_t *pool;
pjmedia_port *mem_port;
pjsua_conf_port_id port;

/*
create bridge, attach memory device to it. Yes, this means we don't use
the conference bridge created just for us. 

Cleanup: Delete conference device, delete pool. 

pj_status_t pjmedia_conf_create   (   pool,
    16, 16000, 1, 160, 16,
    PJMEDIA_CONF_SMALL_FILTER | PJMEDIA_CONF_NO_MIC ,
    pjmedia_conf **   p_conf   
  )   


*/


pj_caching_pool_init(&cp, &pj_pool_factory_default_policy, 0);
if ( pjmedia_endpt_create(&cp.factory, NULL, 1, &med_endpt) != PJ_SUCCESS )
  return py::object(-1);

pool = pj_pool_create( &cp.factory, "mrec", 16384, 16384, NULL  );
if (pjmedia_mem_capture_create(pool, conversation, 14745600*2, 8000, 1, 80, 16, 0, &mem_port) != PJ_SUCCESS)
  return py::object(-1);

if (pjsua_conf_add_port( pool, mem_port, &port ) != PJ_SUCCESS )
  return py::object(-1);

return py::object(port);
"""

    try: 
      poo = pj.auto_lock()
      self.recorder = scipy.weave.inline(mcode, ['conversation'],
                       support_code=support_code, 
                       libraries=libraries, library_dirs=library_dirs, 
                       extra_link_args=["-fPIC"] ) 
      poo = None
    except Exception, e:
      print "pjmedia_mem_capture_create error", e

    print "recorder:", self.recorder

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
        pj.conf_connect(call_slot, 0)
        pj.conf_connect(0 , call_slot)
        pj.conf_connect(call_slot, self.recorder)

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

def pj_sleep():
  code=""" pj_thread_sleep(10); """
  scipy.weave.inline(code, support_code=support_code, libraries=libraries,
                     library_dirs=library_dirs, extra_link_args=["-fPIC"])

def get_cap_pos( recorder ):
  code=""" return pjmedia_mem_capture_get_size   ( port ); """   
  return scipy.weave.inline(code, recorder, support_code=support_code,
                     libraries=libraries,
                     library_dirs=library_dirs, extra_link_args=["-fPIC"])

try:
  lib.init(log_cfg=pjsua.LogConfig(level=0, callback=log_cb), media_cfg=mediaConf)
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
    pj_sleep()
    if incomming_calls:
      call_to_answer=incomming_calls.pop()
      pj_sleep()
      call_to_answer.answer()
      active_calls.append(call_to_answer)
    if active_calls:
      for call in active_calls:
        pos = get_cap_pos( ['call.recorder'] )
        last_pos = getattr( call, 'last_pos', 0 )
        if pos-last_pos < 512:
          continue
        if not hasattr( call, 'tones'  ): 
          call.tones = []

        print "meow:", pos, last_pos
        last_pos=pos

        fft_vals = call.conversation[pos-512:pos]
        tone = numpy.fft.fft(fft_vals)
        call.tones.append(tone)

        freq = []

        freq.append( tone[44] + tone[45] ) 
        freq.append( tone[49] + tone[50] ) 
        freq.append( tone[54] + tone[55] )
        freq.append( tone[60] + tone[61] )
        freq.append( tone[77] + tone[78] )
        freq.append( tone[85] + tone[86] )
        freq.append( tone[94] + tone[95] )
        freq.append( tone[104] + tone[105] )

        print freq

        # 5, 5, 6, 7, 8, 9, 10


        # DO FFT
        # Look at the tones, do they match? Save the match, otherwise
        # write -1 in tones. 

        # Check the tones history. Do we have a continuous tone, then 
        # save it. 

        """
        8000/512
        15.62500000000000000000
        a=15.625
        697/a
        44.60800000000000000000
        770/a
        49.28000000000000000000
        852/a
        54.52800000000000000000
        941/a
        60.22400000000000000000
        1209/a
        77.37600000000000000000
        1336/a
        85.50400000000000000000
        1477/a
        94.52800000000000000000
        1633/a
        104.51200000000000000000
        """
    

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

