import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
import pandas as pd
import re
from fractions import Fraction
import random
import sklearn


# Given a word, if fraction exists, convert fraction to decimal
def word_fraction_to_decimal_old(word):        
    if bool(re.match("(?<!\S)[0-9]\$[0-9]/[0-9](?!\S)", word)) == True:
    #if bool(re.match("(?<!\S)[1-9][0-9]*(?:\/[1-9][0-9])*/g(?!\S)", word)) == True:    
        first_half = word.split('$')[0]
        second_half = word.split('$')[1]
        
        first_half_float = float(first_half)
        second_half_float = float(Fraction(second_half))        

        fraction_value = round(first_half_float + second_half_float,2)
        return fraction_value
    # Matches only if pattern is enclosed with whitespace
    elif bool(re.match("(?<!\S)[0-9]/[0-9](?!\S)", word)) == True:
    #elif bool(re.match("(?<!\S)[1-9][0-9]*(?:\/[1-9][0-9])*/g(?!\S)", word)) == True:
        return round(float(Fraction(word)),2)
    else:
        return word

# From NYT code
def word_unclump_fraction(s):
    """
    Replacess $'s with spaces. The reverse of clumpFractions.
    """
    return re.sub(r'\$', " ", s)


def word_fraction_to_decimal(word):    
    word_unclumped = word_unclump_fraction(word)    
    try:       
        return float(word_unclumped)        
    except ValueError:
        try: 
            num, denom = word_unclumped.split('/')
            try:
                leading, num = num.split(' ')
                whole = float(leading)
            except ValueError:
                whole = 0
            frac = float(num) / float(denom)
            return round(whole - frac if whole < 0 else whole + frac,2)
        except:
            return word_unclumped


# No longer needed: Compound words should be separate tokens, but both matched with "NAME"
def word_combine_compounds(sentence, compound_word): 
    # Break out sentence and compound word to lists
    sentence_list = sentence.split(" ")
    compound_word_list = compound_word.split()    

    
    # Find the indexes of the compound words in the sentence  
    sentence_list_index = []
    for word in compound_word_list:        
        # if can't find name of ingredient in "input" row, let it through (bad data)
        try:
            sentence_list_index.append(sentence_list.index(word)) 
        except:
            return sentence_list

    # Calculate low and upper bound index (assumes compound words are contiguous)
    lower_bound = sentence_list_index[0]
    upper_bound = sentence_list_index[-1]+1
    
    # Rewrite 
    merge = [(lower_bound,upper_bound)]
    
    for t in merge[::-1]:
        merged = ' '.join(sentence_list[t[0]:t[1]])  # merging values within a range
        sentence_list[t[0]:t[1]] = [merged]         # slice replacement
        
    return sentence.split(" ")
    #return sentence_list

# From NYT code
def word_singularize(word):
    """
    A poor replacement for the pattern.en singularize function, but ok for now.
    """

    units = {
        "cups": u"cup",
        "tablespoons": u"tablespoon",
        "teaspoons": u"teaspoon",
        "pounds": u"pound",
        "ounces": u"ounce",
        "cloves": u"clove",
        "sprigs": u"sprig",
        "pinches": u"pinch",
        "bunches": u"bunch",
        "slices": u"slice",
        "grams": u"gram",
        "heads": u"head",
        "quarts": u"quart",
        "stalks": u"stalk",
        "pints": u"pint",
        "pieces": u"piece",
        "sticks": u"stick",
        "dashes": u"dash",
        "fillets": u"fillet",
        "cans": u"can",
        "ears": u"ear",
        "packages": u"package",
        "strips": u"strip",
        "bulbs": u"bulb",
        "bottles": u"bottle",
        "lbs":"pound",
        "oz":"ounce",
        "tsp":"teaspoon",   
        "g":"gram"     
    }

    if word in units.keys():
        return units[word]
    else:
        return word



# From NYT code 
def sentence_clump_fractions(sentence):        
    """
    Replaces the whitespace between the integer and fractional part of a quantity
    with a dollar sign, so it's interpreted as a single token. The rest of the
    string is left alone.
        clumpFractions("aaa 1 2/3 bbb")
        # => "aaa 1$2/3 bbb"
    """        
    return re.sub(r'(\d+)\s+(\d)/(\d)', r'\1$\2/\3', sentence)


# For words that follow this pattern: 15g, separates into two words
def word_separate_grams(word):
    if re.match("\d+g", word):        
        g_index = word.index('g')
        number = word[0:g_index]
        unit = word[g_index:]

        return number + ' ' + unit         
    else:
        return word



def sentence_separate_grams(sentence):
    sentence_grams_separated = [word_separate_grams(i) for i in sentence.split(' ')]
    join_to_sentence = ' '.join(sentence_grams_separated)
    re_split_to_list = join_to_sentence.split(' ')
    sentence_grams_separated_final = ' '.join(re_split_to_list)
    return sentence_grams_separated_final


# From NYT code
def sentence_clean_unicode_fractions(sentence):    
    """
    Replace unicode fractions with ascii representation, preceded by a
    space.
    "1\x215e" => "1 7/8"
    """

    fractions = {
        u'\x215b': '1/8',
        u'\x215c': '3/8',
        u'\x215d': '5/8',
        u'\x215e': '7/8',
        u'\x2159': '1/6',
        u'\x215a': '5/6',
        u'\x2155': '1/5',
        u'\x2156': '2/5',
        u'\x2157': '3/5',
        u'\x2158': '4/5',
        u'\xbc': ' 1/4',
        u'\xbe': '3/4',
        u'\x2153': '1/3',
        u'\x2154': '2/3',
        u'\xbd': '1/2',
    }

    for f_unicode, f_ascii in fractions.items():
        sentence = sentence.replace(f_unicode, ' ' + f_ascii)

    return sentence

# Iterates over word_fraction_to_decimal for one sentence
def sentence_fraction_to_decimal(sentence):    
    words = sentence.split(" ")
    
    words_clean = [str(word_fraction_to_decimal(i)) for i in words]    
    
    return " ".join(words_clean)

# Singularizes all words in a sentence if they appear in the list of words in word_singularize
def sentence_singularize(sentence):
    sentence_singularized_list = [word_singularize(i) for i in sentence.split(" ")]
    sentence_singularized_str = " ".join(sentence_singularized_list)
    return sentence_singularized_str


# Standardizes text format of a sentence
def sentence_special_chars(sentence):    
    return sentence.replace("(","") \
        .replace(")","") \
        .replace(","," , ") \
        .replace(".", " . ") \
        .replace(")", " ) ") \
        .replace("(", " ( ") \
        .replace("'", " ' ") \
        .replace("-", " ") \
        .replace("+", " + ") \
        .replace("\t", " ") \
        .lower()

# Converts sentence into list of words 
def sentence_to_list(sentence):
    return sentence.split(" ")


def sentence_clean_input(sentence):    
    cleaned_sentence = sentence_clump_fractions(sentence)     
    cleaned_sentence = sentence_clean_unicode_fractions(cleaned_sentence)
    cleaned_sentence = sentence_special_chars(cleaned_sentence)   
    cleaned_sentence = sentence_separate_grams(cleaned_sentence)         
    cleaned_sentence = sentence_fraction_to_decimal(cleaned_sentence)        
    cleaned_sentence = sentence_singularize(cleaned_sentence) 
    cleaned_sentence = cleaned_sentence.replace('.0','') 
    
    return cleaned_sentence

# Gets in format that CRF model requires: List of list of tuples.
def sentence_format_for_crf(sentence):   
    clean_sentence = sentence_clean_input(sentence)
    clean_sentence_list = sentence_to_list(clean_sentence)
    clean_sentence_list = [i for i in clean_sentence_list if i] # gets rid of empty strings    
    
    overall_list = []
    sentence_tagged_list = []

    for word in clean_sentence_list:    
        word_string = str(word)        
        word_pos_tag = nltk.pos_tag([word_string])            
                
        word_pos_tag_tuple = tuple(word_pos_tag[0])
        label_tuple = tuple(['']) # blank tuple for label

        word_tagged_tuple = word_pos_tag_tuple + label_tuple
        sentence_tagged_list.append(word_tagged_tuple)

    overall_list.append(sentence_tagged_list)

    return overall_list    

# Cleans training dataset, assuming data is formatted as Pandas DataFrame
def df_clean_training_data(df):
    ingredients_labeled_clean_df = df[df['input'].notnull()]
    ingredients_labeled_clean_df = ingredients_labeled_clean_df[ingredients_labeled_clean_df['name'].notnull()]
    

    print("Cleaning Input column...")
    ingredients_labeled_clean_df['clean_input'] = \
        ingredients_labeled_clean_df['input'] \
            .apply(lambda x: sentence_clean_input(str(x))) \
            .apply(lambda x: sentence_to_list(str(x)))
    print("Input column cleaned...")
    
    print("Cleaning name column...")
    ingredients_labeled_clean_df['clean_name'] = \
        ingredients_labeled_clean_df['name'] \
            .apply(lambda x: sentence_clean_input(str(x)))
            #.apply(lambda x: sentence_fraction_to_decimal(str(x)))            

    print("Name column cleaned...")
    
    
    return ingredients_labeled_clean_df
    

# Formats DataFrame for CRF model
# CRF model needs data in form [('word','part-of-speech','label')...]
# List of lists, where one list is a full sentence. Entire corpus is a list of sentences.
# Labels are only added for training/test data; left blank otherwise
def df_format_for_crf(df):    
    sentence_list = df.loc[0]['clean_input']    
    sentence_list = [i for i in sentence_list if i] # gets rid of empty strings

    overall_list = []

    for index, row in df.iterrows():        
        name = row['clean_name']
        qty = str(row['qty']).replace('.0','')
        unit = row['unit']       

        sentence_list = row['clean_input']
        sentence_list = [i for i in sentence_list if i] # gets rid of empty strings

        sentence_tagged_list = []

        for word in sentence_list:    
            word_string = str(word)       
            word_pos_tag = nltk.pos_tag([word_string])            
            if word_string in name:
                label = "NAME"
            elif word_string == qty:
                label = "QTY"
            elif word_string == unit:
                label = "UNIT"
            else:
                label = "OTHER"
            
            word_pos_tag_tuple = tuple(word_pos_tag[0])
            label_tuple = tuple([label])

            word_tagged_tuple = word_pos_tag_tuple + label_tuple
            sentence_tagged_list.append(word_tagged_tuple)

        overall_list.append(sentence_tagged_list)

    return overall_list


