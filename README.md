# [Free Stock Market](http://freestockmarket.me/)
[freestockmarket.me](http://freestockmarket.me/)

Created by Filip Stojanovic

## Overview
The Free Stock Market is a virtual stock brokerage that simulates the real stock market. You can practice trading and holding real stocks and cryptocurrencies with their true prices. Accurate prices are updated every hour from the stock exchange so you can see your investments grow in real time. You never have to risk any of your real money on the marketplace, everything is done with virtual currency. So go ahead and invest in your favorite companies and test your predictions to see just how much money you can make!

## Technical Overview
The Free Stock Market web application was developed using Flask and a PostgreSQL database for the backend. It was deployed in a Docker container hosted on a Virtual Machine using Nginx and Gunicorn. Stock prices are updated hourly by using cron to schedule automated jobs that launch Docker containers to pull stock prices using the Alpaca API. The front end is made using CSS, HTML and Bootstrap.
