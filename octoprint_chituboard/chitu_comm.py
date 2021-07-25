# coding=utf-8
#from socket import *
import socket
import netifaces as ni
from uuid import getnode as get_mac
from octoprint.filemanager.destinations import FileDestinations
import octoprint.filemanager
import multiprocessing
import struct

import octoprint.util
import logging
import threading
import select
#https://docs.python.org/3/library/socket.html

PRINTERNAME = "Mars 2"

class chitu_comm():

    def __init__(self,sel):

        self.sup = sel

        self.file_is_uploading = False
        self.ip = "0.0.0.0"

        for addr in octoprint.util.interface_addresses():
            if addr != "127.0.0.1":
                self.ip = addr

        self.mac = "0:0:0:0"
                
        self.name = "Octoprint"
        self.version = "V1.4.1"
        self.id = "28,00,26,00,0d,50,48,50"
        self.z_step_hight = "0.000625"
        self.ok_answer = str.encode("ok")
        self.nameLastUploadedFile = None
        self.file_handler = None
        self.uploaded_file_path = None
        self.shutdownSig = False

        self.last_file_position_count = 0
        

        def get_host_ip(self, parameter_list):
            #[ad["addr"] for ad in ni.ifaddresses(interface)[ni.AF_INET]
            pass
            #TODO: implemet

        def get_host_mac(self, parameter_list):
            pass
            #TODO: implemet

        def set_host_ip(self, parameter_list):
            pass    #':'.join(("%012X" % get_mac())[i:i+2] for i in range(0, 12, 2))
            #TODO: implemet

        def set_host_mac(self, parameter_list):
            pass
            #TODO: implemet

        def find_host_ip(self, parameter_list):
            pass
            #TODO: implemet #gethostbyname(gethostname())

        def find_host_mac(self, parameter_list):
            pass
            #TODO: implemet

    def printstartCP(self,cb=None):
        if cb is not None:
            self.printCB = cb
    # ~ def process_m99999(message):
        # ~ """
        # ~ M99999 is used to process Chitubox brocast requests
        # ~ """
        # ~ resp = "ok. NAME:{0} IP:{1} \n".format(PRINTERNAME, localIp)
        # ~ s.sendto(resp, address)
        # ~ if debug:
            # ~ print("Info: Received broadcast request from {0}\n".format(address[0]))
            # ~ print("Recv: {0}\nSend: {1}".format(str(message), resp))
    
    def shutdownService(self):
        pass
        #self.process_conn.send("shutdown")

    def start_listen_reqest(self):
        
        self.listen_thread = threading.Thread(target=self.listen_request)
        self.listen_thread.daemon = True
        self.listen_thread.start()
        
        """
        self.process_conn, child_conn = multiprocessing.Pipe()
        self.udp_process = multiprocessing.Process(target=self.listen_request,args=(child_conn,))

        self.udp_process.start()
        """
    def listen_request(self):
        self.file_is_uploading = False
        
        self.s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        self.s.bind(('',3000))
        self.s.settimeout(2)
        port = 3000
        self._logger.info("Info: Chitubox file receiver is now listening on the port {0}\n".format(str(port)))
        # ~ file_handler = None
        # ~ uploaded_file_path = None
        # ~ shutdownSig = False
        
        while True:
            #print(conn.recv())
            #if conn.recv() == "shutdown":
            #    self.s.close()
            #    break
            try:
                m = self.s.recvfrom(4096)
            except socket.timeout:
                continue
    
            except KeyboardInterrupt:
                self.s.close()
                break
            ############################################
            #file upload processing
            ############################################
            
            if self.file_is_uploading is True:
                if "M4012 I1" in m[0].decode('latin-1'):
                    self._logger.info("recive M4012 I1")
                    
                    #print("%s count" % (struct.unpack("<i",message_end_part)[0] 
                    
                    answer = "ok "+ str(last_file_position_count)+"/1"
                    answer_as_bytes = str.encode(answer)
                    self.s.sendto(answer_as_bytes,m[1])
                    
                    continue     
    
    
                if "M29" in m[0].decode('latin-1'):
                    self._logger.info("recive M29 end file upload")
                    self.sup._logger.info("end fileupload of file: "+uploaded_file_path)
    
                    self.file_handler.close()
    
                    self.file_is_uploading = False
    
                    self.s.sendto(self.ok_answer,m[1])
                    continue
    
                message_end_part = m[0][len(m[0])-6:len(m[0])-2]
                last_file_position_count = struct.unpack("<i",message_end_part)[0] + len(m[0])-6
    
    
                #TODO:byte len(m[0])-1 ist die "prüfsumme" 
                # muss noch validiert werden.
                #wenn prüfsumme falsch sende resend antwort
                """
                if (receivedText.Find("resend") != wxNOT_FOUND)
                {
                    long resend_index = getValue(receivedText, "resend ", -1);
                    photonFile->Seek(resend_index, wxFromStart);
                }
                
                """
    
                self.file_handler.write(m[0][0:len(m[0])-6])
    
                last_file_position_count = struct.unpack("<i",message_end_part)[0] + len(m[0])-6
    
                self.s.sendto(self.ok_answer,m[1])
                continue
    
            #############################################
    
            if m[0] == b'M99999':#to find printer in network
                self._logger.info("recive M99999 broadcast message")
    
                answer = 'ok MAC:'+ self.mac +' IP:'+self.ip.encode("utf-8")+' VER:'+self.version+' ID:'+self.id+' NAME:'+self.name
                answer_as_bytes = str.encode(answer)
                self.s.sendto(answer_as_bytes,m[1])
                continue
    
            if m[0] == b'M4001':
                #ok X:0.012500 Y:0.012500 Z:0.000625 E:0.001340 T:0/0/0/155/1 U:'GBK' B:1
                #self.log.info("recive M4001 init Message")
                answer = "ok X:0.012500 Y:0.012500 Z:"+self.z_step_hight+" E:0.001340 T:0/0/0/155/1 U:'GBK' B:1"
                answer_as_bytes = str.encode(answer)
                self.s.sendto(answer_as_bytes,m[1])
                continue
    
            ############################################
            #file upload
            ############################################
            if "M28" in m[0].decode('latin-1'):
                self._logger.info("recive M28 start Fileupload")
                
                self.nameLastUploadedFile = m[0][3:len(m[0])].decode('latin-1')
                self.uploaded_file_path = self.sup._settings.global_get_basefolder("watched") + "/" + self.nameLastUploadedFile
    
                try:
                    self.file_handler = open(self.uploaded_file_path, "wb")
                except OSError as e:
                    self.sup._logger.info("cant write to file "+ file_path +" , throwing error")
                
                self.file_is_uploading = True
                self.s.sendto(self.ok_answer,m[1])
                continue
    
            if "M6030" in m[0].decode('latin-1'):
                print("recive M6030 start Print")
    
                filenameToSelect = self.sup._file_manager.path_on_disk(FileDestinations.LOCAL, self.nameLastUploadedFile)
                print(filenameToSelect)
                self.sup.sla_printer.select_file(filenameToSelect, False, printAfterSelect=True)
    
                self.s.sendto(self.ok_answer,m[1])
                continue
            ##self._storage(destination).file_in_path(path, file)
