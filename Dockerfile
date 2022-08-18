FROM python:3.7.13
SHELL ["/bin/bash", "-c"]
RUN mkdir web_test
COPY .. ./web_test
ENV PYTHONPATH=/web_test
# install google chrome (version 104 is needed, otherwise there could be issues between chrome version and chromedriver
# version
RUN apt update -y && wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb  \
    && dpkg -i google-chrome-stable_current_amd64.deb || true

# install missing dependencies and install chrome again
RUN apt-get install -f -y && dpkg -i google-chrome-stable_current_amd64.deb

# install chromedriver version 104
RUN wget https://chromedriver.storage.googleapis.com/104.0.5112.79/chromedriver_linux64.zip \
    && unzip /chromedriver_linux64.zip

# activate venv
RUN if [ -d /web_test/venv ]; then rm -Rf /web_test/venv; fi
RUN cd /web_test && python -m venv venv
ENV PATH=/web_test/venv/bin:$PATH
RUN pip install -r /web_test/requirements.txt
RUN cd /

# install pgsql
RUN apt install postgresql postgresql-contrib -y

EXPOSE 8080

# start pgsql, run scraping and rendering with output reachable on 127.0.0.1:8080
CMD /web_test/src/runner.sh