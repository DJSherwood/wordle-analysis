# wordle-analysis

The goal of this project is to model my own and my friends performance playing Wordle. 

Wordle is a free game available at [nytimes.com/games/wordle](https://www.nytimes.com/games/wordle/index.html).
The object of the game is to guess a word within 6 tries.

My current process is to: 
	1. Organize a dataset from a WhatsApp Chat backup ( using my custom module, ProccessWordle.py )
	2. Model the distribution of fails using a BetaBinomial distribution via PYMC ( BetterBinomial.ipynb )
	3. Display results in a Dash Apps ( WordleApp.ipynb )
