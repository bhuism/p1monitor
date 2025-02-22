####################################################################
# shared lib for processing the p1 port telegram                   #
# this lib is used for functions that can be reused by serial      #
# or network devices that can deliver the P1 telegram data         #
####################################################################

import apiconst
import const
import datetime
import inspect
import json
import shutil
import string
import os
import systemid
import time
import util
import process_lib

###########################################################
# email notification when there is no data seen on the P1 #
# port                                                    #
###########################################################
class P1PortDataNotification():
    
    def __init__( self, statusdb=None, configdb=None, flog=None ):
        self.statusdb               = statusdb
        self.configdb               = configdb
        self.did_send_data          = False
        self.flog                   = flog

    def run( self ):

        try:
            _id, on, _label = self.configdb.strget( 175, self.flog )
            if int(on) != 1:
                self.flog.debug( __class__.__name__ + ": email voor controle op P1 data staat uit, geen actie.")  
                return 
        except:
            return

        try:

            # construct subject.
            _id, subject, _label = self.configdb.strget( 69, self.flog )
            if len( subject) < 1:
                subject =  const.DEFAULT_EMAIL_NOTIFICATION

            # get time difference
            try:
                _id, utc_str, _description, _index = self.statusdb.strget( 87, self.flog )
                delta_time = abs( util.getUtcTime() - int( utc_str ) )
            except:
                self.flog.debug( __class__.__name__  + ": tijd is niet gezet, er wordt niets uitgevoerd.")
                return

            # make date time string
            t = time.localtime()
            timestring = "%04d-%02d-%02d %02d:%02d:%02d"% ( t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec )
           
            # 1 is ok, 0 is not ok
            _id, p1_data_is_ok, _label, _security = self.statusdb.strget( 123, self.flog ) 

            self.flog.debug( __class__.__name__ + ": p1_data_is_ok = " + p1_data_is_ok + " self.did_send_data = " +  str( self.did_send_data ) )

            # P1 data is NOT ok
            if int ( p1_data_is_ok ) == 0 and self.did_send_data == False:
                self.flog.debug( __class__.__name__ + ": P1 data ontbreekt. " )
                subject_str = ' -subject "' + subject + ' (slimme meter data niet ontvangen)."'
                messagetext = ' -msgtext "Data uit de slimme meter komt niet meer binnen.\n' +  timestring + ' Laatste slimme meter telegram ' + str( delta_time ) + ' seconden geleden ontvangen."'
                messagehtml = ' -msghtml "<p>Data uit de slimme meter komt niet meer binnen.</p><p>' + timestring + ': Laatste slimme meter telegram <b>' + str(delta_time)+'</b> seconden geleden ontvangen.</p>"'
                #if os.system( '/p1mon/scripts/P1SmtpCopy.py ' + subject_str + messagetext + messagehtml + ' >/dev/null 2>&1' ) > 0:
                #    self.flog.error( inspect.stack()[0][3]+" email notificatie P1 data ontbreekt is gefaald." )
                #else:
                #    self.flog.warning(inspect.stack()[0][3]+" email verstuurd dat er geen P1 data wordt ontvangen in de afgelopen " + str( delta_time ) + " seconden." )
                #    self.did_send_data = True

                #cmd = "/p1mon/scripts/pythonlaunch.sh P1SmtpCopy.py " + subject_str + messagetext + messagehtml + ' >/dev/null 2>&1' #180 upgrade
                cmd = "/p1mon/scripts/pythonlaunch.sh P1SmtpCopy.py '" + subject_str + messagetext + messagehtml + "' >/dev/null 2>&1"

                r = process_lib.run_process( 
                    cms_str = cmd,
                    use_shell=True,
                    give_return_value=True,
                    flog=self.flog 
                    )
                if ( r[2] ) > 0:
                     self.flog.error( __class__.__name__ + " email notificatie P1 data ontbreekt is gefaald." )
                else:
                    self.flog.warning( __class__.__name__ + " email verstuurd dat er geen P1 data wordt ontvangen in de afgelopen " + str( delta_time ) + " seconden." )
                    self.did_send_data = True

            # P1 data is OK
            if int( p1_data_is_ok ) == 1 and self.did_send_data == True:
                self.flog.debug( __class__.__name__ + ": P1 data is ok of weer binnengekomen" )
                subject_str = ' -subject "' + subject + ' (slimme meter data ontvangen.)."'
                messagetext = ' -msgtext "Data uit de slimme meter komt binnen.\n' + timestring + ' Laatste slimme meter telegram ' + str( delta_time )+' seconden geleden ontvangen."'
                messagehtml = ' -msghtml "<p>Data uit de slimme meter komt weer binnen.</p><p>' + timestring + ': Laatste slimme meter telegram <b>' + str(delta_time) +'</b> seconden geleden ontvangen.</p>"'
                #if os.system( '/p1mon/scripts/P1SmtpCopy.py ' + subject_str + messagetext + messagehtml + ' >/dev/null 2>&1' ) > 0:
                #    self.flog.error( inspect.stack()[0][3]+" email notificatie P1 data werkt weer is gefaald." )
                # else:
                #    self.flog.info( inspect.stack()[0][3]+" P1 data komt weer binnen, email verstuurd." )
                #    self.did_send_data = False
                #cmd = "/p1mon/scripts/pythonlaunch.sh P1SmtpCopy.py " + subject_str + messagetext + messagehtml + ' >/dev/null 2>&1' #180 upgrade
                cmd = "/p1mon/scripts/pythonlaunch.sh P1SmtpCopy.py '" + subject_str + messagetext + messagehtml + "' >/dev/null 2>&1"
                r = process_lib.run_process( 
                    cms_str = cmd,
                    use_shell=True,
                    give_return_value=True,
                    flog=self.flog 
                    )
                if ( r[2] ) > 0:
                    self.flog.error( __class__.__name__ + " email notificatie P1 data werkt weer is gefaald." )
                else:
                    self.flog.info( __class__.__name__ + " P1 data komt weer binnen, email verstuurd." )
                    self.did_send_data = False

        except Exception as e:
            self.flog.error( __class__.__name__ + ": error " + str(e) )


###########################################################
# read the FQDN from the config database and load the     #
# to the data structure *data_set (basic_json)            #
###########################################################
def fqdn_from_config( verbose=False , configdb=None, data_set=None, flog=None):
    try:
        _id, fqdn, _label = configdb.strget( 150, flog )
        data_set[apiconst.JSON_API_FQDN] = fqdn
        if verbose:
            flog.info( inspect.stack()[0][3]+" fqdn ingelezen: " + str(fqdn) )
    except Exception as e:
        flog.warning( inspect.stack()[0][3]+" lezen van FQDN  melding: " + str(e.args[0]) )


###########################################################
# read the values from the P1 telegram and convert them   #
# to the data structure *data_set                         #
###########################################################
def parse_serial_buffer( serialbuffer=None, data_set=None, status=None, phase_db_rec=None, flog=None ):

    tarief_code = 'P' # default value when not set
    timestamp_telegram = None

    #global serial_buffer

    status['gas_present_in_serial_data'] = False
    #write_p1_telegram_to_ram( buffer=serialbuffer, flog=flog ) 

    #flog.debug( inspect.stack()[0][3] + " gas_record_prefix_number = " + str(status['gas_record_prefix_number']) )

    #content = []
    while len(serialbuffer) > 0:
        line = serialbuffer.pop(0)
        #print len(line)
        if len(line) < 1: # we don't do empty lines
            continue
        try:
            buf = line.split('(')
            #print("#### "+str(buf[0]))
            if len(buf) < 2: # verwijder velden die niet interessant zijn
                continue

            if buf[0] == '0-0:96.1.1': # verwijder slimme meter header 
                continue

            if buf[0] == '0-' + str( status['gas_record_prefix_number'] ) + ':24.2.3':
                content = buf[2].split(')')
                content = content[0].split('*')
                data_set['gas_verbr_m3_2421'] = util.cleanDigitStr(content[0])
                status['gas_present_in_serial_data'] = True
            
            if buf[0] == '0-' + str( status['gas_record_prefix_number'] ) + ':24.2.1':
                content = buf[2].split(')')
                content = content[0].split('*')
                data_set['gas_verbr_m3_2421'] = util.cleanDigitStr( content[0] )
                status['gas_present_in_serial_data'] = True

            if buf[0] == '0-' + str( status['gas_record_prefix_number'] ) + ':24.3.0':
                line_tmp = serialbuffer.pop(0)
                buf_tmp =  line_tmp.split('(')
                data_set['gas_verbr_m3_2421'] = util.cleanDigitStr( buf_tmp[1] )
                status['gas_present_in_serial_data'] = True

            elif buf[0] == '1-0:1.8.1':
                content = buf[1].split('*') 
                data_set['verbrk_kwh_181'] = util.cleanDigitStr(content[0])

            elif buf[0] == '1-0:1.8.2':
                content = buf[1].split('*') 
                data_set['verbrk_kwh_182'] = util.cleanDigitStr(content[0])

            elif buf[0] == '1-0:2.8.1':
                content = buf[1].split('*') 
                data_set['gelvr_kwh_281'] = util.cleanDigitStr(content[0])

            elif buf[0] == '1-0:2.8.2':
                content = buf[1].split('*') 
                data_set['gelvr_kwh_282'] = util.cleanDigitStr(content[0])

            elif buf[0] == '1-0:1.7.0':
                content = buf[1].split('*') 
                data_set['act_verbr_kw_170'] = util.cleanDigitStr(content[0])

            elif buf[0] == '1-0:2.7.0':
                content = buf[1].split('*')
                data_set['act_gelvr_kw_270'] = util.cleanDigitStr(content[0])

            elif buf[0] == '0-0:96.14.0':
                content = buf[1].split(')')
                tarief_code=util.cleanDigitStr(content[0])

            elif buf[0] == '1-0:21.7.0':
                content = buf[1].split('*')
                phase_db_rec['consumption_L1_kW'] = util.cleanDigitStr(content[0])

            elif buf[0] == '1-0:41.7.0':
                content = buf[1].split('*')
                phase_db_rec['consumption_L2_kW'] = util.cleanDigitStr(content[0])

            elif buf[0] == '1-0:61.7.0':
                content = buf[1].split('*')
                phase_db_rec['consumption_L3_kW'] = util.cleanDigitStr(content[0])

            elif buf[0] == '1-0:22.7.0':
                content = buf[1].split('*')
                phase_db_rec['production_L1_kW'] = util.cleanDigitStr(content[0])

            elif buf[0] == '1-0:42.7.0':
                content = buf[1].split('*')
                phase_db_rec['production_L2_kW'] = util.cleanDigitStr(content[0])

            elif buf[0] == '1-0:62.7.0':
                content = buf[1].split('*')
                phase_db_rec['production_L3_kW'] = util.cleanDigitStr(content[0])

            elif buf[0] == '1-0:32.7.0':
                content = buf[1].split('*')
                phase_db_rec['L1_V'] = util.cleanDigitStr(content[0])

            elif buf[0] == '1-0:52.7.0':
                content = buf[1].split('*')
                phase_db_rec['L2_V'] = util.cleanDigitStr(content[0])

            elif buf[0] == '1-0:72.7.0':
                content = buf[1].split('*')
                phase_db_rec['L3_V'] = util.cleanDigitStr(content[0])

            elif buf[0] == '1-0:31.7.0':
                content = buf[1].split('*')
                phase_db_rec['L1_A'] = util.cleanDigitStr(content[0])

            elif buf[0] == '1-0:51.7.0':
                content = buf[1].split('*')
                phase_db_rec['L2_A'] = util.cleanDigitStr(content[0])

            elif buf[0] == '1-0:71.7.0':
                content = buf[1].split('*')
                phase_db_rec['L3_A'] = util.cleanDigitStr(content[0])

            elif buf[0] == '0-0:1.0.0':
                #print ( buf[1] )
                content = buf[1].split(')')
                #print ( content )
                timestamp_telegram = util.cleanDigitStr(content[0])

            elif buf[0] == '1-0:1.4.0':
                content = buf[1].split('*')
                data_set['peak_quarter_hour_140'] = util.cleanDigitStr(content[0])
            
            elif buf[0] == '1-0:1.6.0':
                content = buf[1].split('*')
                data_set['peak_month_peak_160_ts'] = util.cleanDigitStr(content[0])
                content = buf[2].split('*')
                data_set['peak_month_peak_160'] = util.cleanDigitStr(content[0])
                #print( data_set['peak_month_peak_160_ts'] )
                #print( data_set['peak_month_peak_160'] )

            # specific codes for large users
            if status['large_consumption_user'] == True:
            
                if buf[0] == '1-0:1.8.0':   # kWh consumed 
                    content = buf[1].split('*') 
                    data_set['lc_180'] = util.cleanDigitStr(content[0])

                elif buf[0] == '1-0:2.8.0': # kWh produced
                    content = buf[1].split('*') 
                    data_set['lc_280'] = util.cleanDigitStr(content[0])

                elif buf[0] == '1-0:90.7.0': # total amps R,S,T (L1,L2,L3)
                    content = buf[1].split('*') 
                    data_set['ls_9070'] = util.cleanDigitStr(content[0])

                elif buf[0] == '1-0:0.9.1':  # time in format hhmmsss
                    content = buf[1].split(')') 
                    data_set['lc_091'] = util.cleanDigitStr(content[0])
                
                elif buf[0] == '1-0:0.9.2': # date in format ddmmyy
                    content = buf[1].split(')') 
                    data_set['lc_092'] = util.cleanDigitStr(content[0])

        except Exception as e:
            flog.error(inspect.stack()[0][3]+": fout in P1 data. Regel="+\
            line+" melding:"+str(e.args[0]))

    if tarief_code == '0002':
        tarief_code = 'P'

    if tarief_code == '0001':
        tarief_code = 'D'

    data_set['tarief_code'] = tarief_code

    if data_set['lc_091'] != const.NOT_SET and data_set['lc_092'] != const.NOT_SET:
        timestamp_telegram = data_set['lc_092'] + data_set['lc_091']

    if timestamp_telegram != None:
        #print ( timestamp )
        #timestamp = timestamp + "10"
        try: # check if this is a valid date.
            p1_time = datetime.datetime.strptime( timestamp_telegram, "%y%m%d%H%M%S" ).timestamp()
            #print ( abs(int(time.time() - p1_time)) )
            status['p1_time_delta'] = str( abs(int(time.time() - p1_time)) )
            #print ("#1",status['p1_time_delta'] )
        except ValueError:
            flog.warning( inspect.stack()[0][3] + " Timestamp van P1 bericht is niet correct (yymmddhhmmss) -> " + str(timestamp_telegram) )

    #print("#1", data_set)

   

    #flog.setLevel( logger.logging.DEBUG )
    # convert the large cosumption values to cosumer code and calculate
    # missing values, where possible
    if status['large_consumption_user'] == True and status['calculate_missing_values'] == True:

        # conversion of consumed kWh
        if data_set['lc_180'] != const.NOT_SET:
            data_set['verbrk_kwh_182'] = data_set['lc_180']
            data_set['verbrk_kwh_181'] = '000000.000'

        # conversion of produced kWh
        if data_set['lc_280'] != const.NOT_SET:
            data_set['gelvr_kwh_282'] = data_set['lc_280']
            data_set['gelvr_kwh_281'] = '000000.000'

        # try to calculate current consumed power (Watt)

        # old way with total AMP's 
        """
        if data_set['act_verbr_kw_170'] == const.NOT_SET:
            # is total amp set and the voltages used that
            if data_set['ls_9070'] != const.NOT_SET:
                v_total = []
                if phase_db_rec['L1_V'] != const.NOT_SET:
                       v_total.append( int(phase_db_rec['L1_V']) )
                if phase_db_rec['L2_V'] != const.NOT_SET:
                       v_total.append( int(phase_db_rec['L2_V']) ) 
                if phase_db_rec['L2_V'] != const.NOT_SET:
                       v_total.append( int(phase_db_rec['L3_V']) )

                data_set['act_verbr_kw_170'] = "{0:06.3f}".format( (float(data_set['ls_9070']) * statistics.mean(v_total))/1000 )
        """

        if data_set['act_verbr_kw_170'] == const.NOT_SET: # fails save if calc fails
            data_set['act_verbr_kw_170'] = "00.000"
        
        if data_set['act_gelvr_kw_270'] == const.NOT_SET:
            data_set['act_gelvr_kw_270'] = "00.000"

        # check if phase Watt values are set, if not try to calculate them
        if phase_db_rec['L1_V'] != const.NOT_SET and phase_db_rec['L1_A'] != const.NOT_SET:
            phase_db_rec['consumption_L1_kW'] = '{0:.3f}'.format(  (float(phase_db_rec['L1_V']) * float(phase_db_rec['L1_A'])) / 1000  )

        if phase_db_rec['L2_V'] != const.NOT_SET and phase_db_rec['L2_A'] != const.NOT_SET:
            phase_db_rec['consumption_L2_kW'] = '{0:.3f}'.format(   float(phase_db_rec['L2_V']) * float(phase_db_rec['L2_A']) / 1000 )

        if phase_db_rec['L3_V'] != const.NOT_SET and phase_db_rec['L3_A'] != const.NOT_SET:
            phase_db_rec['consumption_L3_kW'] = '{0:.3f}'.format( float(phase_db_rec['L3_V']) * float(phase_db_rec['L3_A']) / 1000 )

        # add fase Watt values to total Watt value
        total_watt = 0.0
        if phase_db_rec['consumption_L1_kW'] != const.NOT_SET:
            total_watt += float( phase_db_rec['consumption_L1_kW'] )
        if phase_db_rec['consumption_L2_kW'] != const.NOT_SET:
             total_watt += float( phase_db_rec['consumption_L2_kW'] )
        if phase_db_rec['consumption_L3_kW'] != const.NOT_SET:
             total_watt += float( phase_db_rec['consumption_L3_kW'] )

        data_set['act_verbr_kw_170'] = '{0:06.3f}'.format( total_watt )

    #print( "#2", data_set )
    #print( " ----- ")
    #print ( phase_db_rec )
    #print ( "\n" )

    #sys.exit()

    if status['day_night_mode']  == 1:
        flog.debug( inspect.stack()[0][3] + " Dag en nacht tarief staat op mode 1: Belgie" )
    
        tmp = data_set['verbrk_kwh_181']
        data_set['verbrk_kwh_181'] = data_set['verbrk_kwh_182']
        data_set['verbrk_kwh_182'] = tmp

        tmp = data_set['gelvr_kwh_281']
        data_set['gelvr_kwh_281'] = data_set['gelvr_kwh_282']
        data_set['gelvr_kwh_282'] = tmp

        if tarief_code == 'P': # wisselen van tarief code 00002 is piek in NL maar dal in Belgie.  0001 is dal in NL maar piek in Belgie.
            tarief_code = 'D'
            data_set['tarief_code'] = 'D'
        else: 
            tarief_code = 'P'
            data_set['tarief_code'] = 'P'

    if status['day_night_mode']  == 0: 
        flog.debug( inspect.stack()[0][3] + " Dag en nacht tarief staat op mode 0: Nederland" )

###########################################################
# check if all major fields are valid. If one field fails #
# the function will return. This is changed from version  #
# 1.3.2 and above.                                        #
###########################################################
def record_sanity_check( data_set=None, status=None, flog=None ):

    if status['gas_present_in_serial_data'] == True:
        if data_set['gas_verbr_m3_2421'] == const.NOT_SET:
            flog.warning(inspect.stack()[0][3]+": Gefaald op gas verbruikt (24.2.1), waarde was " + str( data_set['gas_verbr_m3_2421'] ) )
            return False

    if data_set['verbrk_kwh_181'] == const.NOT_SET:
        flog.warning(inspect.stack()[0][3]+": Gefaald op dal/nacht voor verbruikte energie(1.8.1), waarde was "+str( data_set['verbrk_kwh_181'] ) )
        return False

    if data_set['verbrk_kwh_182'] == const.NOT_SET:
        flog.warning(inspect.stack()[0][3]+": Gefaald op piek/dag voor verbruikte energie(1.8.2), waarde was " + str(data_set['verbrk_kwh_182'] ) )
        return False

    if data_set['gelvr_kwh_281'] == const.NOT_SET:
        flog.warning(inspect.stack()[0][3]+": Gefaald op dal/nacht voor geleverde energie(2.8.1), waarde was "+str( data_set['gelvr_kwh_281'] ) )
        return False

    if data_set['gelvr_kwh_282'] == const.NOT_SET:
        flog.warning(inspect.stack()[0][3]+": Gefaald op piek/dag voor geleverde energie(2.8.2), waarde was "+str( data_set['gelvr_kwh_282'] ) )
        return False

    if data_set['act_verbr_kw_170'] == const.NOT_SET:
        flog.warning(inspect.stack()[0][3]+": Gefaald op actueel verbruikt vermogen, waarde was "+str( data_set['act_verbr_kw_170'] ) )
        return False

    if data_set['act_gelvr_kw_270'] == const.NOT_SET:
        flog.warning(inspect.stack()[0][3]+": Gefaald op actueel geleverd vermogen, waarde was "+str( data_set['act_gelvr_kw_270'] ))
        return False

    if status['gas_present_in_serial_data'] == True:
        if len(str( data_set['gas_verbr_m3_2421'] ) ) < 8 or len(str(data_set['gas_verbr_m3_2421'] ) ) > 12:
            flog.warning(inspect.stack()[0][3]+": Gefaald op gas verbruikt (24.2.1) (lengte), waarde was "+str( data_set['gas_verbr_m3_2421'] ) )
            return False

    if len(str( data_set['verbrk_kwh_181'] )) < 9 or len(str( data_set['verbrk_kwh_181'] ) ) > 10:
        flog.warning(inspect.stack()[0][3]+": Gefaald op dal/nacht format (1.8.1) (lengte), waarde was "+str( data_set['verbrk_kwh_181'] ) )
        return False

    if len(str( data_set['verbrk_kwh_182'] )) < 9  or len(str( data_set['verbrk_kwh_182'] )) > 10:
        flog.warning(inspect.stack()[0][3]+": Gefaald op piek/dag format (1.8.2) (lengte), waarde was "+str( data_set['verbrk_kwh_182'] ) )
        return False

    if len(str( data_set['gelvr_kwh_281'] )) < 9  or len(str( data_set['gelvr_kwh_281'] )) > 10:
        flog.warning(inspect.stack()[0][3]+": Gefaald op dal/nacht format (2.8.1) (lengte), waarde was "+str( data_set['gelvr_kwh_281'] ) )
        return False

    if len(str( data_set['gelvr_kwh_282'] )) < 9 or len(str( data_set['gelvr_kwh_282'] )) > 10:
        flog.warning(inspect.stack()[0][3]+": Gefaald op piek/dag format (2.8.2) (lengte), waarde was "+str( data_set['gelvr_kwh_282'] ) )
        return False

    if len(str( data_set['act_verbr_kw_170'] )) < 6 or len(str( data_set['act_verbr_kw_170'] ) ) > 7:
        flog.warning(inspect.stack()[0][3]+": Gefaald op actueel verbruikt vermogen format (1.7.0) (lengte), waarde was "+str( data_set['act_verbr_kw_170']) )
        return False
    
    if len(str( data_set['act_gelvr_kw_270'] )) < 6 or len(str( data_set['act_gelvr_kw_270'] ) ) > 7:
        flog.warning(inspect.stack()[0][3]+": Gefaald op actueel geleverd vermogen format (2.7.0) (lengte), waarde was "+str( data_set['act_gelvr_kw_270'] ) )
        return False

    return True # alle is well :)

#############################################################
# restore data to ram from disk                             #
#############################################################
def disk_restore_from_disk_to_ram(flog=None):
    #os.system("/p1mon/scripts/P1DbCopy.py --allcopy2ram")
    cmd = "/p1mon/scripts/pythonlaunch.sh P1DbCopy.py --allcopy2ram" #180 upgrade
    process_lib.run_process( 
        cms_str = cmd,
        use_shell=True,
        give_return_value=False,
        flog=flog 
    )

#############################################################
# backup data to disk on the mod minute timestamp           #
#############################################################
def backup_data_to_disk_by_timestamp( statusdb=None, flog=None, minute_mod=15 ):

    try:
        if int(util.mkLocalTimeString()[14:16])%minute_mod != 0:
            return # do noting, we are not in the mod range normaly 0,15,30,45 minutes

        file_sec_delta = util.file_delta_timestamp( const.FILE_DB_E_FILENAME ,const.DIR_FILEDISK )
        
        if file_sec_delta > 60  or file_sec_delta == -1:
            #os.system("/p1mon/scripts/P1DbCopy.py --serialcopy2disk --forcecopy")
            cmd = "/p1mon/scripts/pythonlaunch.sh P1DbCopy.py --serialcopy2disk --forcecopy" #180 upgrade
            process_lib.run_process( 
                cms_str = cmd,
                use_shell=True,
                give_return_value=False,
                flog=flog 
            )


            statusdb.timestamp( 41,flog )

    except Exception as e:
        flog.error(inspect.stack()[0][3]+": data back-up fout: "+str(e))

#############################################################
# get setting for P1 telegram mode of large consumers       #
# 0: do not process                                         #
# 1: do process                                             #
#############################################################
def get_large_consumer_mode( status=None ,configdb=None, flog=None ):

    try:
        _id, parameter, _label = configdb.strget( 178, flog )

        if int( parameter ) != status['large_consumption_user']:
            status['large_consumption_user'] = int( parameter )
            if int( parameter ) == 0:
                text = "uit."
            else:
                text = "aan."
            flog.info(inspect.stack()[0][3]+": groot verbruiker mode is " + text )

    except Exception as e:
            flog.error(inspect.stack()[0][3]+": sql error( config )" + str(e))


#############################################################
# get country settings for day and night mode               #
# 0: NL verwerking van E velden                             #
# 1: BE processing of the E fields 181/182 and 281/282      #
# inverted high/low value. 0-0:96.14.0 rate is also changed.#
#############################################################
def get_country_day_night_mode( status=None ,configdb=None, flog=None ):

    try:
        _id, parameter, _label = configdb.strget( 78,flog )

        if int( parameter ) != status['day_night_mode']:
            status['day_night_mode'] = int( parameter )
            flog.info(inspect.stack()[0][3]+": dag nacht mode aangepast met de waarde " + str( status['day_night_mode'] )  + ". Mode 0 is Nederland, Mode 1 is Belgie.")

    except Exception as e:
            flog.error(inspect.stack()[0][3]+": sql error( config )"+str(e))


#############################################################
# This flag determines if missing values must be calculated #
# True means calculate if possible                          #
#############################################################
def get_calculate_missing_values( status=None ,configdb=None, flog=None ):

    try:
        _id, parameter, _label = configdb.strget( 179,flog )

        if int( parameter ) != status['calculate_missing_values']:
            status['calculate_missing_values'] = int( parameter )
            flog.info(inspect.stack()[0][3]+":  berekenen van ontbrekende waarde mode aangepast met de waarde " + str( status['calculate_missing_values'] ) )

    except Exception as e:
            flog.error(inspect.stack()[0][3]+": sql error( config )"+str(e))


#############################################################
#  get the telgram prefix from the datbase                  #
#############################################################
def get_gas_telgram_prefix( status=None ,configdb=None, flog=None ):
    #checkGasTelgramPrefix()
    
    try:
        gas_config_rec = configdb.strget( 38, flog )

        if str( gas_config_rec[1] ) != status['gas_record_prefix_number']:
            status['gas_record_prefix_number'] = str( gas_config_rec[1] )
            flog.info(inspect.stack()[0][3]+": gas telegram records gewijzigd naar " + str( status['gas_record_prefix_number'] ) )
        else:
            flog.debug(inspect.stack()[0][3]+": gas telegram records niet gewijzigd. huidige waarde " + str( status['gas_record_prefix_number'] ))
    except Exception as e:
        flog.error(inspect.stack()[0][3]+": gas telegram prefix record niet gewijzigd." + str(e) )

#############################################################
# get the van crc controle from the config database         #
#############################################################
def get_P1_crc( status=None ,configdb=None, flog=None ):

    try:

        if configdb.strget( 45,flog )[1] == "0":
            status['p1_crc_check_is_on'] = False
        else:
            status['p1_crc_check_is_on'] = True

        flog.debug( inspect.stack()[0][3]+": CRC check is " + str( status['p1_crc_check_is_on'] ) )

    except Exception as e:
        flog.error( inspect.stack()[0][3]+": CRC aan of uit niet te lezen => ." + str(e) )

#############################################################
# update the JSON dataset for DBX, UDP, etc                 #
#############################################################
def update_json_data( jsondata=None, p1data=None ):

    #convert dutch tarif code to English Dal = Low, Peak = High 
    if p1data['tarief_code'] == 'P': 
        tarief_code = 'HIGH'
    else: 
        tarief_code = "LOW" # there are only two options (D/P)

    jsondata[ apiconst.JSON_TS_LCL ]                   = str(util.mkLocalTimeString())
    jsondata[ apiconst.JSON_TS_LCL_UTC ]               = util.getUtcTime()
    jsondata[ apiconst.JSON_API_API_STTS ]             = 'production'
    jsondata[ apiconst.JSON_API_CNSMPTN_KWH_L ]        = float( p1data['verbrk_kwh_181'] )
    jsondata[ apiconst.JSON_API_CNSMPTN_KWH_H ]        = float( p1data['verbrk_kwh_182'] )
    jsondata[ apiconst.JSON_API_PRDCTN_KWH_L ]         = float( p1data['gelvr_kwh_281']  )
    jsondata[ apiconst.JSON_API_PRDCTN_KWH_H ]         = float( p1data['gelvr_kwh_282'] )
    jsondata[ apiconst.JSON_API_TRFCD ]                = str( tarief_code )
    jsondata[ apiconst.JSON_API_CNSMPTN_KW ]           = float( p1data['act_verbr_kw_170'] )
    jsondata[ apiconst.JSON_API_PRDCTN_KW ]            = float( p1data['act_gelvr_kw_270'] )
    jsondata[ apiconst.JSON_API_CNSMPTN_GAS_M3 ]       = float( p1data['gas_verbr_m3_2421'] )
    jsondata[ apiconst.JSON_API_SYSTM_ID]              = systemid.getSystemId()

#############################################################
# set the gas value in the dataset                          #
#############################################################
def instert_db_gas_value( data_set=None, status=None, statusdb=None, flog=None ):

    try:
        statusdb.strset(str(float( data_set['gas_verbr_m3_2421'] )), 43, flog )
    except Exception as e:
        flog.error(inspect.stack()[0][3]+": Melding="+str(e.args[0]))
    
    # calculate gas/hour value.
    try:
        #print ( 'run version ='+str(int(time.time()))+ ' delta ='+str(int(time.time() - g2h_previous_timestamp)) )
        if status['g2h_previous_timestamp'] == const.NOT_SET: # first run
            status['g2h_previous_timestamp'] = int(time.time())
            status['g2h_previous_gas_value'] = data_set['gas_verbr_m3_2421']
            return

        #print ( '--------------------0' )
        #print ( gas_verbr_m3_2421 )

        if status['g2h_previous_gas_value'] != data_set['gas_verbr_m3_2421']:
            #flog.setLevel( logging.DEBUG )
            #print ( '--------------------1' )
            #print ( g2h_previous_gas_value )
            #print ( gas_verbr_m3_2421 )
            gas_delta  = abs( float( status['g2h_previous_gas_value'] ) - float( data_set['gas_verbr_m3_2421'] ) )
            time_delta = abs( int(   status['g2h_previous_timestamp'] ) - int(time.time()) )

            flog.debug( inspect.stack()[0][3] + ": gas waarde verschild met vorige meting=" + str(gas_delta)  )
            flog.debug( inspect.stack()[0][3] + ": seconden verstreken met vorige meting="  + str(time_delta) )

            gas_m2hour = ( gas_delta / time_delta) * 3600
            flog.debug( inspect.stack()[0][3] + ": gas per uur (berekend) =" + str(gas_m2hour ) )

            statusdb.strset(str(float(gas_m2hour)),50,flog)

            status['g2h_previous_timestamp'] = int(time.time())
            status['g2h_previous_gas_value'] = data_set['gas_verbr_m3_2421']

            #flog.setLevel( logging.INFO )

    except Exception as e:
            flog.error(inspect.stack()[0][3]+": gas per uur fout -> "+str(e))


#############################################################
# set the status database with peak values                  #
#############################################################
def set_peak_kw_value(data_set=None, dbstatus=None, flog=None ):
    
    try:
        
        # 1.4.0. update
        if float(data_set['peak_quarter_hour_140']) != const.NOT_SET: #only do updates if once set, not every smart meter supplies the 1.4.0. code
            _id, value, _label, _security = dbstatus.strget( 32, flog ) 
            if value != str(data_set['peak_quarter_hour_140']) :
                #print("1.4.0 update")
                dbstatus.strset( str(data_set['peak_quarter_hour_140']) ,32 ,flog )
                dbstatus.strset( str(util.mkLocalTimeString()) ,33 ,flog )            # 'peak_quarter_hour_140_ts' 

        #1.6.0 updates
        if float(data_set['peak_month_peak_160']) != const.NOT_SET:
            _id, value, _label, _security = dbstatus.strget( 34, flog )
            _id, timestamp, _label, _security = dbstatus.strget( 35, flog )
            #print ("#1",  value )
            #print ("#2",  timestamp )
            #print ("#3",  str(data_set['peak_month_peak_160_ts']))

            if value != str(data_set['peak_month_peak_160']) or timestamp != telegram_timestr_conversion( p1_telgram=str(data_set['peak_month_peak_160_ts'])):
                #print("1.6.0 update")
                dbstatus.strset( str(data_set['peak_month_peak_160']) ,34 ,flog )
                dbstatus.strset( telegram_timestr_conversion( p1_telgram=str(data_set['peak_month_peak_160_ts']), flog=flog ) ,35 ,flog )

    except Exception as e:
        flog.error( inspect.stack()[0][3] + ": peak waarde update gefaald. Melding = "+str(e.args[0]) )


############################################################
# make standard timestring from P1 telegram timestring     #
############################################################
def telegram_timestr_conversion( p1_telgram=None, flog=None ) -> str:
    try:
        return p1_telgram[0:4] + "-" + p1_telgram[4:6] + "-" + p1_telgram[6:8] + " " + p1_telgram[8:10] + ":" + p1_telgram[10:12] + ":" + p1_telgram[12:14]
    except Exception as e:
        flog.error( inspect.stack()[0][3] + ": tijd conversie gefaald. Melding="+str(e.args[0]) )
        return ""

 
#############################################################
# set the status database with the max kWh values           #
#############################################################
def max_kWh_day_value(data_set=None, dbstatus=None, dbserial=None, flog=None ):
    
    #flog.setLevel( logger.logging.DEBUG )

    timestr=util.mkLocalTimeString()
    daytime_start_str = timestr[0:10]+" 00:00:00"
    daytime_end_str   = timestr[0:10]+" 23:59:59"

    try:
        sqlstr = "select verbr_kwh_181,verbr_kwh_182,gelvr_kwh_281,gelvr_kwh_282 \
        from " + const.DB_SERIAL_TAB+" where timestamp = \
        (select min(timestamp) from "+const.DB_SERIAL_TAB + \
        " where timestamp >= '" + daytime_start_str + "'and timestamp <= '" + daytime_end_str + "')"
        sqlstr = " ".join(sqlstr.split())
        flog.debug(inspect.stack()[0][3]+": sql="+sqlstr) 
        
        start_van_dag_waarde = dbserial.select_rec( sqlstr )
        flog.debug(inspect.stack()[0][3]+": record="+str(start_van_dag_waarde))
        
        dbstatus.strset( util.alwaysPlus(float( data_set['verbrk_kwh_181'] )- float(start_van_dag_waarde[0][0])),8,flog  )
        dbstatus.strset( util.alwaysPlus(float( data_set['verbrk_kwh_182'] )- float(start_van_dag_waarde[0][1])),9,flog  )
        dbstatus.strset( util.alwaysPlus(float( data_set['gelvr_kwh_281']  ) - float(start_van_dag_waarde[0][2])),10,flog )
        dbstatus.strset( util.alwaysPlus(float( data_set['gelvr_kwh_282']  ) - float(start_van_dag_waarde[0][3])),11,flog )

    except Exception as e:
        flog.error( inspect.stack()[0][3]+": serial e-buffer kwH waarden vorige dag gefaald. Melding="+str(e.args[0]) )
    #flog.setLevel( logger.logging.INFO )

#############################################################
# insert a record in the serial database                    #
#############################################################
def insert_db_serial_record( data_set=None, status=None ,dbstatus=None, dbserial=None, flog=None ):

    try:

        # Bug fix from between 1.3.0 and 1.4.1
        dbstatus.strset( str( data_set['tarief_code'] ), 85, flog )

        timestr = util.mkLocalTimeString()
        #timestr_min=timestr[0:16]+":00"

        if status['gas_present_in_serial_data'] == False:
            #gas_verbr_m3_2421 = 0
            data_set['gas_verbr_m3_2421'] = 0

        sqlstr ="insert or replace into " + const.DB_SERIAL_TAB + \
        " values (\
        '"+timestr+"',\
        '"+"0"+"',\
        '"+str( data_set['verbrk_kwh_181'] )+"', \
        '"+str( data_set['verbrk_kwh_182'] )+"', \
        '"+str( data_set['gelvr_kwh_281'] )+"', \
        '"+str( data_set['gelvr_kwh_282'] )+"', \
        '"+str( data_set['tarief_code'] )+"', \
        '"+str( data_set['act_verbr_kw_170'] )+"', \
        '"+str( data_set['act_gelvr_kw_270'] )+"',\
        '"+str( data_set['gas_verbr_m3_2421'] )+"')"
        sqlstr = " ".join(sqlstr.split())
        flog.debug( inspect.stack()[0][3] + ": (2)serial e-buffer insert: sql=" + sqlstr )

        dbserial.insert_rec( sqlstr )
        # timestamp telegram processed
        dbstatus.timestamp( 16, flog )                        # Timestring + Daylight saving.
        dbstatus.strset( str(util.getUtcTime()), 87 , flog  ) # UTC time
        status['p1_record_is_ok'] = 1
        dbstatus.strset( str(status['p1_record_is_ok']), 46, flog ) # P1 data is ok recieved
        status['timestamp_last_insert'] = util.getUtcTime()

       # if util.isMod( timestr,15 ) == True:
       #     backupData()

    except Exception as e:
        flog.error(inspect.stack()[0][3]+": Insert gefaald. Melding="+str(e.args[0]))

#############################################################
# read the last/current room temperature values in + out    #
#############################################################
def current_room_temperature( temperaturedb=None, flog=None):
    sqlstr = "select TEMPERATURE_1_AVG, TEMPERATURE_2_AVG FROM " + \
         const.DB_TEMPERATUUR_TAB + " where record_id = 10 order by timestamp desc limit 1"

    try:
        temperature_in  = 0 # failsave if there is no data
        temperature_out = 0 # failsave if there is no data
        list = temperaturedb.select_rec( sqlstr )
        temperature_in  = list[0][0]
        temperature_out = list[0][1]
    except Exception as e:
        flog.debug(inspect.stack()[0][3]+": DB lezen van temperatuur (kamer) melding:"+str(e.args[0]))

    flog.debug( inspect.stack()[0][3] +  ": temperature_in=" + str(temperature_in) + " temperature_out="+str(temperature_out) )
    return temperature_in, temperature_out

#############################################################
# read the last/current watermeter value                    #
#############################################################
def current_watermeter_count( configdb=None, waterdb=None, flog=None):

    try:
        _id, is_water_active, _label = configdb.strget( 96, flog )
        #print( "is_water_active=" + str(is_water_active) )

        if int( is_water_active ) == 0: # return
            flog.debug( inspect.stack()[0][3] + ": water meting staat uit. " )
            return 0

        watermeters_count_total = 0 # failsave if there is no data
        _timestamp, _utc, _puls_per_timeunit, _verbr_per_timeunit, verbr_in_m3_total = waterdb.select_one_record() 
        #print( "verbr_in_m3_total=" + str( verbr_in_m3_total ) )
        if verbr_in_m3_total != None:
            watermeters_count_total = round( float( verbr_in_m3_total ), 3 )
            flog.debug( inspect.stack()[0][3] +  ": watermeters_count_total=" + str(watermeters_count_total) )
            return watermeters_count_total
    except Exception as e:
        pass
        #flog.warning( inspect.stack()[0][3] + ": probleem bij het lezen van de watermeter stand -> " + str(e.args[0]) )
    return 0

#############################################################
# set all values in the data structure to NOT SET           #
#############################################################
def clear_data_buffer( buffer=None ):
    for key in buffer:
        buffer[key] = const.NOT_SET

#############################################################
# deletes the records in the serial data base based on the  #
# number of retention day's. currently 7 days for 10 sec    #
# processing and 1 day for 1 second processing              #
# only records that are processed are deleted on normal     #
# conditions. As failsave all records older then 7+1 or     #
# 1+1 are deleted to prevent exhausting the available space #
# on the ram disk                                           #
#############################################################
def delete_serial_records( p1_processing=None, serial_db=None, flog=None ):

    try:
        
        timestampstr = util.mkLocalTimeString()
       
        sql_del_str = "delete from " + const.DB_SERIAL_TAB + " where timestamp < '" + \
        str(datetime.datetime.strptime( timestampstr, "%Y-%m-%d %H:%M:%S") -\
        datetime.timedelta( days=p1_processing['max_days_db_data_retention']) )+ \
        "' and record_verwerkt=1"
    
        flog.debug(inspect.stack()[0][3]+": serial e-buffer delete: sql=" + sql_del_str )

        serial_db.del_rec( sql_del_str )

        sql_del_str = "delete from " + const.DB_SERIAL_TAB + " where timestamp < '" + \
        str(datetime.datetime.strptime( timestampstr, "%Y-%m-%d %H:%M:%S") -\
        datetime.timedelta( days=p1_processing['max_days_db_data_retention'] + 1) ) + "'"
        
        flog.debug(inspect.stack()[0][3]+": serial e-buffer delete: sql=" + sql_del_str )
        serial_db.del_rec( sql_del_str )

    except Exception as e:
        flog.error(inspect.stack()[0][3]+": delete gefaald. Melding=" + str(e.args[0]) )


###########################################################
# set the rate limiting of P1 telegram and the retention  #
# days of the serial database                             #
###########################################################
def set_p1_processing_speed( p1_processing = None , config_db=None, flog=None ):
    try:
        change_flag = p1_processing['max_processing_speed']
        _id, processing, _label = config_db.strget( 154, flog )

        if processing == "1":
            p1_processing['max_processing_speed'] = True
            p1_processing['max_days_db_data_retention'] = 1
        else:
            p1_processing['max_processing_speed'] = False
            p1_processing['max_days_db_data_retention'] = 7

        if change_flag != p1_processing['max_processing_speed']:
            flog.info( inspect.stack()[0][3] + ": maximale snelheid P1 data verwerking gewijzigd naar " + str( p1_processing['max_processing_speed'] ) )
            flog.info( inspect.stack()[0][3] + ": slimme meter data rententie is " + str(  p1_processing['max_days_db_data_retention'] ) + " dag(en)." )

    except Exception as e:
        flog.warning( inspect.stack()[0][3] + ": P1 10/of 1 seconden snelheid fout ->  " + str(e.args) )


###########################################################
# write the json data in the buffer array to a ram file   #
###########################################################
def write_p1_json_to_ram( data=None, flog=None, sysid=const.SYSTEM_ID_DEFAULT ):
    #flog.setLevel(logging.DEBUG)
   
    try:
        filename     = const.DIR_RAMDISK  + const.API_BASIC_JSON_PREFIX + sysid + const.API_BASIC_JSON_SUFFIX
        filename_tmp = const.DIR_RAMDISK  + const.API_BASIC_JSON_PREFIX + sysid + const.API_BASIC_JSON_SUFFIX + ".tmp"
        flog.debug(inspect.stack()[0][3]+": json output =" + json.dumps( data , sort_keys=True ) + " naar bestand " + filename)
        with open( filename_tmp, 'w') as outfile:
            json.dump( data , outfile, sort_keys=True )
        util.setFile2user( filename_tmp,'p1mon' ) # to make sure we can process the file
        if os.path.exists( filename_tmp ):
            if os.path.getsize( filename_tmp ) > 250: # only write the file if it has some content
                shutil.move( filename_tmp, filename ) # beter then os.rename/os.move
    except Exception as e:
        flog.error(inspect.stack()[0][3]+": wegschrijven data naar ramdisk is mislukt. melding:"+str(e.args[0]))

    #flog.setLevel(logging.INFO)

###########################################################
#  write the json data to the Dropbox file buffer and     #
# only do this every 10 seconds. Rate limiting to not     #
# overload Dropbox                                        #
###########################################################
def write_p1_json_dbx_folder( configdb=None, data=None, flog=None, sysid=const.SYSTEM_ID_DEFAULT, utc_ok_timestamp=0):
    
    #flog.setLevel(logging.DEBUG)
    _id, parameter, _label = configdb.strget(50,flog) # is Dropbox is on or off 
    if int(parameter) == 0: # dropbox sharing is off
        return utc_ok_timestamp # do nothing

    #print ("#!"+ str( abs(util.getUtcTime() - utc_ok_timestamp) ) )

    if abs(util.getUtcTime() - utc_ok_timestamp) < 10:
         return utc_ok_timestamp # do nothing, DBX rate limting

    try:
        filename = const.DIR_DBX_LOCAL + const.DBX_DIR_DATA + '/' + const.API_BASIC_JSON_PREFIX + sysid + const.API_BASIC_JSON_SUFFIX
        flog.debug(inspect.stack()[0][3]+": json output =" + json.dumps( data , sort_keys=True ) + " naar bestand " + filename )

        with open(filename, 'w') as outfile:
            json.dump( data , outfile, sort_keys=True )

        utc_ok_timestamp = util.getUtcTime() 
        util.setFile2user( filename,'p1mon' ) # to make sure we can process the file

    except Exception as e:
        flog.error(inspect.stack()[0][3]+": wegschrijven data naar Dropbox is mislukt. melding:"+str(e.args[0]))

    return utc_ok_timestamp
    #flog.setLevel(logging.INFO)

###########################################################
# write the serial data in the buffer array to a ram file #
###########################################################
def write_p1_telegram_to_ram( buffer=None, flog=None ):
       #dump buffer naar bestand voor user interface
    try:

        tmp_filename = const.FILE_P1MSG + ".tmp"
        filename     = const.FILE_P1MSG
        fo = open( tmp_filename, "w" )
        for item in buffer:
            filtered_string = ''.join( filter(lambda x: x in string.printable, item) ).rstrip()[0:1024]
            #print ( filtered_string )
            fo.write("%s\n" % filtered_string )
        fo.flush() # needed or else the file size check wil fail.
        fo.close
        #print ("size is " + str( os.path.getsize( tmp_filename ) ) )
        if os.path.getsize( tmp_filename ) > 200: # only write the file if it has some content
                shutil.move( tmp_filename, filename ) # beter then os.rename()
        
        flog.debug(inspect.stack()[0][3]+": file weggeschreven naar " + filename )

    except Exception as e:
        flog.error(inspect.stack()[0][3]+": p1 berichten buffer wegschrijven naar file " + str(e.args[0]) )
