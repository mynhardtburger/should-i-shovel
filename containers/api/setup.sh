#!/bin/bash

set -e

echo "Apply custom setup to $POSTGRES_DB..."
chmod 600 /root/.pgpass
chown root: /root/.pgpass

echo "Setting up cron job..."
cat <<EOT >>  /etc/cron.hourly/refresh_weather_data
#!/bin/bash
curl -X 'GET' 'http://127.0.0.1/data_mangement/refresh_weather_data' -H 'accept: application/json'
EOT
chmod +x /etc/cron.hourly/refresh_weather_data
chown root: /etc/cron.hourly/refresh_weather_data
