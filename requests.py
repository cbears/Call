import random
import eventlet
from eventlet.green import socket

sysrand = random.SystemRandom()

"""
  ha1 = md5("username:realm:password");
  ha2 = md5("method:digestURI");
  response = md5("%s:nonce:%s" % (ha1, ha2) )
"""

sequence_number=0;
def seqNo():
  global sequence_number;
  sn=sequence_number=sequence_number+1
  return sn

import hashlib
ha1 = hashlib.md5("1302955e0:sipgate.com:SSYCQZ");
ha2 = hashlib.md5("REGISTER:sip:sipgate.com")
print ha1.hexdigest()
print ha2.hexdigest()
response = hashlib.md5("%s:4e4191eca7efe80b4bf007979db1a5dbc18fff36:%s" %(ha1.hexdigest(), ha2.hexdigest()) )
print response.hexdigest()

def randStr( digits=31, symb=61 ):
  randString = []
  for j in xrange ( 0, digits):
    k = sysrand.randint ( 0, symb ) 
    if k < 10:
      k += 0x30
    elif k < 36: 
      k += 0x41 - 10
    else:
      k += 0x61 - 36
    randString.append( chr( k ) ) 
  return "".join( randString )

class CallError(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

HOSTNAME = ""


class register():
  """ 
    This class registers a connection with a SIP provider. 

    It's default is to block until the registration is successful. An
    exception is generated should registration fail.

  """
  def handleIncomming(self):
    self.sock.recv(65536);
    pass

 def __init__(self, username, password, gw, hostname=""):
    global HOSTNAME

    self.sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM, 0 )
    self.sock.bind(('0.0.0.0',0))

    self.un = username
    self.pw = password
    self.gw = gw

    if (!hostname) 
      if (!HOSTNAME)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('google.com', 0))
        HOSTNAME = s.getsockname()[0]
      self.hn = HOSTNAME
    else
      self.hn = hostname

    self.seq = seqNo()
    self.callId = "%s-%d" % ( randStr(), seqNo() )
    self.tag = "%s-%d" % ( randStr(), seqNo() )
    self.branch = "%s-%d" % ( randStr(), seqNo() )
    self.port = self.sock.getsockname()[1]
    eventlet.greenthread.spawn(self.handleIncomming)
    raise CallError("Something something")

  def toDict():
    return dict((name, getattr(self, name)) for name in dir(self)) 

  def gen_request(  seq=seqNo(),
    branch="%s-%d" % (randStr(), seqNo()), hn="10.0.150.8", port=34990,
    tag="%s-%d" % (randStr(), seqNo()), callId="%s-%d" % (randStr(), seqNo())  ):
    return """REGISTER sip:%(gw)s SIP/2.0
Via: SIP/2.0/UDP %(hn)s:%(port)s;branch=%(branch)s
Route: <sip:%(gw)s;lr>
Max-Forwards: 70
From: <sip:%(un)s@%(gw)s>;tag=%(tag)s
To: <sip:%(un)s@%(gw)s>
Call-ID: %(callId)s
CSeq: %(seq)s REGISTER
User-Agent: pysip bear
Contact: <sip:%(un)s@%(hn)s:%(port)s;ob>
Expires: 60
Allow: PRACK, INVITE, ACK, BYE, CANCEL, UPDATE, SUBSCRIBE, NOTIFY, REFER, MESSAGE, OPTIONS
Content-Length:  0
""" % self.toDict()

 


 

print gen_request()

