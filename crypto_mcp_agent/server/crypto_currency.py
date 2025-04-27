# import httpx
# from mcp import tool

# # Define the CoinGecko API base URL
# COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"




from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("crypto_currency")
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"


@mcp.tool()
async def get_crypto_market_info(crypto_ids: str, currency: str = "usd") -> str:
    """
    Get market information for one or more cryptocurrencies.
    
    Parameters:
    - crypto_ids: Comma-separated list of cryptocurrency IDs (e.g., 'bitcoin,ethereum')
    - currency: The currency to display values in (default: 'usd')
    
    Returns:
    - Market information including price, market cap, volume, and price changes
    """
    # Validate inputs
    if not crypto_ids or not isinstance(crypto_ids, str):
        return "Error: crypto_ids must be a non-empty string."
    
    # Construct the API URL
    url = f"{COINGECKO_BASE_URL}/coins/markets"
    
    # Set up the query parameters
    params = {
        "vs_currency": currency.lower(),  # Ensure currency is lowercase for API compatibility
        "ids": crypto_ids,               # Comma-separated crypto IDs
        "order": "market_cap_desc",      # Order by market cap
        "page": 1,                       # Page number
        "sparkline": "false"             # Exclude sparkline data
    }
    
    try:
        # Make the API call
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            
            # Parse the response
            data = response.json()
            
            # Check if we got any data
            if not data:
                return f"No data found for cryptocurrencies: '{crypto_ids}'. Please check the IDs and try again."
            
            # Format the results
            result = ""
            for crypto in data:
                name = crypto.get('name', 'Unknown')
                symbol = crypto.get('symbol', '???').upper()
                price = crypto.get('current_price', 'Unknown')
                market_cap = crypto.get('market_cap', 'Unknown')
                volume = crypto.get('total_volume', 'Unknown')
                price_change = crypto.get('price_change_percentage_24h', 'Unknown')
                
                # Format numbers for readability
                price_str = f"{price:.2f}" if isinstance(price, (int, float)) else str(price)
                market_cap_str = f"{market_cap:,.0f}" if isinstance(market_cap, (int, float)) else str(market_cap)
                volume_str = f"{volume:,.0f}" if isinstance(volume, (int, float)) else str(volume)
                price_change_str = f"{price_change:.2f}" if isinstance(price_change, (int, float)) else str(price_change)
                
                result += f"{name} ({symbol}):\n"
                result += f"Current price: {price_str} {currency.upper()}\n"
                result += f"Market cap: {market_cap_str} {currency.upper()}\n"
                result += f"24h trading volume: {volume_str} {currency.upper()}\n"
                result += f"24h price change: {price_change_str}%\n\n"
            
            return result.strip()  # Remove trailing newline
            
    except httpx.HTTPStatusError as e:
        return f"HTTP error fetching market data: {str(e)}"
    except httpx.RequestError as e:
        return f"Network error fetching market data: {str(e)}"
    except Exception as e:
        return f"Unexpected error fetching market data: {str(e)}"