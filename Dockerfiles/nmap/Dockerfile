FROM kathara/base:latest

RUN echo "nameserver 8.8.8.8"

RUN apt update
RUN apt install -y nmap

RUN mkdir /nmap
WORKDIR /nmap

EXPOSE 80

ENTRYPOINT echo "$TARGET_IP" && python3 -m http.server 80
