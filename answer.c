#include <pjsua-lib/pjsua.h>

static void answer_call(pjsua_acc_id acc_id, pjsua_call_id call_id,
           pjsip_rx_data *rdata) {
  pjsua_call_info ci;
  pjsua_call_get_info(call_id, &ci);
  printf("Got a call from %s (%d)\n", ci.remote_info.ptr, call_id);

  pjsua_call_answer(call_id, 200, NULL, NULL);
}

static void call_state(pjsua_call_id call_id, pjsip_event *e) {
  pjsua_call_info ci;
  pjsua_call_get_info(call_id, &ci);
  printf("New status, %s (%d)\n", ci.state_text.ptr, call_id);
}

static void media_change(pjsua_call_id call_id) {
  pjsua_call_info ci;
  if (ci.media_status == PJSUA_CALL_MEDIA_ACTIVE) {
      pjsua_conf_connect(ci.conf_slot, 0);
      pjsua_conf_connect(0, ci.conf_slot);
  }
}



int main(int argc, char** argv) {
  pjsua_config cfg;
  pjsua_logging_config log_cfg;
  pjsua_acc_id acc_id;
  pjsua_acc_config acc;
  pjsua_transport_config trans;


  char* siphost = getenv("SIPHOST");
  char* sipuser = getenv("SIPUSER");
  char* sippass = getenv("SIPPASS");

  if ( !siphost || !sipuser || !sippass ) {
    printf("Must supply SIPHOST, SIPUSER, & SIPPASS\n");
    return -1;
  } else {
    printf("SIPHOST='%s' SIPUSER='%s' SIPPASS='%s'\n", 
             siphost, sipuser, sippass );
  }

  if (pjsua_create() != PJ_SUCCESS) {
    printf("Error creating pjsua library\n");
    return 2;
  }
  pjsua_config_default(&cfg);
  cfg.cb.on_incoming_call = &answer_call;
  cfg.cb.on_call_media_state = &media_change;
  cfg.cb.on_call_state = &call_state;

  pjsua_logging_config_default(&log_cfg);
  log_cfg.console_level = 4;

  if ( pjsua_init(&cfg, &log_cfg, NULL) != PJ_SUCCESS ) {
    printf("Error initializing pjsua library\n");
    return 1;
  }

  pjsua_transport_config_default(&trans);
  trans.port = 0;
  if (pjsua_transport_create(PJSIP_TRANSPORT_UDP, &trans, NULL) != PJ_SUCCESS){
    printf("Error initializing transport layer\n");
    return 3;
  }

  if ( pjsua_start() != PJ_SUCCESS ) {
    printf("Error starting pjsua\n");
    return 4;
  }

  pjsua_acc_config_default(&acc);

  char buf[512], buf2[512];
  snprintf(buf, 512, "sip:%s@%s", sipuser, siphost );
  acc.id = pj_str(buf);
  snprintf(buf2, 512, "sip:%s", siphost);
  acc.reg_uri = pj_str(buf2);
  acc.cred_count = 1;
  acc.cred_info[0].realm = pj_str(siphost);
  acc.cred_info[0].scheme = pj_str("digest");
  acc.cred_info[0].username = pj_str(sipuser);
  acc.cred_info[0].data_type = PJSIP_CRED_DATA_PLAIN_PASSWD;
  acc.cred_info[0].data = pj_str(sippass);

  if (pjsua_acc_add(&acc, PJ_TRUE, &acc_id) != PJ_SUCCESS) {
    printf("Error connecting to SIP Account. Check Credentials?\n");
    return (9);
  }
  
  getchar();

  pjsua_destroy();
  

}
