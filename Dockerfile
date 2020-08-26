FROM python

RUN pip3 install --upgrade pip
RUN pip3 install requests

#overwrite during build or pass in at runtime
ENV REFRESH_TOKEN='YOUR_TOKEN_HERE'
ENV CLIENT_ID='YOUR_CLIENT_ID_HERE'

COPY trade/ /app/

WORKDIR /app/

ENTRYPOINT python3 token_refresh.py
