from flask import Flask, render_template, jsonify, request, send_file
import json
import random
import os
import requests
import subprocess
import io
import tempfile

app = Flask(__name__)

def load_words():
    try:
        with open('words.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_words(words):
    with open('words.json', 'w', encoding='utf-8') as f:
        json.dump(words, f, ensure_ascii=False, indent=4)

# 단어 데이터베이스 로드
words = load_words()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/get_word')
def get_word():
    if not words:
        return jsonify({'error': '단어가 없습니다.'}), 404
    word, info = random.choice(list(words.items()))
    return jsonify({
        'word': word,
        'type': info[0],
        'meaning': info[1]
    })

@app.route('/speak/<word>')
def speak_word(word):
    try:
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_filename = temp_file.name

        # espeak으로 음성 생성
        subprocess.run([
            'espeak',
            '-v', 'en',
            '-w', temp_filename,
            word
        ], check=True)

        # 생성된 오디오 파일을 읽어서 응답으로 전송
        with open(temp_filename, 'rb') as f:
            audio_data = io.BytesIO(f.read())
        
        # 임시 파일 삭제
        os.unlink(temp_filename)

        return send_file(
            audio_data,
            mimetype='audio/wav',
            as_attachment=False,
            download_name=f'{word}.wav'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/check_answer', methods=['POST'])
def check_answer():
    data = request.get_json()
    user_answer = data.get('answer', '').lower()
    user_meaning = data.get('meaning', '')
    correct_word = data.get('word', '').lower()
    correct_meaning = data.get('correct_meaning', '')
    
    # 스펠링과 뜻이 모두 맞아야 정답
    is_correct = user_answer == correct_word and any(m.strip() == user_meaning.strip() for m in correct_meaning.split(','))
    
    return jsonify({
        'correct': is_correct,
        'correct_answer': correct_word,
        'correct_meaning': correct_meaning
    })

@app.route('/api/words', methods=['GET'])
def get_words():
    return jsonify(words)

@app.route('/api/words', methods=['POST'])
def add_word():
    data = request.get_json()
    word = data.get('word', '').lower()
    word_type = data.get('type', '')
    meaning = data.get('meaning', '')
    
    if not word or not word_type or not meaning:
        return jsonify({'error': '모든 필드를 입력해주세요.'}), 400
    
    words[word] = [word_type, meaning]
    save_words(words)
    return jsonify({'message': '단어가 추가되었습니다.'})

@app.route('/api/words/<word>', methods=['DELETE'])
def delete_word(word):
    if word.lower() in words:
        del words[word.lower()]
        save_words(words)
        return jsonify({'message': '단어가 삭제되었습니다.'})
    return jsonify({'error': '단어를 찾을 수 없습니다.'}), 404

@app.route('/api/words/<word>', methods=['PUT'])
def update_word(word):
    if word.lower() not in words:
        return jsonify({'error': '단어를 찾을 수 없습니다.'}), 404
    
    data = request.get_json()
    word_type = data.get('type', '')
    meaning = data.get('meaning', '')
    
    if not word_type or not meaning:
        return jsonify({'error': '모든 필드를 입력해주세요.'}), 400
    
    words[word.lower()] = [word_type, meaning]
    save_words(words)
    return jsonify({'message': '단어가 수정되었습니다.'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 