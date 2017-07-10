""" Testing GDB, yay """

import os
from gnuradio import gr
from gnuradio import blocks
from gnuradio import digital
from gnuradio import analog
import specmonitor as specmonitor
import zadoffchu
import numpy as np
import matplotlib.pyplot as plt

class CreateSNREstTest(gr.top_block):
    def __init__(self, snr_val, verbose=False):
        gr.top_block.__init__(self,name="SNR estimation accuracy test")
        zc_seq_len = 503#199

        sample_rate = 1e6
        frame_duration = 2.0e-3
        test_duration = 1.5*frame_duration
        samples_per_frame = int(round(frame_duration*sample_rate))
        samples_per_test = int(round(test_duration*sample_rate))
        n_samples_snr_estim = zc_seq_len#int(round(samples_per_frame/20))
        random_samples_skip = np.random.randint(samples_per_frame/2)+samples_per_frame/2
        preamble_seq = zadoffchu.generate_sequence(zc_seq_len,1,0)
        preamble_pwr_sum = np.sum(np.abs(preamble_seq)**2)
        sigma_val = 1/float(10.0**(snr_val/20.0))
        thres = 0.25

        # if samples_per_test-random_samples_skip+2*preamble_seq.size+n_samples_snr_estim >= samples_per_test:
        #     print "The test duration is not long enough"
        #     exit()

        self.framer = specmonitor.framer_c(sample_rate, frame_duration, preamble_seq)
        self.awgn = analog.noise_source_c(analog.GR_GAUSSIAN,sigma_val)
        self.add = blocks.add_cc()
        self.skiphead = blocks.skiphead(gr.sizeof_gr_complex, random_samples_skip)
        self.corr_est = specmonitor.corr_est_norm_cc(preamble_seq,1,0,thres)#digital.corr_est_cc(preamble_seq, 1, 0)
        self.snr_est = specmonitor.framer_snr_est_cc(n_samples_snr_estim, preamble_seq.size)
        if verbose is True:
            self.tag_db = blocks.tag_debug(gr.sizeof_gr_complex, "tag debugger")
        self.head = blocks.head(gr.sizeof_gr_complex, samples_per_test)
        self.dst = blocks.vector_sink_c()

        self.connect(self.framer,(self.add,0))
        self.connect(self.awgn,(self.add,1))
        self.connect(self.add,self.skiphead)
        self.connect(self.skiphead,self.head)
        self.connect(self.head,self.corr_est)
        self.connect(self.corr_est,self.snr_est)
        if verbose is True:
            self.connect(self.snr_est,self.tag_db)
        self.connect(self.snr_est,self.dst)

def test_RMSE_vs_SNR():
    """ go, go, go """
    SNRdB_range = np.arange(-5,41)
    n_runs_per_SNR = [500]*(SNRdB_range.size)
    SNRestimdB = np.zeros(len(SNRdB_range))
    SNRestimdB_std = np.zeros(len(SNRdB_range))
    SNRestimdB_rmse = np.zeros(len(SNRdB_range))
    SNRestimdB_bias = np.zeros(len(SNRdB_range))
    nan_counter = np.zeros(len(SNRdB_range))
    for i,s in enumerate(SNRdB_range):
        print "Run",i, ": SNRdB =", s
        run_snr_l = []
        N = n_runs_per_SNR[i]
        for r_i in range(N):
            while True:
                top_block = CreateSNREstTest(s)
                top_block.run()
                x_data = top_block.dst.data()
                snr_estim = top_block.snr_est.SNRdB()
                if np.isnan(snr_estim):
                    if nan_counter[i]==0:
                        print "Got an SNR as a NaN"
                    nan_counter[i]+=1
                else:
                    break
            run_snr_l.append(snr_estim)
        SNRestimdB[i] = np.mean(np.array(run_snr_l))
        SNRestimdB_std[i] = np.std(np.array(run_snr_l))*N/(N-1)
        SNRestimdB_rmse[i] = np.sqrt(np.mean((np.array(run_snr_l)-s)**2))
        SNRestimdB_bias[i] = np.mean(np.array(run_snr_l)-s)

    print "I got this amount of NaNs: ", nan_counter

    if np.min(n_runs_per_SNR)>1:
        fig, (ax0, ax1) = plt.subplots(nrows=2)

        ax0.plot(SNRdB_range,SNRestimdB, 'bx-')
        ax0.plot(SNRdB_range,SNRdB_range,'k--')
        if np.min(n_runs_per_SNR)>1:
            # SNRestimdB_sigma = np.sqrt(N/(N-1)*(SNRestimdB_m2 - SNRestimdB**2))
            print "standard deviation: ", SNRestimdB_std
            print "standard rmse: ", SNRestimdB_rmse
            ax1.plot(SNRdB_range,SNRestimdB_rmse, 'bx-')
            ax1.plot(SNRdB_range,SNRestimdB_std, 'ro-')
            ax1.plot(SNRdB_range,SNRestimdB_bias, 'g-')
            # plt.plot(SNRdB_range,SNRestimdB+SNRestimdB_sigma,'b--')
    else:
        plt.plot(SNRdB_range,SNRestimdB, 'bx-')
        plt.plot(SNRdB_range,SNRdB_range, 'k--')
    plt.show()

if __name__ == "__main__":
    print 'Blocked waiting for GDB attach (pid = %d)' % (os.getpid(),)
    raw_input ('Press Enter to continue: ')
    test_RMSE_vs_SNR()
