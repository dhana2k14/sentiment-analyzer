import json
import flask
import re
import spacy
from flask import Flask, request, render_template, jsonify
from nlp_architect.models.absa.inference.inference import SentimentInference
from spacy.cli.download import download as spacy_download
import inference_to_labels 
from spacy.lang.en import English

# Construction via create_pipe
nlp = English()
sentencizer = nlp.create_pipe("sentencizer")
nlp.add_pipe(sentencizer)

app = Flask(__name__)
spacy_download('en')
inference = SentimentInference('generated_aspect_lex_updated_v2.csv', 'generated_opinion_lex_reranked_v2.csv', parse = True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods = ['POST'])
def predict():
    try:
        name = request.json['input_text_name']
        body = request.json['input_text_body']
        if name:
            sentiment_doc = inference.run(body)
            if sentiment_doc != None:
                labels = inference_to_labels.doc2label(sentiment_doc)
                labels['_vendor_name'] = name
                labels = inference_to_labels.labels_enhancer(labels)
                output_sents = ''
                for _id, _sent in enumerate(labels['_sentences']):
                    sentence_num = _id + 1
                    sentence = [v for k, v in _sent.items() if v][0]
                    polarity = [v for k, v in _sent.items() if v][1]
                    output = "Sentence " + str(sentence_num) + ":" + '\n' + sentence + "." + '\n' + "Sentiment " +  ": " + polarity
                    output_sents = re.sub(r'^\n', '', output_sents + '\n' + output + '\n')
                response =  {}
                response['response'] = {'summary_document': str(labels['_doc_polarity']),'summary_sents': output_sents}
                return flask.jsonify(response)
        else:
            res = dict({'message': 'Empty input'})
            return app.response_class(response=json.dumps(res), status=500, mimetype='application/json')

    except Exception as ex:
        res = dict({'message': str(ex)})
        print(res)
        return app.response_class(response=json.dumps(res), status=500, mimetype='application/json')

if __name__ == '__main__':
    app.run(host = 'localhost', debug = True, port = 5006, use_reloader = False)

