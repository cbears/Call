import sys
import pjsua
import time

current_call = None

# Logging callback
def log_cb(level, str, len):
  print str,


# Callback to receive events from account
class MyAccountCallback(pjsua.AccountCallback):

  def __init__(self, account=None):
    pjsua.AccountCallback.__init__(self, account)

  # Notification on incoming call
  def on_incoming_call(self, call):
    global current_call 
    if current_call:
      call.answer(486, "Busy")
      return
      
    print "Got a connection from: ", call.info().remote_uri

    current_call = call

    call_cb = MyCallCallback(current_call)
    current_call.set_callback(call_cb)

    current_call.answer(200) # Answer call


    
# Callback to receive events from Call
class MyCallCallback(pjsua.CallCallback):

  def __init__(self, call=None):
    pjsua.CallCallback.__init__(self, call)

  # Notification when call state has changed
  def on_state(self):
    global current_call
    print "Call with", self.call.info().remote_uri,
    print "is", self.call.info().state_text,
    print "last code =", self.call.info().last_code, 
    print "(" + self.call.info().last_reason + ")"
    
    if self.call.info().state == pjsua.CallState.DISCONNECTED:
      current_call = None
      print 'Current call is', current_call

  # Notification when call's media state has changed.
  def on_media_state(self):
    if self.call.info().media_state == pjsua.MediaState.ACTIVE:
      # Connect the call to sound device
      call_slot = self.call.info().conf_slot
      #PJMEDIA_FILE_NO_LOOP=1;
      hello = -1
      try: 
        hello = pjsua.Lib.instance().create_player("/home/bear/hello.wav", True)
        print "Created hello player", hello, hell2
      except Exception, e:
        print "Error playing greeting", e
        
      try: 
        if hello != -1:
          pjsua.Lib.instance().conf_connect( 
            pjsua.Lib.instance().player_get_slot(hello), call_slot )
        pjsua.Lib.instance().conf_connect(call_slot, 0)
        pjsua.Lib.instance().conf_connect(0 , call_slot)
      except Exception, e:
        print "An error occured.", e
      print "Media is now active"
    else:
      print "Media is inactive"

# Create library instance
lib = pjsua.Lib()

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

try:
  # Init library with default config and some customized
  # logging config.
  lib.init(log_cfg = pjsua.LogConfig(level=3, callback=log_cb))

  # Create UDP transport which listens to any available port
  transport = lib.create_transport(pjsua.TransportType.UDP, pjsua.TransportConfig(0))
  print "\nListening on", transport.info().host, 
  print "port", transport.info().port, "\n"
  
  # Start the library
  lib.start()

  sys.excepthook = handler

  # Create local account
  acc = lib.create_account(pjsua.AccountConfig("sipgate.com", "1302955e0", "SSYCQZ"), True, cb=MyAccountCallback())

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

