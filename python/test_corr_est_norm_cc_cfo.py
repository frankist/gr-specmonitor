""" Testing GDB, yay """

import os
from gnuradio import gr
from gnuradio import blocks
from gnuradio import digital
from gnuradio import analog
from gnuradio import channels
import specmonitor as specmonitor
import zadoffchu
import numpy as np
import matplotlib.pyplot as plt

class CreateCFORadioTest(gr.top_block):
    def __init__(self, snr_val, cfo = 0, sto = 0, verbose=False):
        gr.top_block.__init__(self,name="CFO estimation test")
        zc_seq_len = 503#199
        sample_rate = 1e6
        frame_duration = 2.0e-3
        test_duration = 1.5*frame_duration
        sigma_val = 1/float(10.0**(snr_val/20.0))
        thres = 0.25

        samples_per_frame = int(round(frame_duration*sample_rate))
        samples_per_test = int(round(test_duration*sample_rate))
        n_samples_snr_estim = zc_seq_len
        random_samples_skip = np.random.randint(samples_per_frame/2)+samples_per_frame/2
        preamble_seq = zadoffchu.generate_sequence(zc_seq_len,1,0)
        preamble_pwr_sum = np.sum(np.abs(preamble_seq)**2)

        self.framer = specmonitor.framer_c(sample_rate, frame_duration, preamble_seq)
        self.channel = channels.channel_model(sigma_val,cfo,sto,[1+1j])
        self.skiphead = blocks.skiphead(gr.sizeof_gr_complex, random_samples_skip)
        self.corr_est = specmonitor.corr_est_norm_cc(preamble_seq,1,0,thres)#digital.corr_est_cc(preamble_seq, 1, 0)
        self.snr_est = specmonitor.framer_snr_est_cc(n_samples_snr_estim, preamble_seq.size)
        if verbose is True:
            self.tag_db = blocks.tag_debug(gr.sizeof_gr_complex, "tag debugger")
        self.head = blocks.head(gr.sizeof_gr_complex, samples_per_test)
        self.dst = blocks.vector_sink_c()
        self.dst2 = blocks.vector_sink_c()

        self.connect(self.framer,self.channel)
        self.connect(self.channel,self.skiphead)
        # self.connect(self.framer,self.skiphead)
        self.connect(self.skiphead,self.head)
        self.connect(self.head,self.corr_est)
        self.connect(self.corr_est,self.snr_est)
        self.connect((self.corr_est,1),self.dst2)
        if verbose is True:
            self.connect(self.snr_est,self.tag_db)
        self.connect(self.snr_est,self.dst)

def test_CFO():
    SNRdB = 20
    cfo = 0.5
    sto = 1
    zc_len = 503
    preamble_seq = zadoffchu.generate_sequence(zc_len,1,0)

    top_block = CreateCFORadioTest(SNRdB,cfo,sto,True)
    top_block.run()
    x_data = np.array(top_block.dst.data())
    corr_data = top_block.dst2.data()
    snr_estim = top_block.snr_est.SNRdB()

    max_i = np.argmax(np.abs(corr_data))+1
    range_preamble = range(max_i,max_i+503)
    max_corr = np.max(np.abs(corr_data))
    pycorr = np.correlate(x_data,preamble_seq,'full')
    pycorr *= max_corr/np.max(np.abs(pycorr))
    pycorr = pycorr[zc_len::]

    fig, (ax0, ax1) = plt.subplots(nrows=2)
    ax0.plot(np.abs(corr_data))
    ax0.plot(np.abs(x_data),'r')
    ax0.plot(range_preamble,np.abs(x_data[range_preamble]),'g')
    ax0.plot(np.abs(pycorr),'m:')

    ax1.plot(np.abs(np.fft.fft(x_data[range_preamble]*np.conj(preamble_seq))))
    ax1.plot(np.abs(np.fft.fft(x_data[range_preamble])),'g')
    ax1.plot(np.abs(np.fft.fft(preamble_seq)),'r')
    plt.show()

# def test_CFO():
#     """ go, go, go """
#     SNRdB_range = np.arange(20,21)#np.arange(-5,41)
#     n_runs_per_SNR = [1]*(SNRdB_range.size)
#     SNRestimdB = np.zeros(len(SNRdB_range))
#     SNRestimdB_std = np.zeros(len(SNRdB_range))
#     SNRestimdB_rmse = np.zeros(len(SNRdB_range))
#     SNRestimdB_bias = np.zeros(len(SNRdB_range))
#     nan_counter = np.zeros(len(SNRdB_range))
#     for i,s in enumerate(SNRdB_range):
#         print "Run",i, ": SNRdB =", s
#         run_snr_l = []
#         N = n_runs_per_SNR[i]
#         for r_i in range(N):
#             while True:
#                 top_block = CreateSNREstTest(s)
#                 top_block.run()
#                 x_data = top_block.dst.data()
#                 y_data = top_block.dst2.data()
#                 snr_estim = top_block.snr_est.SNRdB()
#                 if np.isnan(snr_estim):
#                     if nan_counter[i]==0:
#                         print "Got an SNR as a NaN"
#                     nan_counter[i]+=1
#                 else:
#                     break
#             run_snr_l.append(snr_estim)
#         SNRestimdB[i] = np.mean(np.array(run_snr_l))
#         SNRestimdB_std[i] = np.std(np.array(run_snr_l))*N/(N-1)
#         SNRestimdB_rmse[i] = np.sqrt(np.mean((np.array(run_snr_l)-s)**2))
#         SNRestimdB_bias[i] = np.mean(np.array(run_snr_l)-s)

#     print "I got this amount of NaNs: ", nan_counter

#     if np.min(n_runs_per_SNR)>1:
#         fig, (ax0, ax1) = plt.subplots(nrows=2)

#         ax0.plot(SNRdB_range,SNRestimdB, 'bx-')
#         ax0.plot(SNRdB_range,SNRdB_range,'k--')
#         if np.min(n_runs_per_SNR)>1:
#             # SNRestimdB_sigma = np.sqrt(N/(N-1)*(SNRestimdB_m2 - SNRestimdB**2))
#             print "standard deviation: ", SNRestimdB_std
#             print "standard rmse: ", SNRestimdB_rmse
#             ax1.plot(SNRdB_range,SNRestimdB_rmse, 'bx-')
#             ax1.plot(SNRdB_range,SNRestimdB_std, 'ro-')
#             ax1.plot(SNRdB_range,SNRestimdB_bias, 'g-')
#             # plt.plot(SNRdB_range,SNRestimdB+SNRestimdB_sigma,'b--')
#     else:
#         plt.plot(SNRdB_range,SNRestimdB, 'bx-')
#         plt.plot(SNRdB_range,SNRdB_range, 'k--')
#     plt.show()

if __name__ == "__main__":
    # print 'Blocked waiting for GDB attach (pid = %d)' % (os.getpid(),)
    # raw_input ('Press Enter to continue: ')
    test_CFO()
