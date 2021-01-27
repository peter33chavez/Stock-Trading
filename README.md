# Stock-Trading
Stocks website that gives you the capability to create an account and Buy/Sell/Lookup stocks at current price. 


I've implemented a database with hash functionality for safely storing passwords and username. Apon Creating accounts, I use SQLite to store
my hashed passwords and usernames within my database running error checks before hand to confirm the username hasn’t been taken.

I'm also using Flask to dynamically generate logic for my Dashboard, Lookup, Buy, Sell, and History pages. 

On the Dashboard you will be able to view all the Stocks the current logged in user owns, the current price of that stock, your current cash amount, 
and total Cash Value. 

On the Lookup tab I use the IEX Cloud API to give accurate price quotes of a given stock. the form does have error handling for stocks
that do not exsist or if Null is given in the search bar.

On the Buy/Sell tabs the functionality is to buy or sell a given stock. I use SQLite to cross reference my database checking my users database 
as well as the API to insure the user has enough money to buy the requested stock(s) as well as has exsisting stocks to sell. 
If the user was successful on buying/selling the stock that data is reflected in a second database called transations for use on the 
Dashboard and the History tab.

Lastly on the History tab is simply the history of every transaction for the current logged-in user, from buying stocks to when they sold stocks.



To run website with the API create an account with IEX 
@ iexcloud.io/cloud-login#/register/.

then use export "API_KEY=value"
where value is your API token from IEX
