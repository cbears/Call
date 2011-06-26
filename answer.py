import sys
import pjsua
import time
import os


current_call = None

# Logging callback
def log_cb(level, str, len):
  print str,


# Callback to receive events from account
class answerPhoneCB(pjsua.AccountCallback):

  def __init__(self, account=None):
    pjsua.AccountCallback.__init__(self, account)

  # Notification on incoming call
  def on_incoming_call(self, call):
    print "Got a connection from: ", call.info().remote_uri

    current_call = call
    call_cb = AnswerLoopCB(current_call)
    current_call.set_callback(call_cb)
    current_call.answer(200) # Answer call


    
# Callback to receive events from Call
class AnswerLoopCB(pjsua.CallCallback):

  def __init__(self, call=None):
    pjsua.CallCallback.__init__(self, call)
    self.r=None
    self.r2=None
    self.pj=None

  def on_state(self):
    global current_call
    print "Call:", self.call.info().remote_uri, self.call.info().state_text, current_call, self.call.info().call_slot
    
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
    self.curcall = current_call
    print "Call started: ", self.time
    pj = pjsua.Lib.instance()
    self.pj = pj
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
      print "Finished ACTIVE state", call_slot
    else:
      print "CHANGED STATE: ", self.call.info().media_state, call_slot


import pdb

def handler(type, value, tb):
  global current_call
  #pdb.pm()
  if current_call:
    print "Hanging up current call... "
    current_call.hangup()
    time.sleep(1)
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
mediaConf.clock_rate = 22050
mediaConf.channel_count=1
mediaConf.snd_auto_close_time=900

try:
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

