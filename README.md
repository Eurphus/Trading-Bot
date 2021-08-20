# Trading-Bot
 A Simple Binance Trading Bot that uses my algorithm. 
 
 Here is how the algorithm works:
 Checks price every x seconds, and determines if the price is higher/lower then it was previously. If the price is lower, it sells, but if it is higher, it buys and saves the price. On the next check, if the price is lower, it is sold and the saved price stays the same, but if the price goes higher, the bot holds the money and updates the saved price. With each check, every update in price that is above the saved price triggers a buy, while anything dipping too far below it (configurable, could be anywhere from 0.1 - 5% reasonably) it will automatically sell it.
 
 Example:
 If I buy BTC at 45k, the saved price will be set to 45k. If BTC drops down to 49900, the bot will sell the BTC right away. However, once BTC jumps back to 45k it will rebuy the BTC. If BTC continues rising to 46K without any drops, the saved price will continue increasing and the BTC will not be sold. If the BTC drops again however, the BTC will be sold again and only bought once the price recovers to 46k. 
 
 Here is a graph which describes this process

 ![image](https://user-images.githubusercontent.com/40347186/130169209-10f32be2-1938-4926-b31f-30e8d378640e.png)
 
 Blue Line = BTC live price
 
 Black Line = Saved price
 
 The bot sells your balance right before any small, or major drops while still holding during price rises. This theoretically completely eliminates losing money due to price crashes while still taking full advantage of it. This is basically a trailing stop loss that automatically rebuys. Saved price is never fixed, it can always be changed in case you want to take advantage of any lows while your saved price is still in the previous highs.
 
 # Project Currently On Hold
 Project has been put on hold due to Binance restricting my API access and banning binance in my province. Code will be converted to run on another platform when development resumes.

  There are known issues, such as:
  - Incorrect Fee calculations 
  - Bad tracking of balance and separation from other coins in the same wallet
  - Does not always use 100% of available or allotted balance on the coin due to bad precision
 
