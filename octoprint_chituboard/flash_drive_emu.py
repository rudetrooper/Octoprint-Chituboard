
#!/usr/bin/python
# coding=utf-8

import os
import stat
import logging
import subprocess


class flash_drive_emu():



    def __init__(self,firstrun = False):
        self.firstrun = firstrun
        self.errorcode = 0 
        self.error = {
            60 : "no root",
            61 : "no Pi zero",
            62 : "no first argument found",
            63 : "second argument is no dir",
            64 : "kernelmodul not enabled",
            127 : "unknown command"
        } 
        

        self._logger = logging.getLogger(__name__)

        self.filepath = "/usr/sbin/flash"

        if os.path.isfile(self.filepath):

            flashScriptStat = os.stat(self.filepath)
        
            if not(flashScriptStat.st_mode & stat.S_IRGRP):
                raise Exception('can\'t execute Flashscript')
            else:

                if self.firstrun:
                    command = 'sudo -S %s initRun' %(self.filepath)

                else:
                    command = 'sudo -S %s addMod' %(self.filepath)

                #commandtest = "/home/pi/OctoPrint-Sla_plugin/Octoprint-SLA-Plugin/flash testfail"

                p = os.system(command)

                if p>>8 <= 0:  #bitshift
                    self.errorcode = p>>8
                    raise Exception('Flashscripttest failed')


                #print(p)
                #if not subprocess.call(['sudo ' + self.filepath + ' testrun']):
                #    raise Exception('execute Flashscript as root fails')

        
        else:
            raise Exception('Flashscript dont exists')



if __name__ == '__main__':
    # execute only if run as the entry point into the program
    import sys

    try: 
        test =  flash_drive_emu()
        

    except Exception as error:
        print('Caught this error: ' + repr(error))
        sys.exit()
        

    print(dir(test))
