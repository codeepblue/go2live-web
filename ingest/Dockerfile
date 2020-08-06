FROM ubuntu:18.04

RUN apt update -y && apt upgrade -y \
    && apt-get install --no-install-recommends --no-install-suggests -y build-essential libpcre3 libpcre3-dev libssl-dev ffmpeg git \
    && apt-get remove --purge --auto-remove -y && rm -rf /var/lib/apt/lists/*

# Install PCRE - supports regular expression, required by NGINX Core and Rewrite
ADD https://ftp.pcre.org/pub/pcre/pcre-8.44.tar.gz /build/pcre-8.44.tar.gz
RUN cd /build \
    && tar -zxf ./pcre-8.44.tar.gz \
    && cd pcre-8.44 \
    && ./configure \
    && make && make install

# Install ZLib - supports header compression, required by NGINX Gzip module
ADD http://zlib.net/zlib-1.2.11.tar.gz /build/zlib-1.2.11.tar.gz
RUN cd /build \
    && tar -zxf ./zlib-1.2.11.tar.gz \
    && cd zlib-1.2.11 \
    && ./configure \
    && make && make install

# Install OpenSSL - supports the HTTPS protocol, required by the NGINX SSL module and others
ADD http://www.openssl.org/source/openssl-1.1.1d.tar.gz /build/openssl-1.1.1d.tar.gz
RUN cd /build \
    && tar -zxf ./openssl-1.1.1d.tar.gz \
    && cd openssl-1.1.1d \
    && ./Configure linux-x86_64 --prefix=/usr \
    && make && make install

# Install NGINX with RTMP module
ADD http://nginx.org/download/nginx-1.18.0.tar.gz /build/nginx-1.18.0.tar.gz
ADD https://github.com/arut/nginx-rtmp-module/archive/v1.2.1.tar.gz /build/v1.2.1.tar.gz
RUN cd build \
    && tar -zxf ./nginx-1.18.0.tar.gz \
    && tar -zxf ./v1.2.1.tar.gz \
    && cd nginx-1.18.0 \
    && ./configure \
        --sbin-path=/usr/local/nginx/nginx \
        --conf-path=/usr/local/nginx/nginx.conf \
        --pid-path=/usr/local/nginx/nginx.pid \
        --with-pcre=/build/pcre-8.44 \
        --with-zlib=/build/zlib-1.2.11 \
        --with-http_ssl_module \
        --with-stream \
        --add-module=/build/nginx-rtmp-module-1.2.1 \
    && make && make install

# Cleanup
RUN rm -rf /build

COPY ./nginx.conf /usr/local/nginx/nginx.conf

RUN mkdir -p /record \
    && chown -R www-data:www-data /record

# VALIDATE config file
#RUN /usr/local/nginx/nginx -t

WORKDIR /record
EXPOSE 80
EXPOSE 1935

STOPSIGNAL SIGTERM

CMD ["/usr/local/nginx/nginx", "-c", "/usr/local/nginx/nginx.conf", "-g", "daemon off;"]
