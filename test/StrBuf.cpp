#include <cstring>
#include <cstdlib>
#ifdef UNDER_TEST
#include <cstdio>
#endif

#include "StrBuf.h"

class StrBufImpl {
public:
    StrBufImpl() {
        data = 0;
        capacity = 0;
        refcount = 1;
    }
    StrBufImpl(const StrBufImpl&) = delete;
    StrBufImpl& operator=(const StrBufImpl&) = delete;

    ~StrBufImpl() {
        free(data);
        data = 0;
        capacity = 0;
    }

    int refcount;
    char *data;
    size_t capacity;
};

StrBuf::StrBuf()
{
    impl = new StrBufImpl();
    impl->data = strdup("Undefined");
    impl->capacity = strlen(impl->data);
#ifdef UNDER_TEST
    // printf("## alloc def %p %p\n", this, impl);
#endif
}

StrBuf::StrBuf(const char *s)
{
    impl = new StrBufImpl();
    impl->data = strdup(s);
    impl->capacity = strlen(impl->data);
#ifdef UNDER_TEST
    // printf("## alloc c %p %p\n", this, impl);
#endif
}

StrBuf::StrBuf(const StrBuf &other)
{
    impl = other.impl;
    impl->refcount += 1;
#ifdef UNDER_TEST
    // printf("## copy constructor %p %p\n", this, impl);
#endif
}

StrBuf& StrBuf::operator=(const StrBuf &other)
{
    if (this != &other) {
        impl->refcount -= 1;
        if (impl->refcount <= 0) {
#ifdef UNDER_TEST
            // printf("## del impl %p\n", impl);
#endif
            delete impl;
        }
        impl = other.impl;
        impl->refcount += 1;
#ifdef UNDER_TEST
        // printf("## assignment %p %p\n", this, impl);
#endif
    }
    return *this;
}

StrBuf::~StrBuf()
{
#ifdef UNDER_TEST
    // printf("## destroy %p\n", this);
#endif
    impl->refcount -= 1;
    if (impl->refcount <= 0) {
#ifdef UNDER_TEST
        // printf("## del impl %p\n", impl);
#endif
        delete impl;
    }
    impl = 0;
}

const char *StrBuf::c_str() const
{
    return impl->data;
}

void StrBuf::sui_generis()
{
    if (impl->refcount > 1) {
#ifdef UNDER_TEST
        // printf("## alloc sui %p %p\n", this, impl);
#endif
        StrBufImpl* copy = new StrBufImpl();
        copy->data = strdup(impl->data);
        copy->capacity = strlen(impl->data);
        impl->refcount -= 1;
        impl = copy;
    }
}

char *StrBuf::hot_str()
{
    sui_generis();
    return impl->data;
}

bool StrBuf::equals(const char *s) const
{
    return strcmp(impl->data, s) == 0;
}

bool StrBuf::equalsi(const char *s) const
{
    return strcasecmp(impl->data, s) == 0;
}

bool StrBuf::equals(const StrBuf& other) const
{
    return impl == other.impl || equals(other.c_str());
}

void StrBuf::update(const char *s)
{
    reserve(strlen(s));
    strcpy(impl->data, s);
}

void StrBuf::reserve(size_t size)
{
    sui_generis();
    if (impl->capacity < size) {
#ifdef UNDER_TEST
        // printf("## incr capacity %p %p\n", this, impl);
#endif
        impl->data = (char *) realloc(impl->data, size + 1);
        for (size_t i = impl->capacity; i <= size; ++i) {
            impl->data[i] = 0;
        }
        impl->capacity = size;
    }
}

size_t StrBuf::length() const
{
    return strlen(impl->data);
}
