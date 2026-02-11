"""
Metal Price Fetcher
Fetches current precious metal prices from Yahoo Finance with rate limiting protection
"""
import requests
from datetime import datetime
import json
import time

class MetalPriceFetcher:
    def __init__(self):
        # Yahoo Finance symbols for metals
        self.symbols = {
            'gold': 'GC=F',      # Gold Futures
            'silver': 'SI=F'     # Silver Futures
        }
        self.prices = {
            'gold': 2050.00,      # Default fallback prices
            'silver': 23.50
        }
        self.last_updated = None
        
        # Headers to avoid rate limiting
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def fetch_price(self, symbol):
        """Fetch price for a single symbol from Yahoo Finance"""
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                'interval': '1d',
                'range': '1d'
            }
            
            # Reduced timeout to 3 seconds to prevent blocking
            response = requests.get(url, params=params, headers=self.headers, timeout=3)
            
            # If rate limited, return None to use cached price
            if response.status_code == 429:
                print(f"Rate limited for {symbol}, using cached price")
                return None
            
            response.raise_for_status()
            
            data = response.json()
            
            # Extract the current price from the response
            chart_data = data['chart']['result'][0]
            current_price = chart_data['meta']['regularMarketPrice']
            
            return round(current_price, 2)
        
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return None
    
    def fetch_all_prices(self):
        """Fetch all metal prices with delay between requests"""
        print("Fetching metal prices from Yahoo Finance...")
        
        for metal, symbol in self.symbols.items():
            price = self.fetch_price(symbol)
            if price:
                self.prices[metal] = price
                print(f"  {metal.capitalize()}: ${price}")
            else:
                print(f"  {metal.capitalize()}: ${self.prices.get(metal, 0.00)} (cached)")
            
            # Small delay between requests to avoid rate limiting
            time.sleep(0.5)
        
        self.last_updated = datetime.now()
        return self.prices
    
    def get_prices(self):
        """Get current prices (cached)"""
        return {
            'prices': self.prices,
            'last_updated': self.last_updated.strftime('%Y-%m-%d %H:%M:%S') if self.last_updated else None
        }
    
    def get_price(self, metal):
        """Get price for a specific metal"""
        return self.prices.get(metal.lower())

# Global price fetcher instance
price_fetcher = MetalPriceFetcher()
