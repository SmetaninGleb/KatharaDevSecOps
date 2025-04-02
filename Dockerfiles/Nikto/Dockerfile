FROM kathara/base:latest

RUN echo "nameserver 8.8.8.8"

RUN git clone https://github.com/sullo/nikto.git /nikto
RUN apt update
RUN apt install -y perl
RUN apt install -y libnet-ssleay-perl
RUN apt install -y libcrypt-ssleay-perl

WORKDIR /nikto

EXPOSE 80

