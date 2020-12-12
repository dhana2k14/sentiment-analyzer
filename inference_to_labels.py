import json
import re
import spacy
from spacy.lang.en import English
from nltk import flatten 

# Construction via create_pipe
nlp = English()
sentencizer = nlp.create_pipe("sentencizer")
nlp.add_pipe(sentencizer)

# Custom func
def word_freq(word_list):
    """
    Return Polarity    
    """
    word_freq = [word_list.count(w) for w in word_list]
    return(dict(zip(word_list, word_freq)))

def doc2label(doc):
    """
    Converts ABSA Inference Doc to Sentiment Labels  
    """
    documents = {}
    sentences_list = []
    line_json = json.loads(doc.json())
    text = line_json['_doc_text']
    doc = nlp(text)
    num_sents = len(list(doc.sents))
    sents = line_json['_sentences']
    events = []
    for i in range(len(sents)):
        for e in sents[i]['_events']:
            for ev in e:
                if ev['_type'] == 'OPINION':
                    events.append(ev)
    events = {d['_text']:d for d in events}.values() # get unique events
    tokens = text.split()
    io = [[re.sub(r'(\,)|(\.)|(\')|(\))|(\()|(\!)|(\")', '', token), 'O'] for token in tokens] # remove punctuation from token terms
    index = 0
    for token_id, token in enumerate(tokens):
        for event in events:
            if event['_start'] == index:
                io[token_id][1] = "<{}>".format(event['_polarity'])
        index += len(token) + 1
    io = flatten(io)
    while 'O' in io:
        io.remove('O')
    output = " ".join([l for l in io])
    for id, sent in enumerate(sents):
        sent_polarity = {}
        s = text[sent['_start']:sent['_end'] + 1]
        s_tokens = s.split()
        s_io = [[re.sub(r'(\,)|(\.)|(\')|(\))|(\()|(\!)|(\")', '', tok), 'O'] for tok in s_tokens]
        for tok_id, tok in enumerate(s_tokens):
            for event in events:
                if event['_text'] == re.sub(r'(\,)|(\.)|(\')|(\))|(\()|(\!)|(\")', '', tok):
                    s_io[tok_id][1] = "<{}>".format(event['_polarity'])
        s_io = flatten(s_io)
        while 'O' in s_io:
            s_io.remove('O')
        sentence = " ".join([l for l in s_io])
        polarity = re.findall(r'<NEG>|<POS>', sentence)
        polarity = [re.sub(r'<|>', '', i) for i in polarity]
        if polarity:
            if max(word_freq(polarity), key = word_freq(polarity).get) == 'POS':polarity = 'Positive'
            else:polarity = 'Negative'
        sent_polarity['sentence ' + str(id + 1)] = sentence # sentence dict
        sent_polarity['polarity'] = polarity
        sentences_list.append(sent_polarity)
    sent_pol_list = []
    for sentences in sentences_list:
        sent_pol_list.append([v if k == 'polarity' else None for k, v in sentences.items()])
    sent_pol_count = word_freq(flatten(sent_pol_list))
    del sent_pol_count[None] # remove None Key from dict
    if sent_pol_count:
        # score based on generated sentences
        sent_pol_score = [round((v * 0.6) / len(sents), 3) if k == 'Negative' else round((v * 0.4) / len(sents), 3) for k, v in sent_pol_count.items()]
        max_score_index = sent_pol_score.index(max(sent_pol_score)) # get max index of polarity
        doc_sentiment = list(sent_pol_count)[max_score_index]
        # score based on all sentences
        sent_pol_score_x = [round((v * 0.6) / num_sents, 3) if k == 'Negative' else round((v * 0.4) / num_sents, 3) for k, v in sent_pol_count.items()]
        max_score_index_x = sent_pol_score_x.index(max(sent_pol_score_x)) # get max index of polarity
        doc_sentiment_x = list(sent_pol_count)[max_score_index_x] 
    else:
        doc_sentiment = ''
        doc_sentiment_x = ''
    documents['_news_text'] = text
    documents['_doc_polarity'] = doc_sentiment
    documents['_doc_polarity_x'] = doc_sentiment_x
    documents['_sentences'] = sentences_list
    documents['#sents_actual'] = num_sents
    documents['#sents_model'] = len(sents)
    documents['%_sents'] = round(len(sents) / num_sents, 3)
    return documents

def labels_enhancer(documents):
    name = re.sub(r'(\,)|(\.)|(\))|(\()', '', documents['_vendor_name'])
    keyword = name.lower().split()
    keyword_short = ''.join([word[0] for word in keyword])
    keyword = ' '.join([word for word in keyword])
    keyword_split = keyword.split()
    regex = re.compile(r'\b(?:%s)' %  '|'.join(flatten([keyword_short, keyword_split, keyword])))
    lookup_index = []
    for sent in documents['_sentences']:
        lookup = [1 if re.search(regex, str(v).lower()) else 0 for k, v in sent.items()][0]
        kv_pair = {'_vendor_name':lookup}
        sent.update(kv_pair)
        if lookup == 1:
            sent_pol = [v if k == 'polarity' else None for k, v in sent.items()]
            lookup_index.append(sent_pol)
    
    lookup_index = [item for item in flatten(lookup_index) if item != None]
    if lookup_index:
        if documents['%_sents'] >= 0.3:
            if documents['_doc_polarity'] == lookup_index[-1]:pass
            else:documents['_doc_polarity'] = lookup_index[-1]
        else:
            if documents['_doc_polarity'] == lookup_index[-1]:pass
            else:documents['_doc_polarity'] = 'Neutral'
    else:documents['_doc_polarity'] = 'Neutral'
    
    return documents
