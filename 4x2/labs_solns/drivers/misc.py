import numpy as np
from qick.qick import SocIp

class AxisKidsimV3(SocIp):
    bindto = ['user.org:user:axis_kidsim_v3:1.0']
    
    # Sampling frequency and frequency resolution (Hz).
    FS_DDS = 1000
    DF_DDS = 1
    
    # DDS bits.
    B_DDS = 16

    # Coefficient/gain bits.
    B_COEF = 16
    
    def __init__(self, description):
        # Initialize ip
        super().__init__(description)
        
        self.REGISTERS = {'dds_bval_reg' : 0, 
                 'dds_slope_reg': 1, 
                 'dds_steps_reg': 2, 
                 'dds_wait_reg' : 3, 
                 'dds_freq_reg' : 4, 
                 'iir_c0_reg'   : 5, 
                 'iir_c1_reg'   : 6, 
                 'iir_g_reg'    : 7, 
                 'outsel_reg'   : 8, 
                 'punct_id_reg' : 9, 
                 'addr_reg'     : 10, 
                 'we_reg'       : 11}

        # Default registers.
        self.we_reg = 0 # Don't write.
        
        # Generics.
        self.L      = int(description['parameters']['L'])
        self.NCH    = 256
        self.NPUNCT = int(self.NCH/self.L)
        
    def configure(self, fs):
        self.logger.debug("configure %s"%(fs))
        fs_hz = fs*1000*1000
        self.FS_DDS = fs_hz
        self.DF_DDS = self.FS_DDS/2**self.B_DDS
        
    def set_registers(self, dds_bval, dds_slope, dds_steps, dds_wait, dds_freq, iir_c0, iir_c1, iir_g, outsel, punct_id, addr):
        self.logger.debug("set_registers %s"%([dds_bval, dds_slope, dds_steps, dds_wait, dds_freq, iir_c0, iir_c1, iir_g, outsel, punct_id, addr]))
        self.dds_bval_reg  = dds_bval
        self.dds_slope_reg = dds_slope
        self.dds_steps_reg = dds_steps
        self.dds_wait_reg  = dds_wait
        self.dds_freq_reg  = dds_freq
        self.iir_c0_reg    = iir_c0
        self.iir_c1_reg    = iir_c1
        self.iir_g_reg     = iir_g
        self.outsel_reg    = outsel
        self.punct_id_reg  = punct_id
        self.addr_reg      = addr
        
        # Write enable pulse.
        self.we_reg     = 1
        self.we_reg     = 0
        
    
    def set_resonator(self, config, verbose = False):
        self.logger.debug("set_resonator %s"%(config))
        self.set_resonator_config(config, verbose)
        self.set_resonator_regs(config, verbose)
        
    def set_resonator_config(self, config, verbose = False):
        self.logger.debug("set_resonator_config %s"%(config))
        # Check if sweep_freq is defined.
        if 'sweep_freq' not in config.keys():
            config['sweep_freq'] = 0.9

        # Check if sweep_time is defined.
        if 'sweep_time' not in config.keys():
            config['sweep_time'] = 100

        # Check if iir_c0 is defined.
        if 'iir_c0' not in config.keys():
            config['iir_c0'] = 0.99

        # Check if iir_c1 is defined.
        if 'iir_c1' not in config.keys():
            config['iir_c1'] = 0.8

        # Gain.
        config['iir_g'] = (1+config['iir_c1'])/(1+config['iir_c0']);

        # Check if sel is defined.
        if 'sel' not in config.keys():
            config['sel'] = 'resonator'

        # Compute PFB Channel from frequency specification.
        if 'channel' not in config.keys():
            config['channel'] = 0

        # Compute DDS frequency.
        if 'dds_freq' not in config.keys():
            config['dds_freq'] = 0

        # Compute Lane number from PFB channel specification.
        config['lane'] = np.mod(config['channel'], self.L)

        # KIDSIM puncuring index.
        config['punct_id'] = int(np.floor(config['channel']/self.L))

        # Sampling frequency of DDSs.
        fs = self.FS_DDS/1e6
        ts = 1/fs

        # Check if nstep is defined.
        if 'nstep' in config.keys():
            config['dds_wait'] = int(config['sweep_time']/(config['nstep']*ts)) - 1
        else:
            #  Check if dds_wait is defined.
            if 'dds_wait' not in config.keys():
                config['dds_wait'] = 1

            # Number of steps.
            config['nstep'] = int(config['sweep_time']/((config['dds_wait']+1)*ts))
        
        # Sanity check (slope = 0).
        config['dds_bval_reg'] = int(round(config['sweep_freq']*1e6/self.DF_DDS))
        config['dds_slope_reg'] = int(round(config['dds_bval_reg']/config['nstep']))
        if (config['dds_slope_reg'] < 1):
            config['dds_slope_reg'] = 1
            config['nstep'] = config['dds_bval_reg']
            config['sweep_time'] = config['nstep']*((config['dds_wait']+1)*ts)
            print('{}: Updated sweep_time to {} us. Try increasing dds_wait.'
                  .format(self.__class__.__name__, config['sweep_time']))

        if verbose:
            print('{}: sel        = {}'.format(self.__class__.__name__,config['sel']))
            print('{}: channel    = {}'.format(self.__class__.__name__,config['channel']))
            print('{}: lane       = {}'.format(self.__class__.__name__,config['lane']))
            print('{}: punct_id   = {}'.format(self.__class__.__name__,config['punct_id']))
            print('{}: iir_c0     = {}'.format(self.__class__.__name__,config['iir_c0']))
            print('{}: iir_c1     = {}'.format(self.__class__.__name__,config['iir_c1']))
            print('{}: iir_g      = {}'.format(self.__class__.__name__,config['iir_g']))
            print('{}: dds_freq   = {}'.format(self.__class__.__name__,config['dds_freq']))
            print('{}: dds_wait   = {}'.format(self.__class__.__name__,config['dds_wait']))
            print('{}: sweep_freq = {}'.format(self.__class__.__name__,config['sweep_freq']))
            print('{}: sweep_time = {}'.format(self.__class__.__name__,config['sweep_time']))
            print('{}: nstep      = {}'.format(self.__class__.__name__,config['nstep']))
    
    def set_resonator_regs(self, config, verbose = False):
        self.logger.debug("set_resonator_regs %s"%(config))
        # DDS Section Registers.
        dds_bval_reg  = config['dds_bval_reg']
        dds_slope_reg = config['dds_slope_reg']
        dds_steps_reg = config['nstep']
        dds_wait_reg  = config['dds_wait']
        dds_freq_reg  = int(round(config['dds_freq']*1e6/self.DF_DDS))

        if verbose:
            print('freq = {}, bval = {}, slope = {}, steps = {}, wait = {}'
                  .format(dds_freq_reg,dds_bval_reg,dds_slope_reg,dds_steps_reg,dds_wait_reg))

        # IIR Section Registers.
        iir_c0_reg = int(round(config['iir_c0']*(2**(self.B_COEF-1))))
        iir_c1_reg = int(round(config['iir_c1']*(2**(self.B_COEF-1))))
        iir_g_reg  = int(round(config['iir_g' ]*(2**(self.B_COEF-1))))

        if verbose:
            print('c0 = {}, c1 = {}, g = {}'
                  .format(iir_c0_reg, iir_c1_reg, iir_g_reg))

        # Output Section Registers.
        if config['sel'] == "resonator":
            outsel_reg = 0
        elif config['sel'] == "dds":
            outsel_reg = 1
        elif config['sel'] == "input":
            outsel_reg = 2
        else:
            outsel_reg = 3

        punct_id_reg = config['punct_id']
        addr_reg     = config['lane']

        if verbose:
            print('sel = {}, punct_id = {}, addr = {}'
                  .format(outsel_reg, punct_id_reg, addr_reg))

        # Set Registers.
        self.set_registers(
            dds_bval_reg ,
            dds_slope_reg,
            dds_steps_reg,
            dds_wait_reg ,
            dds_freq_reg ,
            iir_c0_reg   ,
            iir_c1_reg   ,
            iir_g_reg    ,
            outsel_reg   ,
            punct_id_reg ,
            addr_reg     )                        
        

    def setall(self, config, verbose = False):
        self.logger.debug("setall %s"%(config))
        # Build configuration dictionary.
        self.set_resonator_config(config)
        
        # Set all resonators (L) to the same configuration.
        for i in range(self.L):
            # Overwrite lane.
            config['lane'] = i

            # Write values into hardware.
            self.set_resonator_regs(config, verbose)

