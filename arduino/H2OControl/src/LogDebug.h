#ifndef __LOG_H
#define __LOG_H

class Log
{
public:
    static void d(const char *);
    static void d(const char *, const char *);
    static void d(const char *, int);
    static void d(const char *, double);
};

#endif
