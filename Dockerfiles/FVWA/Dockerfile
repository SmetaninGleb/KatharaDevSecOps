FROM kathara/base:latest

RUN echo "nameserver 8.8.8.8"

RUN git clone https://github.com/SidneyJob/FVWA.git /FVWA && \
    sed -i 's/\(.*\)==.*/\1/g' /FVWA/requirements.txt && \
    python3 -m pip install --no-cache-dir --break-system-packages -r /FVWA/requirements.txt

WORKDIR /FVWA

EXPOSE 5001

ENTRYPOINT [ "python3" ]
CMD [ "main.py" ]
