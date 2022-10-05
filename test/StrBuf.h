#ifndef __STRBUF_H
#define __STRBUF_H

#include <cstddef>

/* Reusable buffer that tries to minimize heap fragmentation */

class StrBufImpl;

class StrBuf {
public:
    StrBuf();
    StrBuf(const char *);
    StrBuf(const StrBuf &);
    StrBuf& operator=(const StrBuf &);
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
    StrBufImpl* impl;
};

#endif
