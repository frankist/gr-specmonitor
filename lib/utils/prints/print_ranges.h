/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

/*
 * File:   general_utils.hpp
 * Author: connect
 *
 * Created on 31 January 2017, 10:11
 */

#include <boost/format.hpp>
#include <sstream>      // std::stringstream
#include <numeric>
#include <complex>
#include <iostream>
#include <stdexcept>

#ifndef _PRINT_UTILS_H_
#define _PRINT_UTILS_H_

template<typename T>
std::string print_complex(std::complex<T> c)
{
    std::stringstream os;
    if(c.imag()>0)
      os << c.real() << "+" << c.imag() << "j";
    else
      os << c.real() << c.imag() << "j";
    return os.str();
}

namespace utils {
template<typename T>
std::complex<T> parse_complex(const std::string& s) {
  std::string stmp = s;
  std::size_t plus_pos = s.find('+');
  std::size_t minus_pos = s.find('-');
  if(plus_pos != std::string::npos || minus_pos != std::string::npos) { // a+bj format
    std::size_t j_pos = s.find('j');
    if(j_pos != std::string::npos) {
      bool neg = false;
      if(plus_pos != std::string::npos)
        stmp[plus_pos] = ' ';
      else if(minus_pos != std::string::npos) {
        stmp[minus_pos] = ' ';
        neg = true;
      }
      stmp[j_pos] = ' ';
      std::stringstream ss(stmp);
      T r, i;
      ss >> r >> i;
      if(neg)
        i = -i;
      return std::complex<T>(r,i);
    }
  }
  throw std::invalid_argument("The format of the complex number is not supported");
}
};

namespace container
{
template<typename Iterator>
std::string print(Iterator b, Iterator e)
{
    std::stringstream os;
    Iterator it = b;
    os << "[";
    os << *b;
    for (++it; it != e; ++it)
        os << ", " << *it;
    os << "]";
    return os.str();
}

template<typename Iterator, typename Op>
std::string print(Iterator b, Iterator e, Op func)
{
    std::stringstream os;
    Iterator it = b;
    os << "[" << func(*b);
    for (++it; it != e; it++)
        os << ", " << func(*it);
    os << "]";
    return os.str();
}

template<typename Iterator, typename Op>
std::string print(Iterator b, Iterator e, const std::string& separator, Op func)
{
    std::stringstream os;
    Iterator it = b;
    os << "[" << func(*b);
    for (++it; it != e; it++)
        os << separator << func(*it);
    os << "]";
    return os.str();
}

template<typename Iterator, typename Op>
std::string print(Iterator b, Iterator e, const std::string& separator, const std::string& format, Op func)
{
    std::stringstream os;
    Iterator it = b;
    os << "[" << func(*b);
    for (++it; it != e; it++)
        os << separator << boost::format(format) % func(*it);
    os << "]";
    return os.str();
}
};

namespace range
{
template<typename Range>
std::string print(const Range& r)
{
    return container::print(r.begin(), r.end());
}

template<typename Range, typename Op>
std::string print(const Range& r, Op func)
{
    return container::print(r.begin(), r.end(), func);
}

template<typename Range, typename Op>
std::string print(const Range& r, const std::string& separator, Op func)
{
    return container::print(r.begin(), r.end(), separator, func);
}
};

#endif /* _PRINT_UTILS_H_ */
