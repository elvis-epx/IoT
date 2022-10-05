#ifndef __STRBUF_H
#define __STRBUF_H

#include <cstddef>
#include <cstdlib>
#include "Pointer.h"

/* Reusable buffer that tries to minimize heap fragmentation */

class StrBufImpl {
public:
    StrBufImpl() {
        data = 0;
        capacity = 0;
    }
    StrBufImpl(const StrBufImpl&) = delete;
    StrBufImpl& operator=(const StrBufImpl&) = delete;

    ~StrBufImpl() {
        free(data);
        data = 0;
        capacity = 0;
    }

    char *data;
    size_t capacity;
};


class StrBuf {
public:
    StrBuf();
    StrBuf(const char *);
    virtual ~StrBuf();
    const char *c_str() const;
    char *hot_str();
    void update(const char *);
    bool equals(const char *) const;
    bool equalsi(const char *) const;
    bool equals(const StrBuf &) const;
    void reserve(size_t);
    size_t length() const;

private:
    void sui_generis();
    Ptr<StrBufImpl> impl;
};

#endif
