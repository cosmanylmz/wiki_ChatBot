from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import requests
import nltk
from string import punctuation
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from time import sleep

app = Flask(__name__)

class ChatBot():
    def __init__(self):
        self.end_chat = False
        self.got_topic = False
        self.do_not_respond = True
        self.title = None
        self.text_data = []
        self.sentences = []
        self.para_indices = []
        self.current_sent_idx = None
        self.punctuation_dict = str.maketrans({p: None for p in punctuation})
        self.lemmatizer = nltk.stem.WordNetLemmatizer()
        self.stopwords = nltk.corpus.stopwords.words('english')
        self.chat_history = []  # Eklenen satır
        self.greeting()

    def greeting(self):
        print("Initializing ChatBot ...")
        sleep(2)
        print('Type "bye" or "quit" or "exit" to end chat')
        sleep(2)
        print('\nEnter your topic of interest when prompted. '
              '\nChatBot will access Wikipedia, prepare itself to '
              '\nrespond to your queries on that topic. \n')
        sleep(3)
        print('ChatBot will respond with short info. '
              '\nIf you input "more", it will give you detailed info '
              '\nYou can also jump to next query')
        sleep(3)
        print('-'*50)
        greet = "Hello, Great day! Please give me a topic of your interest. "
        print("ChatBot >>  " + greet)

    def chat(self, user_input):
        if user_input.lower().strip() in ['bye', 'quit', 'exit']:
            self.end_chat = True
            self.chat_history.append(('User', user_input))
            self.chat_history.append(('ChatBot', 'See you soon! Bye!'))
        elif user_input.lower().strip() == 'more':
            self.do_not_respond = True
            if self.current_sent_idx is not None:
                response = self.text_data[self.para_indices[self.current_sent_idx]]
            else:
                response = "Please input your query first!"
            self.chat_history.append(('User', user_input))
            self.chat_history.append(('ChatBot', response))
        elif not self.got_topic:
            self.scrape_wiki(user_input)
            self.chat_history.append(('User', user_input))
            self.chat_history.append(('ChatBot', 'Topic is "Wikipedia: {}". Let\'s chat!'.format(self.title)))
        else:
            self.sentences.append(user_input)
            response = self.respond()
            self.chat_history.append(('User', user_input))
            self.chat_history.append(('ChatBot', response))

    def respond(self):
        vectorizer = TfidfVectorizer(tokenizer=self.preprocess)
        tfidf = vectorizer.fit_transform(self.sentences)
        scores = cosine_similarity(tfidf[-1], tfidf)
        self.current_sent_idx = scores.argsort()[0][-2]
        scores = scores.flatten()
        scores.sort()
        value = scores[-2]
        if value != 0:
            return self.sentences[self.current_sent_idx]
        else:
            return 'I am not sure. Sorry!'
        del self.sentences[-1]

    def scrape_wiki(self, topic):
        topic = topic.lower().strip().capitalize().split(' ')
        topic = '_'.join(topic)
        try:
            link = 'https://en.wikipedia.org/wiki/' + topic
            data = requests.get(link).content
            soup = BeautifulSoup(data, 'html.parser')
            p_data = soup.findAll('p')
            dd_data = soup.findAll('dd')
            p_list = [p for p in p_data]
            dd_list = [dd for dd in dd_data]
            for tag in p_list + dd_list:
                a = []
                for i in tag.contents:
                    if i.name != 'sup' and i.string is not None:
                        stripped = ' '.join(i.string.strip().split())
                        a.append(stripped)
                self.text_data.append(' '.join(a))

            for i, para in enumerate(self.text_data):
                sentences = nltk.sent_tokenize(para)
                self.sentences.extend(sentences)
                index = [i] * len(sentences)
                self.para_indices.extend(index)

            self.title = soup.find('h1').string
            self.got_topic = True
            print('ChatBot >> Topic is "Wikipedia: {}". Let\'s chat!'.format(self.title))
            self.chat_history.append(('ChatBot', 'Topic is "Wikipedia: {}". Let\'s chat!'.format(self.title)))
        except requests.exceptions.RequestException as e:
            error_msg = 'Error: {}. Please input some other topic!'.format(e)
            self.chat_history.append(('ChatBot', error_msg))
        except Exception as e:
            error_msg = 'An unexpected error occurred: {}. Please input some other topic!'.format(e)
            self.chat_history.append(('ChatBot', error_msg))
    def preprocess(self, text):
        text = text.lower().strip().translate(self.punctuation_dict)
        words = nltk.word_tokenize(text)
        words = [w for w in words if w not in self.stopwords]
        return [self.lemmatizer.lemmatize(w) for w in words]

# Flask uygulama yolları
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form['user_input']
    wiki.chat(user_input)
    chat_history = wiki.chat_history
    return render_template('index.html', chat_history=chat_history)

if __name__ == '__main__':
    wiki = ChatBot()
    app.run(debug=True)
