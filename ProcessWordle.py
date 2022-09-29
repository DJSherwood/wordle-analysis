## import libraries
import numpy as np
import pandas as pd
import censoring
import re

# define classes
class ScrabblePoints: 
    def __init__(self, wordle_answers_input): 
        self.letter_scores = {"a": 1, "c": 3, "b": 3, "e": 1, "d": 2, "g": 2,
         "f": 4, "i": 1, "h": 4, "k": 5, "j": 8, "m": 3,
         "l": 1, "o": 1, "n": 1, "q": 10, "p": 3, "s": 1,
         "r": 1, "u": 1, "t": 1, "w": 4, "v": 4, "y": 4,
         "x": 8, "z": 10}
        # set path for wordle answers
        self.wordle_answers_input = wordle_answers_input
        # initialize blank pandas dataframe
        self.words_df = pd.DataFrame()
        
    def read_wordle_answers(self):
        self.words_df = pd.read_csv(self.wordle_answers_input)
        return self
        
    def scrabble_word_count(self, row):
        # https://stackoverflow.com/questions/59722407/python-scrabble-word-count
        res = 0
        for letter in row['Answer']:
            res += self.letter_scores[letter]
        return res

    def difficulty(self, row):
        if row['ScrabblePoints'] < 12.0:
            return 'Easy'
        elif row['ScrabblePoints'] > 11.0: 
            return 'Hard'
        else:
            return 'Undefined'    
        
    def add_total_and_difficulty(self):
        self.words_df['ScrabblePoints'] = self.words_df.apply(self.scrabble_word_count, axis=1)
        self.words_df['Difficulty'] = self.words_df.apply(self.difficulty, axis=1)
        self.words_df = self.words_df.astype({'PuzzleNum': 'int64'})
        return self
    
class ParseWordle:
    def __init__(self, raw_whatsapp_input, wordle_output, name_alias): 
        self.raw_whatsapp_input = raw_whatsapp_input
        self.wordle_output = wordle_output
        self.name_alias = name_alias
        self.wordle_match = re.compile(r"(\w+ordle)")
        self.template = 'date, time - name: wordle'
        self.wordle_dict = {}
        
    def create_wordle_df(self): 
        date_list = list()
        time_list = list()
        name_list = list()
        wordle_list = list()
        
        with open(self.raw_whatsapp_input, encoding="utf8") as input_file:
            for line in input_file:
                match = self.wordle_match.search(line)
                
                try:
                    match_tuple = match.groups()
                    try: 
                        s1 = line.split(', ')
                        date_list.append(s1[0])
                    except IndexError:
                        s1 = self.template.split(', ')
                        date_list.append(s1[0])
                    try: 
                        s2 = s1[1].split(' - ')
                        time_list.append(s2[0])
                    except IndexError:
                        s2 = self.template.split(', ')[1].split(' - ')
                        time_list.append(s2[0])
                    try:
                        s3 = s2[1].split(': ')
                        name_list.append(s3[0])
                    except IndexError:
                        s3 = self.template.split(', ')[1].split(' - ')[1].split(': ')
                        name_list.append(s3[0])
                    
                    wordle_list.append(s3[1])         
          
                except AttributeError:
                    pass
                
        # create dictionary
        self.wordle_dict = {'Date': date_list, 
                       'Time': time_list, 
                       'Name': name_list, 
                       'Wordle': wordle_list}
        
        # create data frame
        self.wordle_df = pd.DataFrame(self.wordle_dict)
        return self
    
    def process_data_frame(self):
        # filter out errors
        self.wordle_df = self.wordle_df[self.wordle_df['Wordle'] != 'wordle']
        # split wordle and count the number of words
        self.wordle_df['WordCount'] = self.wordle_df['Wordle'].apply(lambda x: len(str(x).split(' ')))
        self.wordle_df = self.wordle_df[ self.wordle_df['WordCount'] == 3]
        # split the left over words into columns
        self.wordle_df[['Game', 'PuzzleNum', 'Score']] = self.wordle_df['Wordle'].str.split(expand=True)
        # more filtering
        self.wordle_df = self.wordle_df[ self.wordle_df['Game'] == 'Wordle']
        # generate final score
        self.wordle_df['FinalScore'] = self.wordle_df['Score'].apply(lambda x: x[0])
        self.wordle_df = self.wordle_df[ self.wordle_df['FinalScore'] != 'g']
        self.wordle_df = self.wordle_df[ self.wordle_df['FinalScore'] != 'h']
        # convert all X's to 7
        self.wordle_df['FinalScore'] = np.where((self.wordle_df.FinalScore == 'X'),'7',self.wordle_df.FinalScore)
        #create number of fails
        self.wordle_df = self.wordle_df.astype({ 'FinalScore': 'int64'})
        self.wordle_df['Fails'] = self.wordle_df['FinalScore'] - 1
        # now convert all 7s to 6s
        self.wordle_df['FinalScore'] = np.where((self.wordle_df.FinalScore == 7),6,self.wordle_df.FinalScore)
        # merge date and time, convert to date time?
        self.wordle_df['Date_Time'] = pd.to_datetime(self.wordle_df['Date'] + ' ' + self.wordle_df['Time'])
        # censor players
        replace_list = list(self.name_alias.items())
        for i in range(8):
            self.wordle_df = self.wordle_df.replace(replace_list[i][0], replace_list[i][1])
        # create final df
        self.wordle_df = self.wordle_df[['Date_Time', 'Name', 'Game', 'PuzzleNum', 'FinalScore','Fails']]
        # change types
        self.wordle_df = self.wordle_df.astype({ 'Date_Time': 'datetime64', 'PuzzleNum': 'int64'})
        return self
    
    def join_data_frames(self, words_df):
        self.final_df = self.wordle_df.merge(
            words_df[['PuzzleNum','Answer','ScrabblePoints','Difficulty']],
            on=['PuzzleNum'], how='left'
        )
        return self
    
    def write_final_df(self):
        # write to csv
        self.final_df.to_csv(self.wordle_output, sep=',', index=False)
        return self