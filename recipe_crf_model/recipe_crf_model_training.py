from itertools import chain
import nltk
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelBinarizer
import sklearn
import pycrfsuite
import recipe_crf_model_data_prep as prep
import random
import pandas as pd
from collections import Counter

# List of list of tuples
# [[("word","pos_tag","label"),...][("word","pos_tag","label"),...]]
# train_sents = list(nltk.corpus.conll2000.iob_sents('train.txt'))
# test_sents = list(nltk.corpus.conll2000.iob_sents('test.txt'))

# Given one word, breaks out into features
# Aware of position in sentence because of the "i" argument
def word_to_features(sent, i):
    word = sent[i][0]
    postag = sent[i][1]
    features = [
        'bias',
        'word.lower=' + word.lower(),
        'word[-3:]=' + word[-3:],
        'word[-2:]=' + word[-2:],
        'word.isupper=%s' % word.isupper(),
        'word.istitle=%s' % word.istitle(),
        'word.isdigit=%s' % word.isdigit(),
        'postag=' + postag,
        'postag[:2]=' + postag[:2],
    ]
    # Beginning of sentence
    if i > 0:
        word1 = sent[i-1][0]
        postag1 = sent[i-1][1]
        features.extend([
            '-1:word.lower=' + word1.lower(),
            '-1:word.istitle=%s' % word1.istitle(),
            '-1:word.isupper=%s' % word1.isupper(),
            '-1:postag=' + postag1,
            '-1:postag[:2]=' + postag1[:2],
        ])
    else:
        features.append('BOS')

    # End of sentence    
    if i < len(sent)-1:
        word1 = sent[i+1][0]
        postag1 = sent[i+1][1]
        features.extend([
            '+1:word.lower=' + word1.lower(),
            '+1:word.istitle=%s' % word1.istitle(),
            '+1:word.isupper=%s' % word1.isupper(),
            '+1:postag=' + postag1,
            '+1:postag[:2]=' + postag1[:2],
        ])
    else:
        features.append('EOS')
                
    return features

# Given one sentence, breaks out into features
def sentence_to_features(sent):
    return [word_to_features(sent, i) for i in range(len(sent))]

def sentence_to_labels(sent):
    return [label for token, postag, label in sent]

def sentence_to_tokens(sent):      
    return [token for token, postag, label in sent]

def bio_classification_report(y_true, y_pred):
    """
    Classification report for a list of BIO-encoded sequences.
    It computes token-level metrics and discards "O" labels.
    
    Note that it requires scikit-learn 0.15+ (or a version from github master)
    to calculate averages properly!
    """
    lb = LabelBinarizer()
    y_true_combined = lb.fit_transform(list(chain.from_iterable(y_true)))
    y_pred_combined = lb.transform(list(chain.from_iterable(y_pred)))
        
    tagset = set(lb.classes_) - {'O'}
    tagset = sorted(tagset, key=lambda tag: tag.split('-', 1)[::-1])
    class_indices = {cls: idx for idx, cls in enumerate(lb.classes_)}
    
    return classification_report(
        y_true_combined,
        y_pred_combined,
        labels = [class_indices[cls] for cls in tagset],
        target_names = tagset,
    )

def train_crf_model(train_file_path, output_model_name):
    print("Creating train_df from CSV file...")
    train_df = pd.read_csv(train_file_path)        
    print("Cleaning training data...")
    cleaned_training_data = prep.df_clean_training_data(train_df)
    print(cleaned_training_data)
    
    
    print("Formatting training data for CRF algorithm...")
    full_recipe_dataset = prep.df_format_for_crf(cleaned_training_data)
    
    print("Preparing test/train datasets and training model...")
    random.shuffle(full_recipe_dataset)
    test_dataset, training_dataset = sklearn.model_selection.train_test_split(full_recipe_dataset, test_size=0.1, train_size=0.9)

    X_train = [sentence_to_features(s) for s in training_dataset]
    y_train = [sentence_to_labels(s) for s in training_dataset]


    X_test = [sentence_to_features(s) for s in test_dataset]
    y_test = [sentence_to_labels(s) for s in test_dataset]

    trainer = pycrfsuite.Trainer(verbose=False)

    for xseq, yseq in zip(X_train, y_train):
        trainer.append(xseq, yseq)

    trainer.set_params({
        'c1': 1.0,   # coefficient for L1 penalty
        'c2': 1e-3,  # coefficient for L2 penalty
        'max_iterations': 50,  # stop earlier

        # include transitions that are possible, but not observed
        'feature.possible_transitions': True
    })

    trainer.params()   
         
    trainer.train(output_model_name)

    print("Model trained...")

# Using model, tags 
def sentence_predict_label(input, model_path):
    tagger = pycrfsuite.Tagger()
    tagger.open(model_path)
   
    #print("Predicted:", ' '.join(tagger.tag(sentence_to_features(input))))
    #return ' '.join(tagger.tag(sentence_to_features(input)))
    return tagger.tag(sentence_to_features(input))
    # print("Correct:  ", ' '.join(sentence_to_labels(example_sent)))

# training_data_file_path = 'C:\\Users\\jkolpak\\Desktop\\General\\Learning\\Recipe Analysis\\NYT-2015-Ingredients-Labeled.csv'
# train_crf_model(training_data_file_path, 'recipetagging-v5.crfsuite')

def crf_classifier_learn(model_path):
    tagger = pycrfsuite.Tagger()
    tagger.open(model_path)
    info = tagger.info()

    def print_transitions(trans_features):
        for (label_from, label_to), weight in trans_features:
            print("%-6s -> %-7s %0.6f" % (label_from, label_to, weight))

    print("Top likely transitions:")
    print_transitions(Counter(info.transitions).most_common())

    print("\nTop unlikely transitions:")
    print_transitions(Counter(info.transitions).most_common()[-15:])
