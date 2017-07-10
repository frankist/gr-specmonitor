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

#ifndef GENERAL_UTILS_HPP
#define GENERAL_UTILS_HPP

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

#endif /* GENERAL_UTILS_HPP */
