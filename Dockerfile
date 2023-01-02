FROM python

RUN pip3 install --upgrade pip
RUN pip3 install requests
RUN pip3 install pandas_market_calendars
RUN pip3 install pandas
RUN pip3 install scipy

RUN apt-get update && apt-get -y install cron

#pass in at runtime
ENV REFRESH_TOKEN='YOUR_TOKEN_HERE'
ENV CLIENT_ID='YOUR_CLIENT_ID_HERE'
ENV SEND_EMAIL='kaermorhentreasury@gmail.com'
ENV SEND_EMAIL_PASSWORD='Groider1!'

COPY trade/ /app/

# Copy hello-cron file to the cron.d directory
COPY trade-cron /etc/cron.d/trade-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/trade-cron

# Apply cron job
RUN crontab /etc/cron.d/trade-cron

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
CMD ["./entrypoint.sh"]
