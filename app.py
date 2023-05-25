from flask import Flask, render_template, request, redirect, url_for, abort, send_from_directory
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageEnhance
import requests
import os
import base64

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024  # 1 MB limit for uploaded files
UPLOAD_FOLDER = './uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
RECAPTCHA_SITE_KEY = '6LdlLBAmAAAAADEkPEp1BIl_lbDYwzeE_n6lkhBt'

@app.route('/mywork', methods=['POST'])
def transform():
    file = request.files.get('file')
    contrast = float(request.form.get('contrast'))

    if not file:
        abort(400, 'No file was uploaded')
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        abort(400, 'File is not an image')

    recaptcha_response = request.form.get('g-recaptcha-response')
    if not recaptcha_response:
        abort(400, 'reCAPTCHA verification failed')
    payload = {
        'secret': '6LdlLBAmAAAAABbqK-N4kGXshV9m_96TNR9Ka6ER',
        'response': recaptcha_response
    }
    response = requests.post('https://www.google.com/recaptcha/api/siteverify', payload).json()
    if not response['success']:
        abort(400, 'reCAPTCHA verification failed')

    img = Image.open(file)
    enhancer = ImageEnhance.Contrast(img)
    contrast_img = enhancer.enhance(contrast)

    orig_colors = get_color_distribution(img)
    contrast_colors = get_color_distribution(contrast_img)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    fig.suptitle('Color Distribution')

    ax1.plot(np.arange(len(orig_colors)), [c[0] / 255 for c in orig_colors], color='blue')  # set a single color
    ax1.set_xticks(np.arange(len(orig_colors)))
    ax1.set_xticklabels([c[1] for c in orig_colors], rotation=45)
    ax1.set_title('Original Image')

    ax2.plot(np.arange(len(contrast_colors)), [c[0] / 255 for c in contrast_colors], color='red')  # set a single color
    ax2.set_xticks(np.arange(len(contrast_colors)))
    ax2.set_xticklabels([c[1] for c in contrast_colors], rotation=45)
    ax2.set_title('Contrast Image')

    plt.tight_layout()
    plot_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'plot.png')
    plt.savefig(plot_filename)
    contrast_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'contrast.png')
    contrast_img.save(contrast_filename)
    orig_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'orig.png')
    img.save(orig_filename)

    result_filename = os.path.basename(plot_filename)
    with open(plot_filename, 'rb') as f:
        plot_bytes = f.read()

    plot_base64 = base64.b64encode(plot_bytes).decode('utf-8')

    return render_template('result.html', orig=orig_filename, plot=plot_base64, result_filename=result_filename, width=img.width, height=img.height)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', sitekey=RECAPTCHA_SITE_KEY)

def get_color_distribution(img):
    colors = img.getcolors(img.size[0] * img.size[1])
    return sorted(colors, key=lambda x: x[0], reverse=True)[:10]

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.config['UPLOAD_FOLDER'] = 'uploads'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
