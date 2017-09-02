#include <boost/date_time/posix_time/posix_time.hpp>

#ifndef _TICTOC_H_
#define _TICTOC_H_

class TicToc
{
    boost::posix_time::ptime tic_tstamp;
public:
	TicToc() {
        tic();
    }
    void tic()
    {
        tic_tstamp = boost::posix_time::microsec_clock::local_time();
    }
    double toc()
    {
        double telapsed = (boost::posix_time::microsec_clock::local_time() - tic_tstamp).total_microseconds() / 1000000.0;
        return telapsed;
    }
};

#endif
