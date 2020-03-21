#/usr/bin/python3
# -*- coding:Utf-8 -*-

# https://github.com/JECSand/yahoofinancials
# https://risk-engineering.org/notebook/stock-market.html


from yahoofinancials import YahooFinancials

yahoo_financials = YahooFinancials('ILD.PA')
print(yahoo_financials.get_summary_data())