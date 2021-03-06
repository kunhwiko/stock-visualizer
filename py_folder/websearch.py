import urllib.request, urllib.parse, urllib.error
from bs4 import BeautifulSoup
from alpha_vantage.timeseries import TimeSeries
from matplotlib import pyplot as plt 
from matplotlib import ticker as plticker
import numpy as np 
import json 
import heapq 

class WebSearch():

    def __init__(self, website):
        # website represents the site to scrape
        self.website = website 


    # parse website to search 5 stocks 
    def web_parse(self):       
        symbol = {}

        # retrieve website to parse (approx 1000 different companies)
        for i in range(9):
            offset = 100 * i
            html = urllib.request.urlopen(self.website + "&offset=" + str(offset)).read()
            soup = BeautifulSoup(html, "html.parser")

            # retrieve company symbols and their daily change in stock
            for stock in soup.find_all('tr',attrs = {'class':'simpTblRow'}):
                for sym in stock.find_all('td',attrs = {'aria-label':'Symbol'}):
                    symbol_tmp = sym.text 
                for ch in stock.find_all('td',attrs = {'aria-label':'Change'}):
                    change_tmp = float(ch.text)
                symbol[symbol_tmp] = change_tmp 
        
        return symbol


    # find 5 symbols with the highest changes 
    def map_symbols(self, symbol):
        # sort symbols by highest changes 
        sorted_syms = []
        for sym in symbol.keys():
            heapq.heappush(sorted_syms, (symbol[sym], sym))
            if len(sorted_syms) > 5:
                heapq.heappop(sorted_syms)
        return [sym for ch, sym in sorted_syms][::-1]


    # call the API of a certain stock, and return a JSON file 
    def api_call(self, symbol, apikey):
        ts = TimeSeries(key = apikey)
        data, meta_data = ts.get_intraday(symbol, interval = '1min', outputsize = 'full')
        return data


    # get the open price upon app start time 
    def get_open_price(self, json_data):
        for k,v in json_data.items():
            # extract just the first open price, the other data is irrelevant
            open_price = v['1. open']
            return open_price


    # cleanse the previous JSON data to build the image
    # also retrieve the most recent closing price  
    def cleanse_json(self, json_data):
        new_records = []
        for k,v in json_data.items():
            close_price = v['4. close']
            new_records.append((k, close_price))

        # format will be in [(time1,price1),(time2,price2)]
        return new_records, new_records[0][1]
        

    # builds an image based on the cleansed data to specified path  
    def plot(self, records, path, type):
        x_axis = []
        y_axis = []

        # limit to 1000 data points 
        count = 0
        for i in range(len(records)):
            if count == 1000:
                break
            x_axis.append(records[i][0][5:16])
            y_axis.append(float(records[i][1]))
            count += 1
        
        x_axis.reverse()   # time order from least to most recent 
        y_axis.reverse()   
        color = ['darkred','darkorange','limegreen','royalblue','darkviolet']
        background = ['mistyrose','navajowhite','honeydew','paleturquoise','lavender']

        # plot 
        fig, ax = plt.subplots(figsize=(16,16))
        plt.plot(x_axis, y_axis, color=color[type], linewidth=1.5, linestyle="solid")
        plt.fill_between(x_axis, y_axis, color=background[type])

        # configure x axis 
        ax.set_xlabel('Time', fontsize=35, fontweight="bold")
        plt.xticks(rotation=20)
        loc = plticker.MultipleLocator(base=len(x_axis)//5)
        ax.xaxis.set_major_locator(loc)
        x_ticks = np.append(ax.get_xticks(), len(x_axis)-1)
        ax.set_xticks(x_ticks)
        ax.tick_params(axis="x", labelsize=25)
        plt.xlim(x_axis[0], x_axis[-1])

        # configure y axis 
        ax.set_ylabel('Price ($)', fontsize=35, fontweight="bold")
        ax.tick_params(axis="y", labelsize=25)
        plt.ylim(min(y_axis)-3, max(y_axis)+3)

        plt.grid(True)
        plt.savefig(path)
        plt.close()


    # writes a new json format : {'Stock 1' : {'symbol', 'open', 'close'}}
    def create_json(self, symbols, open_data, closed_data, path):
        json_data = []
        for i in range(len(symbols)):
            records = {}
            records['name'] = symbols[i]
            records['open_price'] = open_data[i]
            records['closed_price'] = closed_data[i]
            json_data.append(records)
        
        with open(path,'w') as output:
            json.dump(json_data, output)

